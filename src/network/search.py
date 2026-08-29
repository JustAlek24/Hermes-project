import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import asyncio
import json
from src.network.connection import connect_to_peer, send_message, receive_message
from src.protocol.messages import create_sync_request
from src.data.database import apply_sync, init_db


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

            if result[0]:
                last_sync = result[0]
            else:
                last_sync = 0

            sync_request_dict = json.loads(create_sync_request(my_peer_id, last_sync))
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
            updated_count = apply_sync(db_conn, peers)

            writer.close()
            await writer.wait_closed()
            return True

        except Exception:
            if attempt == max_retries - 1:
                return False
            await asyncio.sleep(retry_delay)
