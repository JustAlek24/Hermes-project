import asyncio 
import json
import logging 
from src.protocol import handle_message

_connections = {}
_connection_lock = asyncio.Lock()
logger = logging.getLogger(__name__)

async def start_tcp_server(port, app):

    host = app.config.host
    async def handler(reader, writer):
            addr = writer.get_extra_info("peername")
            print(f"Подключился клиент: {addr}")
    
            try:
                while True:
                    raw_message = await receive_message(reader, timeout=10)
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
                        handle_message(parsed_message, app)
                    except Exception:
                        logger.exception("Ошибка при обработке сообщения")
            finally:
                writer.close()
                await writer.wait_closed()
    server = await asyncio.start_server(handler, host, port)
    async with server:
        await server.serve_forever()
    

async def connect_to_peer(ip, port):
    key = (ip, port)

    async with _connection_lock:
        if key in _connections:
            reader, writer = _connections[key]
            if not writer.is_closing():
                return reader, writer
            del _connections[key]
        try:
            reader, writer = await asyncio.open_connection(ip, port)
        except (ConnectionRefusedError, OSError):
            return None
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
    except (ConnectionResetError,BrokenPipeError, OSError):
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

    if not data:
        return None
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text.rstrip("\r\n")