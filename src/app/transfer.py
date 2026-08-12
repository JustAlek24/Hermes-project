import base64
import os
from hashlib import sha256

from network import connection as connect
from protocol import handler, messages


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


async def send_file(connection, filepath, recipient_id, app, progress_callback=None):
    chunks, file_sha = chunk_file(filepath)
    my_peer_id = app.my_peer_id
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    chunks_count = len(chunks)
    meta = messages.create_meta(my_peer_id, filename, file_size, chunks_count, file_sha)
    await connect.send_message(connection[1], meta)
    handler.register_pending("META", recipient_id)
    ok, status = await handler.wait_for_ack("META", recipient_id, timeout=10)
    if not ok:
        return (False, "Отказано" if status == "REJECT" else "Адресат не отвечает")
    for i in range(chunks_count):
        chunk_msg = messages.create_file_chunk(
            my_peer_id, i, base64.b64encode(chunks[i]).decode()
        )
        await connect.send_message(connection[1], chunk_msg)
        handler.register_pending("FILE_CHUNK", recipient_id, chunk_id=i)
        ok, _ = await handler.wait_for_ack("FILE_CHUNK", recipient_id, chunk_id=i, timeout=10)
        if not ok:
            return (False, f"Чанк #{i} не доставлен")
        if progress_callback:
            progress_callback((i + 1) / chunks_count * 100)
    handler.register_pending("DONE", recipient_id)
    ok, _ = await handler.wait_for_ack("DONE", recipient_id)
    if not ok:
        return (False, "Файл не подтверждён")
    return (True, None)