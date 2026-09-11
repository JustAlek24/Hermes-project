import asyncio
import json
import socket

from data.database import apply_sync
from network import _is_physical_iface, get_local_ips
from network.connection import (
    READER_LIMIT,
    connect_to_peer,
    receive_message,
    send_message,
)
from protocol.messages import create_hello, create_sync_request

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


async def broadcast_discovery(port, my_peer_id, my_port, my_peer_name, interval=5):
    loop = asyncio.get_running_loop()
    try:
        while True:
            message = {
                "type": "DISCOVER",
                "peer_id": my_peer_id,
                "name": my_peer_name,
                "port": my_port,
            }
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


async def send_discover_once(port, my_peer_id, my_port, my_peer_name):
    loop = asyncio.get_running_loop()
    message = {
        "type": "DISCOVER",
        "peer_id": my_peer_id,
        "name": my_peer_name,
        "port": my_port,
    }
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
                    message.get("peer_id"),
                    addr[0],
                    message.get("port"),
                    mtype,
                    message.get("name"),
                )
    finally:
        sock.close()


async def announce_on_discover(discover_message, addr, my_peer_id, my_port, my_peer_name):
    try:
        message = {
            "type": "ANNOUNCE",
            "peer_id": my_peer_id,
            "name": my_peer_name,
            "port": my_port,
        }
        data = json.dumps(message).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        loop = asyncio.get_running_loop()
        await loop.sock_sendto(sock, data, addr)
    finally:
        sock.close()


def make_discovery_callback(app):
    async def _on_peer(peer_id, ip, port, mtype, name=None):
        if not peer_id or peer_id == app.my_peer_id:
            return
        app.on_peer_discovered(peer_id, ip, port, name)
        if mtype == "DISCOVER":
            await announce_on_discover(
                None,
                (ip, app.config.udp_port),
                app.my_peer_id,
                app.config.port,
                app.my_peer_name,
            )

    return _on_peer


def _scan_addresses():
    """Адреса для TCP-скана: все хосты 1..254 в каждой локальной подсети /24
    физического интерфейса, кроме адресов самой машины (у неё может быть
    несколько интерфейсов). Виртуальные подсети (WSL/Hyper-V/TAP) отсекаем —
    там не бывает пиров Hermes, а скан упирается в таймауты."""
    local_ips = [
        ip
        for iface, ip in get_local_ips()
        if _is_physical_iface(iface)
    ]
    self_ips = set(local_ips)
    addresses = []
    seen = set()
    for ip in local_ips:
        parts = ip.split(".")
        if len(parts) != 4:
            continue
        subnet = ".".join(parts[:3])
        for host in range(1, 255):
            candidate = f"{subnet}.{host}"
            if candidate in seen or candidate in self_ips:
                seen.add(candidate)
                continue
            seen.add(candidate)
            addresses.append(candidate)
    return addresses


async def tcp_scan_peers(app, timeout=1.5, concurrency=32):
    """Находит пиров TCP-сканированием локальных подсетей на порт приложения.

    Каждому доступному адресу шлём HELLO со своим peer_id: сосед запоминает
    нас (как при DISCOVER) и отвечает HELLO_RESPONSE со своей идентичностью.
    Это заменяет UDP-broadcast, который упирается во входящий UDP-фильтр
    Windows Firewall (порт 65433 режется), а TCP 65432 открыт — ручное
    добавление пира через него проверено и работает."""
    port = app.config.port
    hello = create_hello(app.my_peer_id, app.my_peer_name, port)
    addresses = _scan_addresses()
    semaphore = asyncio.Semaphore(concurrency)

    async def probe(address):
        async with semaphore:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(address, port, limit=READER_LIMIT),
                    timeout=timeout,
                )
            except (asyncio.TimeoutError, OSError):
                return
            try:
                if not await send_message(writer, hello):
                    return
                raw = await receive_message(reader, timeout=timeout)
                if not raw:
                    return
                reply = json.loads(raw)
                if reply.get("type") != "HELLO_RESPONSE":
                    return
                data = reply.get("data", {})
                app.on_peer_discovered(
                    reply.get("peer_id"),
                    address,
                    data.get("port") or port,
                    data.get("peer_name"),
                )
            except (ValueError, TypeError):
                return
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except (ConnectionResetError, OSError):
                    pass

    await asyncio.gather(*(probe(address) for address in addresses))
