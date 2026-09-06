import asyncio

from data.database import update_last_seen
from network.connection import READER_LIMIT, receive_message, send_message
from protocol.messages import create_heartbeat


async def _ping_peer(app, peer):
    peer_id = peer["peer_id"]
    ip = peer["ip"]
    port = peer["port"]

    try:
        # Собственное соединение, а не общий кэш connect_to_peer: heartbeat
        # закрывает сокет после каждого пинга, а передача файла живёт на том же
        # (ip, port) — закрытие переиспользуемого соединения рвало передачу.
        reader, writer = await asyncio.open_connection(
            ip, port, limit=READER_LIMIT
        )
    except (ConnectionRefusedError, OSError):
        app.update_peer_status(peer_id, "offline")
        return

    try:
        heartbeat_dict = create_heartbeat(app.my_peer_id)
        success = await send_message(writer, heartbeat_dict)

        if not success:
            app.update_peer_status(peer_id, "offline")
            return

        response = await receive_message(reader, timeout=5)
        if response:
            app.update_peer_status(peer_id, "online")
            update_last_seen(app.db, peer_id)
        else:
            app.update_peer_status(peer_id, "offline")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionResetError, OSError):
            pass


async def check_peers_now(app):
    peers = app.get_all_peers(app.db)
    for peer in peers:
        await _ping_peer(app, peer)


async def heartbeat_loop(app, interval=60):

    while True:
        peers = app.get_all_peers(app.db)

        if not peers:
            print("Нет пиров, пропускам цикл")
            await asyncio.sleep(interval)
            continue

        for peer in peers:
            await _ping_peer(app, peer)

        await asyncio.sleep(interval)
