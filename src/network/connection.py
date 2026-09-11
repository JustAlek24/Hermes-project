import sys
import os
import asyncio 
import logging
import json

# Добавляем папку 'src' в пути поиска Python, чтобы он увидел 'protocol'
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Теперь ваш импорт сработает:
from protocol import messages as messages_mod
from protocol.handler import handle_message

_connections = {}
_connection_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

# Дефолтный лимит asyncio.StreamReader — 64 КБ. Строка FILE_CHUNK с чанком 1 МБ
# в base64 занимает ~1.4 МБ и упиралась в лимит: readline() падал с
# LimitOverrunError, обработчик соединения умирал, передача застревала на 0%.
READER_LIMIT = 32 * 1024 * 1024


async def start_tcp_server(port, app):
    host = app.config.host
    logger.info(f"Запуск TCP сервера на {host}:{port} с лимитом {READER_LIMIT} байт")

    async def handler(reader, writer):
        addr = writer.get_extra_info("peername")
        sender_ip = addr[0] if addr else "unknown"
        peer_id = None
        logger.info(f"Подключился клиент: {addr}")

        try:
            while True:
                # Без таймаута: соединение должно жить, пока пир не закроет его сам.
                raw_message = await receive_message(reader, timeout=None)
                if raw_message is None:
                    logger.info(f"Соединение закрыто или пустые данные от {sender_ip}")
                    break
                
                logger.debug(f"ПОЛУЧЕНО СЫРОЕ СООБЩЕНИЕ длиной: {len(raw_message)} байт от {sender_ip}")

                try:
                    parsed_message = app.parse_message(raw_message)
                except Exception as e:
                    logger.error(f"КРИТИЧЕСКИЙ СБОЙ ПАРСИНГА от {sender_ip}: {e}", exc_info=True)
                    continue  # Пропускаем битое сообщение, но держим соединение

                if not isinstance(parsed_message, dict) or parsed_message.get("error"):
                    logger.warning(f"Сообщение содержит ошибку или не является dict: {parsed_message}")
                    continue

                msg_type = parsed_message.get("type")
                
                # БЕЗОПАСНОЕ получение peer_id (избегаем KeyError)
                if msg_type in ("META", "FILE_CHUNK", "HELLO", "HANDSHAKE"):
                    peer_id = parsed_message.get("peer_id")
                    logger.info(f"!!! ЗАРЕГИСТРИРОВАН PEER_ID: {peer_id} для сокета от {sender_ip}")

                logger.info(
                    "RECV type=%s peer=%s from=%s size=%d",
                    msg_type,
                    str(peer_id)[:8] if peer_id else "None",
                    sender_ip,
                    len(raw_message),
                )

                logger.info(">>> ВХОД В handle_message...")
                try:
                    # ВАЖНО: если handle_message синхронная и делает тяжелую I/O (запись на диск), 
                    # это блокирует event loop! Убедитесь, что там используется aiofiles или asyncio.to_thread
                    handle_message(parsed_message, app, sender_ip=sender_ip, writer=writer)
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения в handle_message: {e}", exc_info=True)
                    # Не делаем break, чтобы не рвать соединение из-за одной ошибки чанка

                if msg_type == "HEARTBEAT":
                    try:
                        reply = messages_mod.create_message("HEARTBEAT", app.my_peer_id)
                        await send_message(writer, reply)
                    except Exception as e:
                        logger.exception("Ошибка при отправке ответа на heartbeat")
                        
        finally:
            logger.info(f"Завершение обработчика соединения для {sender_ip} (peer_id: {peer_id})")
            if peer_id and app._incoming_connections.get(peer_id) is writer:
                app._incoming_connections.pop(peer_id, None)
                logger.info(f"Удален peer_id {peer_id} из _incoming_connections")
            
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionResetError, OSError):
                pass

    server = await asyncio.start_server(handler, host, port, limit=READER_LIMIT)
    async with server:
        await server.serve_forever()


async def connect_to_peer(ip, port, force=False):
    key = (ip, port)

    async with _connection_lock:
        if not force and key in _connections:
            reader, writer = _connections[key]
            transport = getattr(writer, "transport", None)
            transport_closing = transport is not None and transport.is_closing()
            if not writer.is_closing() and not transport_closing:
                logger.debug(f"Переиспользуем существующее соединение с {ip}:{port}")
                return reader, writer
            logger.warning(f"Соединение с {ip}:{port} закрыто, удаляем из кэша")
            del _connections[key]
        
        try:
            logger.info(f"Попытка подключения к {ip}:{port}...")
            reader, writer = await asyncio.open_connection(ip, port, limit=READER_LIMIT)
            logger.info(f"Успешно подключено к {ip}:{port}")
        except (ConnectionRefusedError, OSError) as e:
            logger.error(f"Не удалось подключиться к {ip}:{port}: {e}")
            return None, None
        
        _connections[key] = (reader, writer)
        return reader, writer


async def read_outgoing_stream(reader, app, writer=None):
    """Читает ответы пира на исходящем подключении (ACK/REJECT/ERROR/DONE)."""
    try:
        while True:
            raw_message = await receive_message(reader, timeout=None)
            if raw_message is None:
                logger.info("Исходящий поток закрыт (raw_message is None)")
                break
            
            logger.debug(f"ПОЛУЧЕН ОТВЕТ длиной: {len(raw_message)} байт")
            
            try:
                parsed_message = app.parse_message(raw_message)
            except Exception as e:
                logger.error(f"Ошибка при парсинге ответа: {e}", exc_info=True)
                continue
            
            if not isinstance(parsed_message, dict) or parsed_message.get("error"):
                continue
            
            logger.info(
                "RECV_REPLY type=%s peer=%s size=%d",
                parsed_message.get("type"),
                str(parsed_message.get("peer_id"))[:8] if parsed_message.get("peer_id") else "None",
                len(raw_message),
            )
            
            try:
                handle_message(parsed_message, app, writer=writer)
            except Exception as e:
                logger.error(f"Ошибка при обработке ответа: {e}", exc_info=True)
                
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.warning(f"Исходящий поток разорван: {e}")


async def send_message(writer, message_json):
    try:
        if writer.is_closing():
            logger.warning("Попытка отправки в закрывающийся сокет")
            return False
        
        logger.debug("SEND type=%s peer=%s", message_json.get("type"), str(message_json.get("peer_id"))[:8] if message_json.get("peer_id") else "None")
        json_line = json.dumps(message_json, ensure_ascii=False)
        data = (json_line + "\n").encode("utf-8")

        writer.write(data)
        logger.debug("Вызов await writer.drain()...")
        await writer.drain()  # <-- Если передача застряла на 0%, зависание чаще всего происходит ЗДЕСЬ
        logger.debug("SEND drain completed успешно")
        return True
        
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        logger.warning(f"Ошибка сети при отправке: {e}")
        return False
    except Exception as e:
        logger.exception("Не удалось отправить сообщение")
        return False


async def receive_message(reader, timeout=10):
    try:
        data = await asyncio.wait_for(reader.readline(), timeout)
        if not data:
            return None
    except asyncio.TimeoutError:
        return None
    except (ConnectionResetError, OSError) as e:
        logger.debug(f"Сетевая ошибка при чтении: {e}")
        return None
    except (ValueError, asyncio.LimitOverrunError) as e:
        logger.error(f"Превышен лимит чтения или ошибка значения: {e}")
        return None

    if not data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        logger.error(f"Ошибка декодирования UTF-8: {e}")
        return None
    
    return text.rstrip("\r\n")