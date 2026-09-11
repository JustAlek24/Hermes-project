import asyncio
import json
import logging

from data import database as db
from protocol import messages, sec

logger = logging.getLogger(__name__)

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
    try:
        message = json.loads(raw_string)
    except (json.JSONDecodeError, TypeError):
        return {"error": "INVALID_JSON"}

    if not isinstance(message.get("type"), str):
        return {"error": "MISSING_FIELDS"}
    if not isinstance(message.get("peer_id"), str) or not message.get("peer_id"):
        return {"error": "MISSING_FIELDS"}
    if not isinstance(message.get("timestamp"), (int, float)):
        return {"error": "MISSING_FIELDS"}
    if message["type"] not in KNOWN_TYPES:
        return {"error": "UNKNOWN_TYPE"}

    return message


def handle_message(parsed, app, sender_ip=None, writer=None):
    msg_type = parsed.get("type")
    peer_id = parsed.get("peer_id")
    peer_short = str(peer_id)[:8] if peer_id else "None"

    logger.info(f"handle_message: type={msg_type}, peer={peer_short}, writer={'есть' if writer else 'НЕТ'}")

    # Получаем event loop безопасно
    loop = getattr(app, '_loop', None) or asyncio.get_running_loop()

    if msg_type == "HEARTBEAT":
        app.update_peer_status(peer_id, "online")

    elif msg_type == "ACK":
        ack_for = parsed["data"].get("ack_for")
        chunk_id = parsed["data"].get("chunk_id")
        transfer_id = parsed["data"].get("transfer_id")
    
        logger.info(f"🚨 ПОЛУЧЕН ACK: ack_for='{ack_for}', peer_id='{peer_id}', chunk_id={chunk_id}, transfer_id={transfer_id}")
    
        try:
            logger.info(f"🚨 Вызываю app.resolve_pending('{ack_for}', '{peer_id}', {chunk_id})")
            app.resolve_pending(ack_for, peer_id, chunk_id)
            logger.info("✅ app.resolve_pending отработал без исключений")
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА в app.resolve_pending: {e}", exc_info=True)

    elif msg_type == "META":
        valid, reason = sec.validate_message(parsed)
        if not valid:
            logger.warning(f"❌ META валидация провалилась: {reason}")
            if writer and not writer.is_closing():
                err = messages.create_message("ERROR", app.my_peer_id, data={"reason": str(reason)})
                asyncio.run_coroutine_threadsafe(_safe_send(writer, err), loop)
            return

        data = parsed.get("data", {})
        sender_port = data.get("port")
        sender_name = data.get("peer_name")

        if sender_ip and sender_port:
            existing = db.get_peer(app.db, peer_id)
            if existing is None:
                db.add_peer(app.db, peer_id, sender_name or peer_id, sender_ip, sender_port)
            else:
                db.update_peer(app.db, peer_id, ip=sender_ip, port=sender_port, peer_name=sender_name)
            db.delete_peer_with_address(app.db, peer_id, sender_ip, sender_port)

        if writer is not None and not writer.is_closing():
            app._incoming_connections[peer_id] = writer
            logger.info(f"✅ Сохранен writer для peer_id={peer_short}")

        app.add_incoming_transfer(parsed.get("data"), peer_id)

        # 🔥 ОТПРАВЛЯЕМ ACK НА META
        ack_msg = messages.create_message(
            "ACK",
            app.my_peer_id,
            data={"ack_for": "META", "transfer_id": data.get("transfer_id")}
        )
        logger.info(f"📤 Отправляю ACK на META для peer_id={peer_short}")
        asyncio.run_coroutine_threadsafe(_safe_send(writer, ack_msg), loop)

    elif msg_type == "FILE_CHUNK":
        valid, reason = sec.validate_message(parsed)
        if not valid:
            logger.warning(f"❌ FILE_CHUNK валидация провалилась: {reason}")
            return

        chunk_id = parsed["data"].get("chunk_id")
        content = parsed["data"].get("content")
        
        logger.info(f"📥 Получен FILE_CHUNK #{chunk_id} от {peer_short}")

        if writer is not None and not writer.is_closing():
            app._incoming_connections[peer_id] = writer

        app.receive_chunk(peer_id, chunk_id, content)

        # 🔥 ОТПРАВЛЯЕМ ACK НА FILE_CHUNK (ЭТОГО НЕ ХВАТАЛО!)
        ack_msg = messages.create_message(
            "ACK",
            app.my_peer_id,
            data={"ack_for": "FILE_CHUNK", "chunk_id": chunk_id}
        )
        logger.info(f"📤 Отправляю ACK на FILE_CHUNK #{chunk_id} для peer_id={peer_short}")
        asyncio.run_coroutine_threadsafe(_safe_send(writer, ack_msg), loop)

    elif msg_type == "REJECT":
        app.reject_pending(peer_id)
        app.update_transfer_status(peer_id, "rejected")

    elif msg_type == "ERROR":
        app.error_pending(peer_id)
        app.update_transfer_status(peer_id, "error")

    elif msg_type == "SYNC_REQUEST":
        peers = db.get_all_peers(app.db)
        resp = messages.create_sync_response(app.my_peer_id, peers)
        asyncio.run_coroutine_threadsafe(app.send_sync_response(peer_id, resp), loop)

    elif msg_type == "SYNC_RESPONSE":
        peers = parsed.get("data", {}).get("peers", [])
        db.apply_sync(app.db, peers)


async def _safe_send(writer, message):
    """Безопасная обертка для отправки сообщения."""
    from network.connection import send_message
    return await send_message(writer, message)