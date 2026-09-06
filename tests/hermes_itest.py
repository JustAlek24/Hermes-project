import asyncio
import os
import sqlite3
import sys
import tempfile

SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, SRC)

from app.core import Config, HermesApp
from app import transfer
from data import database as db
from network import connection as connect
from protocol import messages

PORT_A = 65440
PORT_B = 65441


def make_conn(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS storage(
            peer_id TEXT PRIMARY KEY, peer_name TEXT, ip TEXT, port INTEGER,
            last_seen INTEGER, updated_at INTEGER, version INTEGER)"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS identity(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            peer_id TEXT, peer_name TEXT, updated_at INTEGER)"""
    )
    conn.commit()
    return conn


async def main():
    loop = asyncio.get_running_loop()
    tmp = tempfile.mkdtemp(prefix="hermes_itest_")
    conn_a = make_conn(os.path.join(tmp, "a.db"))
    conn_b = make_conn(os.path.join(tmp, "b.db"))

    app_a = HermesApp(conn_a, loop=loop, config=Config(host="127.0.0.1", port=PORT_A))
    app_b = HermesApp(conn_b, loop=loop, config=Config(host="127.0.0.1", port=PORT_B))

    # Аналогично main.py: приёмник подтверждает каждый чанк по входящему сокету.
    async def _chunk_ack(pid, cid):
        writer = app_b._incoming_connections.get(pid)
        if writer is not None:
            await connect.send_message(
                writer,
                messages.create_ack(app_b.my_peer_id, "FILE_CHUNK", chunk_id=cid),
            )

    app_b._on_chunk_ack = lambda pid, cid: asyncio.ensure_future(_chunk_ack(pid, cid))

    server_b = loop.create_task(connect.start_tcp_server(PORT_B, app_b))
    await asyncio.sleep(0.2)
    if server_b.done():
        raise RuntimeError(f"server b failed: {server_b.exception()}")

    db.add_peer(conn_a, app_b.my_peer_id, "receiver-b", "127.0.0.1", PORT_B)

    # Файл ~2.5 МБ -> 3 чанка
    src_file = os.path.join(tmp, "payload.bin")
    payload = os.urandom(2 * 1024 * 1024 + 500 * 1024)
    with open(src_file, "wb") as f:
        f.write(payload)

    out_dir = os.path.join(tmp, "out")
    os.makedirs(out_dir, exist_ok=True)

    send_progress = []
    recv_progress = []

    def send_cb(pct):
        send_progress.append(pct)

    def recv_cb(pct):
        recv_progress.append(pct)

    async def sender_flow():
        reader, writer = await connect.connect_to_peer("127.0.0.1", PORT_B)
        assert reader is not None and writer is not None, "dial to receiver failed"
        return await transfer.send_file(
            (reader, writer), src_file, app_b.my_peer_id, app_a,
            progress_callback=send_cb,
        )

    async def receiver_ack_and_recv():
        # момент «ACCEPT»: пока пользователь не принял, ждём META, потом шлём
        # ACK(META) и запускаем приём по тому же сокету
        deadline = loop.time() + 10
        while app_a.my_peer_id not in app_b._incoming_connections:
            if loop.time() > deadline:
                raise RuntimeError("META не пришёл на приёмник")
            await asyncio.sleep(0.05)
        writer = app_b._incoming_connections[app_a.my_peer_id]
        await transfer.send_ack(app_b.my_peer_id, writer)
        return await transfer.recive_files(
            app_a.my_peer_id, writer, app_b, out_dir, progress_callback=recv_cb
        )

    sender_task = asyncio.ensure_future(sender_flow())
    recv_task = asyncio.ensure_future(receiver_ack_and_recv())

    ok, reason = await asyncio.wait_for(sender_task, timeout=30)
    recv_result = await asyncio.wait_for(recv_task, timeout=30)

    print("SENDER_RESULT:", ok, reason)
    print("RECEIVER_RESULT:", recv_result)
    print("SEND_PROGRESS:", send_progress)
    print("RECV_PROGRESS:", recv_progress)

    out_file = os.path.join(out_dir, "payload.bin")
    assert os.path.exists(out_file), "файл не появился в целевой папке"
    with open(out_file, "rb") as f:
        assert f.read() == payload, "содержимое не совпадает"
    print("INTEGRATION_OK")

    server_b.cancel()
    conn_a.close()
    conn_b.close()


if __name__ == "__main__":
    asyncio.run(main())