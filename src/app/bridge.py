import asyncio
import os
import time
import uuid

from PySide6.QtCore import Property, QObject, Signal, Slot

from app import transfer
from data import database as db
from network import connection as connect
from network import get_local_ip
from protocol import messages

DEFAULT_PORT = 65432  # !!! ПОСЛЕ СОЗДАНИЯ РАБОЧЕЙ БД - УДАЛИТЬ НАХУЙ !!!


class AppBridge(QObject):
    conn = db.init_db()
    ### Сигналы ###
    new_peer = Signal(str)  # peer_id
    status_changed = Signal(str, str)  # peer_id, status
    peerStatusChanged = Signal()

    ownAddressChanged = Signal()
    transfersChanged = Signal()
    peerNamesChanged = Signal()

    # Инициализация класса
    def __init__(self, parent=None):
        super().__init__(parent)
        self._peer_status = {}
        self.my_peer_id = uuid.uuid4().hex
        self._transfers = []

    # Метод, запускающий сигнал о добавлении новго приёма файла
    def add_incoming_transfer(self, meta, peer_id):
        peer = db.get_peer(self.conn, peer_id)
        peer_name = peer["peer_name"] if peer else peer_id
        self._transfers.insert(
            0,
            {
                "transfer_id": uuid.uuid4().hex,
                "direction": "in",
                "peer_id": peer_id,
                "peer_name": peer_name,
                "filename": meta["filename"],
                "file_size": meta["file_size"],
                "sha256": meta["sha256"],
                "chunks_count": meta["chunks_count"],
                "status": "pending",
                "timestamp": int(time.time()),
            },
        )
        self._transfers = list(self._transfers)
        self.transfersChanged.emit()

    def add_output_transfer(self, meta, peer_id):
        pass

    # Метод, запускающий сигнал к QML о новом пире
    def new_peer_connected(self, name):
        self.new_peer.emit(name)

    # Слот для кнопки поиска пиров в WI-FI сети
    @Slot()
    def find_peers(self):
        print("Поиск пиров в сети...")

    # Слот для кнопки запуска проверки известных пиров
    @Slot()
    def check_status(self):
        print("Проверка статуса пиров...")

    # Слот для добавления пира в бд
    @Slot()
    def add_peer(self):
        print("Добавление пира...")

    # Слот для кнопки принятия файлов
    @Slot(str)
    def accept_transfer(self, transfer_id):
        for t in self._transfers:
            if t["transfer_id"] == transfer_id:
                t["status"] = "accepted"
                transfer.init_receive_buffer(t["peer_id"], t)
                asyncio.ensure_future(self._send_ack_async(t["peer_id"]))
                asyncio.ensure_future(self._receive_async(t["peer_id"]))
                self.transfersChanged.emit()
        print("Передача принята...")

    # Слот для кнопки отказа от принятия файлов
    @Slot(str)
    def reject_transfer(self, transfer_id):
        for t in self._transfers:
            if t["transfer_id"] == transfer_id:
                t["status"] = "rejected"
                asyncio.ensure_future(self._send_reject_async(t["peer_id"]))
                self.transfersChanged.emit()
        print("Передача отклонена...")

    # Слот для поиска пиров
    @Slot(str)
    def search_peers(self, query):
        print(f"Поиск: {query}")

    # Слот для отправки файла выбранному пиру
    @Slot(str, str)
    def send_file(self, app, connection, peer_id, file_path):
        transfer.send_file(connection, file_path, peer_id, app)
        print(f"Отправка {file_path} пиру {peer_id}")

    # Свойство для проверки статуса пира
    @Property(dict, notify=peerStatusChanged)
    def peer_status(self):
        return self._peer_status  # dict[int, str] Словарь со статусом пиров

    # Свойство для отображения адреса пользователя
    @Property(str, notify=ownAddressChanged)
    def own_address(self):
        return f"{get_local_ip()}:{DEFAULT_PORT}"

    # Свойство для подсчёта онлайн пиров
    @Property(int, notify=peerStatusChanged)
    def online_count(self):
        return sum(1 for s in self._peer_status.values() if s == "online")

    # Свойство для отображения данных по передаче
    @Property(list, notify=transfersChanged)
    def transfers(self):
        return self._transfers

    # Метод, запускающий сигнал для обновления статуса пира в интерфейсе
    def update_peer_status(self, peer_id, status):
        self._peer_status[peer_id] = status
        self.status_changed.emit(peer_id, status)
        self._peer_status = dict(self._peer_status)
        self.peerStatusChanged.emit()

    async def _send_ack_async(self, peer_id):
        peer = db.get_peer(self.conn, peer_id)
        if peer:
            connection = await connect.connect_to_peer(peer["ip"], peer["port"])
            if connection:
                await transfer.send_ack(self.my_peer_id, connection)

    async def _send_reject_async(self, peer_id):
        peer = db.get_peer(self.conn, peer_id)
        if peer:
            connection = await connect.connect_to_peer(peer["ip"], peer["port"])
            if connection:
                await transfer.send_reject(self.my_peer_id, connection)

    def receive_chunk(self, peer_id, chunk_id, content):
        transfer.put_chunk(peer_id, chunk_id, content)
        asyncio.ensure_future(self._send_chunk_ack_async(peer_id, chunk_id))

    async def _send_chunk_ack_async(self, peer_id, chunk_id):
        peer = db.get_peer(self.conn, peer_id)
        if peer:
            connection = await connect.connect_to_peer(peer["ip"], peer["port"])
            if connection:
                ack = messages.create_ack(
                    self.my_peer_id, "FILE_CHUNK", chunk_id=chunk_id
                )
                await connect.send_message(connection[1], ack)

    async def _receive_async(self, peer_id):
        peer = db.get_peer(self.conn, peer_id)
        if peer:
            connection = await connect.connect_to_peer(peer["ip"], peer["port"])
            if connection:
                output_dir = os.path.expanduser("~/Downloads")
                ok, result = await transfer.recive_files(
                    peer_id, connection, self, output_dir
                )
                print(f"Приём завершён: {result}")

    async def send_sync_response(self, peer_id, resp):
        peer = db.get_peer(self.conn, peer_id)
        if peer:
            connection = await connect.connect_to_peer(peer["ip"], peer["port"])
            if connection:
                await connect.send_message(connection[1], resp)

    def update_transfer_status(self, peer_id, status):
        for t in self._transfers:
            if t["peer_id"] == peer_id:
                t["status"] = status
        self.transfersChanged.emit()
