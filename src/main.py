import asyncio
import os
import sys
import threading

_pyside6_dir = os.path.join(
    os.path.dirname(__file__), "..", ".venv", "Lib", "site-packages", "PySide6"
)
_pyside6_dir = os.path.normpath(_pyside6_dir)
if sys.platform == "win32" and os.path.isdir(_pyside6_dir):
    os.add_dll_directory(_pyside6_dir)

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.bridge import AppBridge
from app.core import Config, HermesApp
from data import database as db
from network import connection, heartbeat, search


def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_network(app, loop):
    """Запускает весь сетевой контур поверх asyncio-цикла."""
    port = app.config.port
    udp_port = app.config.udp_port
    bootstrap_ip = app.config.bootstrap_ip
    bootstrap_port = app.config.bootstrap_port

    loop.call_soon_threadsafe(
        lambda: loop.create_task(connection.start_tcp_server(port, app))
    )
    loop.call_soon_threadsafe(
        lambda: loop.create_task(heartbeat.heartbeat_loop(app))
    )
    loop.call_soon_threadsafe(
        lambda: loop.create_task(search.broadcast_discovery(udp_port, app.my_peer_id, port))
    )
    loop.call_soon_threadsafe(
        lambda: loop.create_task(
            search.listen_broadcast(udp_port, search.make_discovery_callback(app))
        )
    )

    if bootstrap_ip and bootstrap_port:
        loop.call_soon_threadsafe(
            lambda: loop.create_task(
                search.connect_to_bootstrap(
                    bootstrap_ip, bootstrap_port, app.my_peer_id, app.db
                )
            )
        )


# Флаг демо-данных для отладки GUI. Поставить False для релиза.
DEMO_DATA = True


def seed_demo_peers(conn):
    """Заполняет БД фейковыми пирами, чтобы их было видно в PeersPage/SendFilePage."""
    demo_peers = [
        {"name": "демо-Алексей", "ip": "192.168.1.50", "port": 65432},
        {"name": "демо-Мария", "ip": "192.168.1.65", "port": 65432},
        {"name": "демо-Сергей", "ip": "192.168.1.77", "port": 65432},
    ]
    for p in demo_peers:
        db.add_peer(conn, "demo-" + p["name"], p["name"], p["ip"], p["port"])


def show_demo_notification(hermes, bridge):
    """Симулирует новую входящую передачу, что триггерит уведомление."""
    meta = {
        "filename": "demo_фото_отпуска.jpg",
        "file_size": 2500000,
        "chunks_count": 3,
        "sha256": "a" * 64,
    }
    hermes.add_incoming_transfer(meta, "demo-демо-Мария")


def main():
    conn = db.init_db()
    asyncio_loop = asyncio.new_event_loop()
    thread = threading.Thread(
        target=start_async_loop, args=(asyncio_loop,), daemon=True
    )
    thread.start()
    """Запуск UI"""
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(_root)
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app = QApplication(sys.argv)

    engine = QQmlApplicationEngine()
    engine.addImportPath(os.path.dirname(os.path.abspath(__file__)))

    config = Config()
    hermes = HermesApp(conn, loop=asyncio_loop, config=config)
    bridge = AppBridge(hermes, loop=asyncio_loop)
    hermes._on_transfer_changed = bridge.transfersChanged.emit
    hermes._on_chunk_ack = lambda pid, cid: asyncio.run_coroutine_threadsafe(
        bridge._send_chunk_ack_async(pid, cid), asyncio_loop
    )
    hermes._on_sync_response = bridge.send_sync_response
    hermes._on_new_incoming = lambda record: bridge.incomingTransfer.emit(
        record["transfer_id"]
    )
    hermes._on_peers_changed = bridge.peersChanged.emit
    engine.rootContext().setContextProperty("app", bridge)

    start_network(hermes, asyncio_loop)

    if DEMO_DATA:
        seed_demo_peers(conn)
        QTimer.singleShot(1500, lambda: show_demo_notification(hermes, bridge))

    ui_dir = os.path.join(os.path.dirname(__file__), "..", "UI")
    engine.addImportPath(ui_dir)

    qml_path = os.path.join(ui_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(os.path.abspath(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
