import json
import time


def create_message(msg_type, peer_id, data=None):

    timestamp = int(time.time())

    if data is None:
        data = {}

    json_string = {
        "type": msg_type,  # Тип json сообщения
        "peer_id": peer_id,  # ID пира отправителя
        "timestamp": timestamp,  # Время создания json сообщения
        "data": data,  # Данные
    }

    return json.dumps(
        json_string, ensure_ascii=False
    )  # Возвращаем json для передачи по сети


def create_heartbeat(peer_id):
    return create_message("HEARTBEAT", peer_id)


def create_meta(peer_id, filename, file_size, chunks_count, sha256):
    data = {
        "filename": filename,
        "file_size": file_size,
        "chunks_count": chunks_count,
        "sha256": sha256,
    }
    return create_message("META", peer_id, data)


def create_file_chunk(peer_id, chunk_id, content):
    data = {"chunk_id": chunk_id, "content": content}
    return create_message("FILE_CHUNK", peer_id, data)


def create_ack(peer_id, ack_for, status="ok", chunk_id=None):
    data = {
        "ack_for": ack_for,
        "status": status,
    }
    if chunk_id is not None:
        data["chunk_id"] = chunk_id
    return create_message("ACK", peer_id, data)


def create_reject(peer_id, reason):
    data = {"reason": reason}
    return create_message("REJECT", peer_id, data)


def create_error(peer_id, code, message):
    data = {"code": code, "message": message}
    return create_message("ERROR", peer_id, data)


def create_sync_request(peer_id, last_sync):
    data = {"last_sync": last_sync}
    return create_message("SYNC_REQUEST", peer_id, data)


def create_sync_response(peer_id, peers):
    data = {"peers": peers}
    return create_message("SYNC_RESPONSE", peer_id, data)
