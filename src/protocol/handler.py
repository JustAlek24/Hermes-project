import asyncio
import json

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


class _Pending:
    def __init__(self):
        self.event = asyncio.Event()
        self.rejected = False
        self.error = False


def register_pending(msg_type, peer_id, chunk_id=None):
    key = (peer_id, msg_type, chunk_id)

    pending_acks[key] = _Pending()

    return key


def resolve_pending(msg_type, peer_id, chunk_id=None):
    pending = pending_acks.get((peer_id, msg_type, chunk_id))

    if pending is not None:
        pending.event.set()


def reject_pending(peer_id):
    pending = pending_acks.get((peer_id, "META", None))

    if pending is not None:
        pending.rejected = True
        pending.event.set()


def error_pending(peer_id):
    for (pid, msg_type, chunk_id), pending in pending_acks.items():

        if pid == peer_id:
            pending.error = True
            pending.event.set()


async def wait_for_ack(
    msg_type, peer_id, chunk_id=None, timeout=10, max_retries=3, resend=None
):
    key = (peer_id, msg_type, chunk_id)

    for i in range(max_retries):
        pending = pending_acks.get(key)

        if pending is None:
            return (False, None)

        try:
            await asyncio.wait_for(pending.event.wait(), timeout)
        except asyncio.TimeoutError:
            if resend is not None:
                resend()
            continue
        else:
            pending_acks.pop(key, None)
            if pending.rejected:
                return (False, "REJECT")
            if pending.error:
                return (False, "ERROR")
            return (True, None)

    pending_acks.pop(key, None)
    return (False, None)


def handle_message(parsed, app):
    msg_type = parsed.get("type")
    peer_id = parsed.get("peer_id")

    if msg_type == "HEARTBEAT":
        app.update_peer_status(peer_id, "online")

    elif msg_type == "ACK":
        resolve_pending(
            parsed["data"].get("ack_for"), peer_id, parsed["data"].get("chunk_id")
        )

    elif msg_type == "META":
        # TODO: transfer_queue + Signal-уведомление GUI
        pass

    elif msg_type == "FILE_CHUNK":
        # TODO: запись через transfer layer
        pass

    elif msg_type == "REJECT":
        # TODO: отмена transfer, Signal-уведомление GUI
        reject_pending(peer_id)

    elif msg_type == "ERROR":
        # TODO: Signal-уведомление GUI
        error_pending(peer_id)

    elif msg_type == "SYNC_REQUEST":
        # TODO: get_peers_since из БД + ответ SYNC_RESPONSE
        pass

    elif msg_type == "SYNC_RESPONSE":
        # TODO: apply_sync в БД
        pass
