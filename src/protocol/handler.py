import asyncio
import json

from data import database as db
from protocol import messages

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


def handle_message(parsed, app):
    msg_type = parsed.get("type")
    peer_id = parsed.get("peer_id")

    if msg_type == "HEARTBEAT":
        app.update_peer_status(peer_id, "online")

    elif msg_type == "ACK":
        app.resolve_pending(
            parsed["data"].get("ack_for"), peer_id, parsed["data"].get("chunk_id")
        )

    elif msg_type == "META":
        app.add_incoming_transfer(parsed.get("data"), peer_id)

    elif msg_type == "FILE_CHUNK":
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
        asyncio.ensure_future(app.send_sync_response(peer_id, resp))

    elif msg_type == "SYNC_RESPONSE":
        for p in parsed.get("data", {}).get("peers", []):
            db.add_peer(
                app.db,
                p["peer_id"],
                p["peer_name"],
                p["ip"],
                p["port"],
                p.get("version", 0),
            )
