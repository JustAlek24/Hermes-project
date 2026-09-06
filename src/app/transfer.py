import asyncio
import base64
import logging
import os
from hashlib import sha256

from network import connection as connect
from protocol import handler
from protocol import messages

logger = logging.getLogger(__name__)

_receive_buffers = {}  # peer_id → {"chunks": {}, "queue": asyncio.Queue, "meta": dict}


def chunk_file(filepath, chunk_size=1048576):
    chunks = []
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks, calculate_sha256(filepath)


def assemble_file(chunks, output_path, expected_sha256):
    with open(output_path, "wb") as file:
        file.writelines(chunks)
    return calculate_sha256(output_path) == expected_sha256


def calculate_sha256(filepath, chunk_size=1048576):
    h = sha256()
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def init_receive_buffer(peer_id, meta):
    _receive_buffers[peer_id] = {
        "chunks": {},
        "queue": asyncio.Queue(),
        "meta": meta,
    }


def put_chunk(peer_id, chunk_id, content):
    buf = _receive_buffers.get(peer_id)
    if buf:
        buf["queue"].put_nowait((chunk_id, content))


async def _read_replies(reader, app, peer_id):
    """Читает ответы отправитель/получатель — ACK/REJECT/ERROR из исходящего
    сокета и передаёт их в общий контур обработки. Так отправителю не нужен
    обратный TCP-дозвон от получателя: подтверждения возвращаются по тому же
    соединению, которое сам отправитель и открыл."""
    while True:
        raw = await connect.receive_message(reader, timeout=None)
        if raw is None:
            return
        try:
            parsed = app.parse_message(raw)
        except Exception:
            continue
        if not isinstance(parsed, dict) or parsed.get("error"):
            continue
        try:
            handler.handle_message(parsed, app)
        except Exception:
            logger.exception(
                "Ошибка при обработке ответа peer=%s", str(peer_id)[:8]
            )


async def send_file(connection, filepath, recipient_id, app, progress_callback=None):
    reader, writer = connection
    chunks, file_sha = chunk_file(filepath)
    my_peer_id = app.my_peer_id
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    chunks_count = len(chunks)
    logger.info("SEND_START file=%s chunks=%d size=%d recipient=%s", filename, chunks_count, file_size, str(recipient_id)[:8])
    meta = messages.create_meta(
        my_peer_id,
        app.my_peer_name,
        filename,
        file_size,
        chunks_count,
        file_sha,
        app.config.port,
    )
    # Подтверждения приходят обратно по этому же сокету — читаем их параллельно
    # с отправкой, иначе ACK «зависнет» в буфере чтения и wait_for_ack истёк.
    reply_task = asyncio.create_task(_read_replies(reader, app, recipient_id))
    try:
        app.register_pending("META", recipient_id)
        sent = await connect.send_message(writer, meta)
        if not sent:
            return (False, "Соединение потеряно")
        ok, status = await app.wait_for_ack("META", recipient_id, timeout=120)
        if not ok:
            return (False, "Отказано" if status == "REJECT" else "Адресат не отвечает")
        # DONE-подтверждение регистрируем ДО цикла чанков: приёмник шлёт его сразу
        # после сборки файла и может успеть раньше, чем отправитель дойдёт до этого
        # места. Если регистрировать после цикла — подтверждение «улетит впустую»,
        # не найдя ожидающего, и передача зависнет на «Файл не подтверждён».
        done_key = app.register_pending("DONE", recipient_id)
        for i in range(chunks_count):
            chunk_msg = messages.create_file_chunk(
                my_peer_id, i, base64.b64encode(chunks[i]).decode()
            )
            app.register_pending("FILE_CHUNK", recipient_id, chunk_id=i)
            await connect.send_message(writer, chunk_msg)
            ok, _ = await app.wait_for_ack(
                "FILE_CHUNK", recipient_id, chunk_id=i, timeout=10
            )
            if not ok:
                app.pending_acks.pop(done_key, None)
                logger.warning("CHUNK_FAILED chunk=%d recipient=%s", i, str(recipient_id)[:8])
                return (False, f"Чанк #{i} не доставлен")
            if progress_callback:
                progress_callback((i + 1) / chunks_count * 100)
        ok, _ = await app.wait_for_ack("DONE", recipient_id, timeout=60)
        if not ok:
            logger.warning("DONE_NOT_ACKED recipient=%s", str(recipient_id)[:8])
            return (False, "Файл не подтверждён")
        logger.info("SEND_DONE_OK recipient=%s", str(recipient_id)[:8])
        return (True, None)
    finally:
        reply_task.cancel()


async def recive_files(peer_id, writer, app, output_dir, progress_callback=None):
    # Дата приходить либо напрямую (HermesApp), либо через мост (AppBridge у
    # которого реальный контур лежит в .core). В мост нет ни my_peer_id, ни
    # update_transfer_status — без этого DONE-подтверждение не ушло бы и
    # отправка зависла бы на «Файл не подтверждён».
    core = getattr(app, "core", app)
    buf = _receive_buffers.get(peer_id)
    if not buf:
        logger.warning("RECV_BUFFER_MISSING peer=%s", str(peer_id)[:8])
        return (False, "Буфер не инициализирован")

    meta = buf["meta"]
    queue = buf["queue"]
    chunks_count = meta["chunks_count"]
    expected_sha = meta["sha256"]
    filename = meta["filename"]
    logger.info("RECV_START file=%s chunks=%d peer=%s", filename, chunks_count, str(peer_id)[:8])

    chunks = {}
    for i in range(chunks_count):
        chunk_id, content = await queue.get()
        chunks[chunk_id] = base64.b64decode(content)
        if progress_callback:
            progress_callback((i + 1) / chunks_count * 100)

    output_path = os.path.join(output_dir, filename)
    chunk_list = [chunks[i] for i in range(chunks_count)]
    ok = assemble_file(chunk_list, output_path, expected_sha)

    _receive_buffers.pop(peer_id, None)

    if ok:
        await connect.send_message(
            writer, messages.create_ack(core.my_peer_id, "DONE")
        )
        logger.info("RECV_DONE_OK file=%s peer=%s", filename, str(peer_id)[:8])
        core.update_transfer_status(peer_id, "completed")
        return (True, output_path)
    else:
        await connect.send_message(
            writer,
            messages.create_error(
                core.my_peer_id, "CHECKSUM_MISMATCH", "SHA256 не совпадает"
            ),
        )
        logger.warning("RECV_CHECKSUM_MISMATCH file=%s peer=%s", filename, str(peer_id)[:8])
        core.update_transfer_status(peer_id, "error")
        return (False, "SHA256 не совпадает")


async def send_ack(my_peer_id, writer):
    ack = messages.create_ack(my_peer_id, "META")
    await connect.send_message(writer, ack)


async def send_reject(my_peer_id, writer):
    rej = messages.create_reject(my_peer_id)
    await connect.send_message(writer, rej)
