import asyncio
import json

from data import database as db
from protocol import messages, sec

KNOWN_TYPES = {
    "HEARTBEAT",
    "META",
    "FILE_CHUNK",
    "ACK",
    "REJECT",
    "ERROR",
    "SYNC_REQUEST",
    "SYNC_RESPONSE",
}


def parse_message(raw_string):

    check = True

    try:
        message = json.loads(raw_string)

    except (json.JSONDecodeError, TypeError):
        return {"error": "INVALID_JSON"}

    if not isinstance(message.get("type"), str):
        check = False

    if not isinstance(message.get("peer_id"), str) or not message.get("peer_id"):
        check = False

    if not isinstance(message.get("timestamp"), (int, float)):
        check = False

    if check == False:
        return {"error": "MISSING_FIELDS"}

    if message["type"] not in KNOWN_TYPES:
        check = False

    if check == False:
        return {"error": "UNKNOWN_TYPE"}

    return message


def handle_message(parsed, app, sender_ip=None):
    msg_type = parsed.get("type")
    peer_id = parsed.get("peer_id")

    if msg_type == "HEARTBEAT":
        app.update_peer_status(peer_id, "online")

    elif msg_type == "ACK":
        app.resolve_pending(
            parsed["data"].get("ack_for"), peer_id, parsed["data"].get("chunk_id")
        )

    elif msg_type == "META":
        valid, _ = sec.validate_message(parsed)
        if not valid:
            return
        # Регистрируем отправителя по его реальному peer_id, чтобы
        # приём файла (ack/получение) находили его адрес независимо от
        # ручного добавления пира со случайным id.
        data = parsed.get("data", {})
        sender_port = data.get("port")
        sender_name = data.get("peer_name")
        if sender_ip and sender_port:
            existing = db.get_peer(app.db, peer_id)
            if existing is None:
                db.add_peer(
                    app.db,
                    peer_id,
                    sender_name or peer_id,
                    sender_ip,
                    sender_port,
                )
            else:
                db.update_peer(
                    app.db,
                    peer_id,
                    ip=sender_ip,
                    port=sender_port,
                    peer_name=sender_name,
                )
            db.delete_peer_with_address(app.db, peer_id, sender_ip, sender_port)
        app.add_incoming_transfer(parsed.get("data"), peer_id)

    elif msg_type == "FILE_CHUNK":
        valid, _ = sec.validate_message(parsed)
        if not valid:
            return
        chunk_id = parsed["data"].get("chunk_id")
        content = parsed["data"].get("content")
        app.receive_chunk(peer_id, chunk_id, content)

    elif msg_type == "REJECT":
        app.reject_pending(peer_id)
        app.update_transfer_status(peer_id, "rejected")

    elif msg_type == "ERROR":
        app.error_pending(peer_id)
        app.update_transfer_status(peer_id, "error")

    elif msg_type == "SYNC_REQUEST":
        peers = db.get_all_peers(app.db)
        resp = messages.create_sync_response(app.my_peer_id, peers)
        asyncio.run_coroutine_threadsafe(
            app.send_sync_response(peer_id, resp), app._loop
        )

    elif msg_type == "SYNC_RESPONSE":
        peers = parsed.get("data", {}).get("peers", [])
        db.apply_sync(app.db, peers)
