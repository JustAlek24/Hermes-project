import asyncio
import json

from data.database import update_last_seen
from network.connection import connect_to_peer, receive_message, send_message
from protocol.messages import create_heartbeat


async def heartbeat_loop(app, interval=60):

    while True:
        peers = app.get_all_peers(app.db)

        if not peers:
            print("Нет пиров, пропускам цикл")
            await asyncio.sleep(interval)
            continue

        for peer in peers:
            peer_id = peer["peer_id"]
            ip = peer["ip"]
            port = peer["port"]

            try:
                reader, writer = await connect_to_peer(ip, port)
                if reader is None or writer is None:
                    app.update_peer_status(peer_id, "offline")
                    continue

                heartbeat_dict = json.loads(create_heartbeat(app.my_peer_id))
                success = await send_message(writer, heartbeat_dict)

                if not success:
                    app.update_peer_status = "offline"
                    writer.close()
                    continue

                response = await receive_message(reader, timeout=5)
                if response:
                    app.update_peer_status(peer_id, "online")
                    update_last_seen(app.db, peer_id)
                else:
                    app.update_peer_status(peer_id, "offline")

                writer.close()
                await writer.wait_closed()

            except Exception:
                app.update_peer_status(peer_id, "offline")
        await asyncio.sleep(interval)
