import asyncio
import base64
import logging
import os
from hashlib import sha256

from network import connection as connect
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


async def send_file(connection, filepath, recipient_id, app, progress_callback=None):
    reader = connection[0]
    logger.info(">>> [TRANSFER] 1. Начинаю чтение файла...")
    chunks, file_sha = chunk_file(filepath)
    my_peer_id = app.my_peer_id
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    chunks_count = len(chunks)
    logger.info(f">>> [TRANSFER] 2. Файл прочитан: {chunks_count} чанков, размер {file_size}")

    meta = messages.create_meta(
        my_peer_id,
        app.my_peer_name,
        filename,
        file_size,
        chunks_count,
        file_sha,
        app.config.port,
    )
    logger.info(">>> [TRANSFER] 3. Сообщение META создано")

    if id(reader) not in app._outbound_readers or app._outbound_readers[id(reader)].done():
        logger.info(">>> [TRANSFER] 4. Запускаю фоновое чтение исходящего потока (read_outgoing_stream)")
        app._outbound_readers[id(reader)] = asyncio.create_task(
            connect.read_outgoing_stream(reader, app, writer=connection[1])
        )

    logger.info(">>> [TRANSFER] 5. Регистрирую ожидание ACK на META")
    app.register_pending("META", recipient_id)

    logger.info(">>> [TRANSFER] 6. Отправляю META в сокет...")
    sent = await connect.send_message(connection[1], meta)
    logger.info(f">>> [TRANSFER] 7. Результат отправки META: sent={sent}")

    if not sent:
        logger.error(">>> [TRANSFER] ОШИБКА: Соединение потеряно при отправке META")
        return (False, "Соединение потеряно")

    logger.info(">>> [TRANSFER] 8. НАЧИНАЮ ОЖИДАНИЕ ACK НА META (таймаут 120с)...")
    ok, status = await app.wait_for_ack("META", recipient_id, timeout=120)
    logger.info(f">>> [TRANSFER] 9. ОЖИДАНИЕ ЗАВЕРШЕНО: ok={ok}, status={status}")

    if not ok:
        logger.error(f">>> [TRANSFER] КРИТИЧЕСКАЯ ОШИБКА: ACK на META не получен или отклонен. status={status}")
        return (False, "Отказано" if status == "REJECT" else "Адресат не отвечает")

    logger.info(">>> [TRANSFER] 10. УСПЕХ! Начинаю цикл отправки чанков...")
    done_key = app.register_pending("DONE", recipient_id)

    for i in range(chunks_count):
        logger.info(f">>> [TRANSFER] 11. Подготовка чанка {i+1}/{chunks_count}")
        chunk_msg = messages.create_file_chunk(
            my_peer_id, i, base64.b64encode(chunks[i]).decode()
        )
        logger.info(f">>> [TRANSFER] 12. Регистрирую ожидание ACK на чанк {i}")
        app.register_pending("FILE_CHUNK", recipient_id, chunk_id=i)

        logger.info(f">>> [TRANSFER] 13. Отправляю FILE_CHUNK {i} в сокет...")
        await connect.send_message(connection[1], chunk_msg)

        logger.info(f">>> [TRANSFER] 14. Жду ACK на чанк {i} (таймаут 10с)...")
        ok, _ = await app.wait_for_ack("FILE_CHUNK", recipient_id, chunk_id=i, timeout=10)
        logger.info(f">>> [TRANSFER] 15. Результат ожидания чанка {i}: ok={ok}")

        if not ok:
            app.pending_acks.pop(done_key, None)
            logger.warning(f">>> [TRANSFER] ОШИБКА: Чанк #{i} не доставлен")
            return (False, f"Чанк #{i} не доставлен")

        if progress_callback:
            progress_callback((i + 1) / chunks_count * 100)

    logger.info(">>> [TRANSFER] 16. Все чанки отправлены, жду финального DONE...")
    ok, _ = await app.wait_for_ack("DONE", recipient_id, timeout=60)
    if not ok:
        logger.warning(">>> [TRANSFER] ОШИБКА: Файл не подтверждён (DONE)")
        return (False, "Файл не подтверждён")

    logger.info(">>> [TRANSFER] 17. ПЕРЕДАЧА УСПЕШНО ЗАВЕРШЕНА!")
    return (True, None)


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
