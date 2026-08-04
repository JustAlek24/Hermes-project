import json
import threading

pending_acks = {}  # Заглушка, потом перенести в app
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


def register_pending(msg_type, peer_id, chunk_id=None):
    key = (peer_id, msg_type, chunk_id)
    thread = threading.Event()

    pending_acks[key] = thread

    return key


def resolve_pending(msg_type, peer_id, chunk_id=None):
    event = pending_acks.get((peer_id, msg_type, chunk_id))

    if event is not None:
        event.set()


def wait_for_ack(
    msg_type, peer_id, chunk_id=None, timeout=10, max_retries=3, resend=None
):
    key = (peer_id, msg_type, chunk_id)

    for i in range(max_retries):
        event = pending_acks.get(key)

        if event is None:
            return False

        if event.wait(timeout):
            pending_acks.pop(key, None)
            return True

        if resend is not None:
            resend()

    pending_acks.pop(key, None)
    return False
