import asyncio
import json
import logging

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

    async def handler(reader, writer):
        addr = writer.get_extra_info("peername")
        sender_ip = addr[0] if addr else "unknown"
        print(f"Подключился клиент: {addr}")

        try:
            while True:
                # Без таймаута: соединение должно жить, пока пир не закроет его
                # сам. Таймаут в 10 сек убивал соединение во время ожидания
                # решения пользователя (приём файла), а также канал подтверждений
                # между передачами — следующая передача уходила в битый сокет.
                raw_message = await receive_message(reader, timeout=None)
                if raw_message is None:
                    break
                try:
                    parsed_message = app.parse_message(raw_message)
                except Exception:
                    logger.exception("Ошибка при парсинге сообщения")
                    continue
                if not isinstance(parsed_message, dict) or parsed_message.get("error"):
                    continue
                try:
                    handle_message(parsed_message, app, sender_ip=sender_ip)
                except Exception:
                    logger.exception("Ошибка при обработке сообщения")
                if parsed_message.get("type") == "HEARTBEAT":
                    try:
                        reply = messages_mod.create_message(
                            "HEARTBEAT", app.my_peer_id
                        )
                        await send_message(writer, reply)
                    except Exception:
                        logger.exception("Ошибка при отправке ответа на heartbeat")
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(handler, host, port, limit=READER_LIMIT)
    async with server:
        await server.serve_forever()


async def connect_to_peer(ip, port, force=False):
    key = (ip, port)

    async with _connection_lock:
        if not force and key in _connections:
            reader, writer = _connections[key]
            # writer.is_closing() может оставаться False после закрытия пиром
            # сокета — проверяем и транспорт, чтобы не переиспользовать битый.
            transport = getattr(writer, "transport", None)
            transport_closing = transport is not None and transport.is_closing()
            if not writer.is_closing() and not transport_closing:
                return reader, writer
            del _connections[key]
        try:
            reader, writer = await asyncio.open_connection(
                ip, port, limit=READER_LIMIT
            )
        except (ConnectionRefusedError, OSError):
            return None, None
        _connections[key] = (reader, writer)
        return reader, writer


async def send_message(writer, message_json):

    try:
        if writer.is_closing():
            return False

        json_line = json.dumps(message_json, ensure_ascii=False)
        data = (json_line + "\n").encode("utf-8")

        writer.write(data)
        await writer.drain()

        return True
    except (ConnectionResetError, BrokenPipeError, OSError):
        return False
    except Exception:
        logger.exception("Не удалось отправить сообщение")
        return False


async def receive_message(reader, timeout=10):
    try:
        data = await asyncio.wait_for(reader.readline(), timeout)
        if not data:
            return None
    except asyncio.TimeoutError:
        return None
    except (ConnectionResetError, OSError):
        return None
    except (ValueError, asyncio.LimitOverrunError):
        # Строка длиннее лимита — соединение в неопределённом состоянии.
        return None

    if not data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text.rstrip("\r\n")
