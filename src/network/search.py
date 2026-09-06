import asyncio
import json
import socket

from data.database import apply_sync
from network import get_local_ips
from network.connection import connect_to_peer, receive_message, send_message
from protocol.messages import create_sync_request

BOOTSTRAP_IP = "127.0.0.1"
BOOTSTRAP_PORT = 64352


async def connect_to_bootstrap(bootstrap_ip, bootstrap_port, my_peer_id, db_conn):
    max_retries = 3
    retry_delay = 30

    for attempt in range(max_retries):
        try:
            reader, writer = await connect_to_peer(bootstrap_ip, bootstrap_port)

            if reader is None or writer is None:
                raise ConnectionError("Не удалось установить соединение")

            cursor = db_conn.cursor()
            cursor.execute("SELECT MAX(updated_at) FROM storage")
            result_of_cursor = cursor.fetchone()

            if result_of_cursor[0]:
                last_sync = result_of_cursor[0]
            else:
                last_sync = 0

            sync_request_dict = create_sync_request(my_peer_id, last_sync)
            success = await send_message(writer, sync_request_dict)

            if not success:
                raise ConnectionError("Не удалось отправить сообщение")

            raw_response = await receive_message(reader, timeout=10)

            if raw_response is None:
                raise TimeoutError("Превышено время ожидания")

            response = json.loads(raw_response)

            if response.get("type") != "SYNC_RESPONSE":
                raise ValueError(
                    f"Ожидался SYNC_RESPONSE, получено: {response.get('type')}"
                )

            peers = response.get("data", {}).get("peers", [])
            apply_sync(db_conn, peers)

            writer.close()
            await writer.wait_closed()
            return True

        except (ConnectionError, TimeoutError, ValueError, OSError):
            if attempt == max_retries - 1:
                return False
            await asyncio.sleep(retry_delay)


def _broadcast_targets(port):
    """Возвращает список (bind_ip, target) для отправки broadcast на каждый
    LAN-интерфейс. Привязка сокета к конкретному интерфейсу гарантирует,
    что broadcast уйдёт в нужную подсеть (проводную и WiFi)."""
    targets = []
    for _iface, ip in get_local_ips():
        targets.append((ip, ("255.255.255.255", port)))
    if not targets:
        targets.append((None, ("255.255.255.255", port)))
    return targets


async def broadcast_discovery(port, my_peer_id, my_port, interval=5):
    loop = asyncio.get_running_loop()
    try:
        while True:
            message = {"type": "DISCOVER", "peer_id": my_peer_id, "port": my_port}
            data = json.dumps(message).encode()
            for bind_ip, addr in _broadcast_targets(port):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setblocking(False)
                try:
                    if bind_ip:
                        sock.bind((bind_ip, 0))
                    await loop.sock_sendto(sock, data, addr)
                finally:
                    sock.close()
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        raise


async def send_discover_once(port, my_peer_id, my_port):
    loop = asyncio.get_running_loop()
    message = {"type": "DISCOVER", "peer_id": my_peer_id, "port": my_port}
    data = json.dumps(message).encode()
    for bind_ip, addr in _broadcast_targets(port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)
        try:
            if bind_ip:
                sock.bind((bind_ip, 0))
            await loop.sock_sendto(sock, data, addr)
        finally:
            sock.close()


async def listen_broadcast(port, on_peer):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    sock.bind(("0.0.0.0", port))
    loop = asyncio.get_running_loop()
    try:
        while True:
            data, addr = await loop.sock_recvfrom(sock, 65535)
            try:
                message = json.loads(data)
            except ValueError:
                continue
            mtype = message.get("type")
            if mtype in {"DISCOVER", "ANNOUNCE"}:
                await on_peer(
                    message.get("peer_id"), addr[0], message.get("port"), mtype
                )
    finally:
        sock.close()


async def announce_on_discover(discover_message, addr, my_peer_id, my_port):
    try:
        message = {"type": "ANNOUNCE", "peer_id": my_peer_id, "port": my_port}
        data = json.dumps(message).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(sock, data, addr)
    finally:
        sock.close()


def make_discovery_callback(app):
    async def _on_peer(peer_id, ip, port, mtype):
        if not peer_id or peer_id == app.my_peer_id:
            return
        app.on_peer_discovered(peer_id, ip, port)
        if mtype == "DISCOVER":
            await announce_on_discover(
                None, (ip, app.config.udp_port), app.my_peer_id, app.config.port
            )

    return _on_peer
