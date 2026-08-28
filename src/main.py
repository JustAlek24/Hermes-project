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

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.bridge import AppBridge
from app.core import HermesApp
from data import database as db

# =============================================================================
# TODO: Что осталось доделать
# =============================================================================
#
# == СДЕЛАНО (не трогать, не в issues) ==
# - Race condition: буфер META создаётся сразу при add_incoming_transfer (core.py),
#   чанки до нажатия "Принять" больше не теряются.
# - SentPage: add_output_transfer реализован (bridge.py), отправки записываются
#   в _transfers с direction "out". Фикс tyзpo transferID -> transferId.
# - ProgressBar: bridge.send_file/_receive_async передают progress_callback,
#   который пишет в _transfer_progress (dict peer_id->percent), BottomPanel
#   читает app.transfer_progress.
# - PeersPage: добавлены app.peers (@Property list, notify=peersChanged) и сигнал
#   peersChanged. Список пиров из db.get_all_peers. Фикс сломанного Connections.
# - SendFilePage: UI с FileDialog + списком пиров, вызывает app.send_file(peer_id, path).
# - AddPeerPage: форма (имя/IP/порт) -> app.add_peer(name, ip, port) -> db.add_peer.
# - AboutPeerPage: инфо из app.peers + кнопка удаления (app.remove_peer).
# - AboutPage/SettingsPage: базовый контент вместо "Скоро тут будет код".
# - sec.validate_message подключён к handler (META/FILE_CHUNK валидируются).
# - SYNC_REQUEST использует app._loop вместо asyncio.get_event_loop().
# - database.py: убран опасный main() с тестовыми данными. __tests__.py почищен.
#
# == Заглушки (awaiting network #24) ==
# find_peers() (bridge.py)        — print. Кнопка "Найти пир в сети Wi-Fi".
#                                   Должна искать через UDP broadcast (#22).
# check_status() (bridge.py)      — print. Кнопка "Проверить статус пиров".
#                                   Должна пинговать пиров + обновлять peerStatus.
# search_peers(query) (bridge.py) — print. Поиск по известным пирам.
# on_user_search_peers() (core.py)— pass. Обработчик поиска.
# on_user_send_file() (core.py)   — pass. Route через core (bridge.send_file сейчас
#                                   вызывает transfer напрямую).
# transfer_queue / tcp_connections — нигде не используются. Для queues при сетевой
#                                   работе.
#
# == Осталось решить ==
# - Мёртвые сигналы: status_changed, ownAddressChanged, peerNamesChanged.
# - peer_status @Property — нет потребителя в QML.
# - update_peer vs apply_sync: SYNC_RESPONSE хардкодит db.add_peer вместо db.apply_sync.
# - progress два потока: dict _transfer_progress не потокобезопасен (оба направления
#   пишут из разных мест). Внутри Qt main thread ок, но при росте - ревью.
#
# == Зависит от network (#24, другие люди) ==
# start_network(loop)         — пустой stub (строка ниже). TCP-сервер не запускается.
# Heartbeat (#25)             — create_heartbeat() есть, but nothing sends it,
#                               nothing marks peers offline. online_count всегда 0.
# UDP Broadcast (#22)         — обнаружение пиров в локальной сети.
# Bootstrap (#23)             — начальная синхронизация списка пиров при запуске.
# last_seen (#16)             — never updated. update_last_seen существует но не вызывается.
# DB sync (#17)               — depends on heartbeat + last_seen.
# connection.py:14            — app.config.host у нас нет. Network пишет host по-своему.
# =============================================================================


def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_network(loop):
    pass


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
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    engine.addImportPath(os.path.dirname(os.path.abspath(__file__)))

    hermes = HermesApp(conn, loop=asyncio_loop)
    bridge = AppBridge(hermes, loop=asyncio_loop)
    hermes._on_transfer_changed = bridge.transfersChanged.emit
    hermes._on_chunk_ack = lambda pid, cid: asyncio.run_coroutine_threadsafe(
        bridge._send_chunk_ack_async(pid, cid), asyncio_loop
    )
    hermes._on_sync_response = bridge.send_sync_response
    engine.rootContext().setContextProperty("app", bridge)

    ui_dir = os.path.join(os.path.dirname(__file__), "..", "UI")
    engine.addImportPath(ui_dir)

    qml_path = os.path.join(ui_dir, "main.qml")
    engine.load(QUrl.fromLocalFile(os.path.abspath(qml_path)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
