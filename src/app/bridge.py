import asyncio
import os
import time
import uuid

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from app import transfer
from data import database as db
from network import connection as connect
from network import get_local_ip, search
from protocol import messages


class AppBridge(QObject):
    ### Сигналы ###
    new_peer = Signal(str)
    peerStatusChanged = Signal()
    ownAddressChanged = Signal()
    transfersChanged = Signal()
    peersChanged = Signal()
    transferProgressChanged = Signal()
    incomingTransfer = Signal(str)

    def __init__(self, core, loop=None, parent=None):
        super().__init__(parent)
        self.core = core
        self._loop = loop
        self._transfer_progress = {}
        self._save_dir = os.path.expanduser("~/Downloads")

    def add_output_transfer(self, filepath, peer_id):
        peer = db.get_peer(self.core.db, peer_id)
        peer_name = peer["peer_name"] if peer else peer_id
        transfer_record = {
            "transfer_id": uuid.uuid4().hex,
            "direction": "out",
            "peer_id": peer_id,
            "peer_name": peer_name,
            "filename": os.path.basename(filepath),
            "file_size": os.path.getsize(filepath),
            "sha256": "",
            "chunks_count": 0,
            "status": "sending",
            "timestamp": int(time.time()),
        }
        self.core._transfers.insert(0, transfer_record)
        self.core._transfers = list(self.core._transfers)
        self.transfersChanged.emit()

    def new_peer_connected(self, name):
        self.new_peer.emit(name)

    @Slot()
    def find_peers(self):
        cfg = self.core.config
        coro = search.send_discover_once(cfg.udp_port, self.core.my_peer_id, cfg.port)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    @Slot()
    def check_status(self):
        from network import heartbeat

        if self._loop:
            asyncio.run_coroutine_threadsafe(
                heartbeat.check_peers_now(self.core), self._loop
            )
        print("Проверка статуса пиров...")

    @Slot(str, str, str, result=bool)
    def add_peer(self, name, ip, port):
        if not name or not ip or not port:
            return False
        try:
            port_int = int(port)
        except ValueError:
            return False
        peer_id = uuid.uuid4().hex
        ok = db.add_peer(self.core.db, peer_id, name, ip, port_int)
        if ok:
            self.peersChanged.emit()
        return ok

    @Slot(str, result=bool)
    def remove_peer(self, peer_id):
        ok = db.delete_peer(self.core.db, peer_id)
        if ok:
            self.peersChanged.emit()
        return ok

    @Slot(str)
    def accept_transfer(self, transfer_id):
        for t in self.core._transfers:
            if t["transfer_id"] == transfer_id:
                t["status"] = "accepted"
                coro1 = self._send_ack_async(t["peer_id"])
                coro2 = self._receive_async(t["peer_id"])
                if self._loop:
                    asyncio.run_coroutine_threadsafe(coro1, self._loop)
                    asyncio.run_coroutine_threadsafe(coro2, self._loop)
                self.transfersChanged.emit()
                return

    @Slot(result=str)
    def choose_save_dir(self):
        directory = QFileDialog.getExistingDirectory(
            None, "Выберите папку для приёма файла", self._save_dir
        )
        if directory:
            self._save_dir = directory
            return directory
        return ""

    @Slot(str)
    def reject_transfer(self, transfer_id):
        for t in self.core._transfers:
            if t["transfer_id"] == transfer_id:
                t["status"] = "rejected"
                coro = self._send_reject_async(t["peer_id"])
                if self._loop:
                    asyncio.run_coroutine_threadsafe(coro, self._loop)
                self.transfersChanged.emit()
                return

    @Slot(str)
    def search_peers(self, query):
        print(f"Поиск: {query}")
        cfg = self.core.config
        coro = search.send_discover_once(cfg.udp_port, self.core.my_peer_id, cfg.port)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    @Slot(str)
    def choose_send_file(self, peer_id):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Выберите файл для отправки", ""
        )
        if file_path:
            self.send_file(peer_id, file_path)

    @Slot(str, str)
    def send_file(self, peer_id, file_path):
        peer = db.get_peer(self.core.db, peer_id)
        if not peer:
            return
        coro = self._send_file_async(peer_id, peer["ip"], peer["port"], file_path)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _send_file_async(self, peer_id, ip, port, file_path):
        self.add_output_transfer(file_path, peer_id)

        def on_progress(percent):
            self._transfer_progress[peer_id] = percent
            self.transferProgressChanged.emit()

        reader, writer = await connect.connect_to_peer(ip, port)
        if reader is None or writer is None:
            self._mark_output_status(peer_id, "failed")
            return

        connection = (reader, writer)
        ok, _ = await transfer.send_file(
            connection, file_path, peer_id, self.core, progress_callback=on_progress
        )
        self._transfer_progress.pop(peer_id, None)
        self.transferProgressChanged.emit()
        self._mark_output_status(peer_id, "completed" if ok else "failed")

    def _mark_output_status(self, peer_id, status):
        for t in self.core._transfers:
            if t["peer_id"] == peer_id and t["direction"] == "out":
                t["status"] = status
        self.transfersChanged.emit()

    @Property(dict, notify=peerStatusChanged)
    def peer_status(self):
        return self.core._peer_status

    @Property(str, notify=ownAddressChanged)
    def own_address(self):
        return f"{get_local_ip()}:{self.core.config.port}"

    @Property(int, notify=peerStatusChanged)
    def online_count(self):
        return sum(1 for s in self.core._peer_status.values() if s == "online")

    @Property(list, notify=transfersChanged)
    def transfers(self):
        return self.core._transfers

    @Property(list, notify=peersChanged)
    def peers(self):
        return db.get_all_peers(self.core.db)

    @Property(dict, notify=transferProgressChanged)
    def transfer_progress(self):
        return self._transfer_progress

    async def _send_ack_async(self, peer_id):
        peer = db.get_peer(self.core.db, peer_id)
        if peer:
            reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
            if reader is not None and writer is not None:
                await transfer.send_ack(self.core.my_peer_id, (reader, writer))

    async def _send_reject_async(self, peer_id):
        peer = db.get_peer(self.core.db, peer_id)
        if peer:
            reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
            if reader is not None and writer is not None:
                await transfer.send_reject(self.core.my_peer_id, (reader, writer))

    async def _send_chunk_ack_async(self, peer_id, chunk_id):
        peer = db.get_peer(self.core.db, peer_id)
        if peer:
            reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
            if reader is not None and writer is not None:
                ack = messages.create_ack(
                    self.core.my_peer_id, "FILE_CHUNK", chunk_id=chunk_id
                )
                await connect.send_message(writer, ack)

    async def _receive_async(self, peer_id):
        peer = db.get_peer(self.core.db, peer_id)
        if peer:
            reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
            if reader is not None and writer is not None:
                connection = (reader, writer)
                output_dir = self._save_dir

                def on_progress(percent):
                    self._transfer_progress[peer_id] = percent
                    self.transferProgressChanged.emit()

                _, _ = await transfer.recive_files(
                    peer_id, connection, self, output_dir, progress_callback=on_progress
                )
                self._transfer_progress.pop(peer_id, None)
                self.transferProgressChanged.emit()

    async def send_sync_response(self, peer_id, resp):
        peer = db.get_peer(self.core.db, peer_id)
        if peer:
            reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
            if reader is not None and writer is not None:
                await connect.send_message(writer, resp)

    def update_peer_status(self, peer_id, status):
        self.core.update_peer_status(peer_id, status)
        self.peerStatusChanged.emit()
