import asyncio
import logging
import os
import time
import uuid

logger = logging.getLogger(__name__)

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from app import transfer
from data import database as db
from network import connection as connect
from network import get_local_ip, ip_equals_self, search
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
    notify = Signal(str)

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
        return transfer_record["transfer_id"]

    def new_peer_connected(self, name):
        self.new_peer.emit(name)

    @Slot()
    def find_peers(self):
        cfg = self.core.config
        coro = self._find_peers_async(cfg)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _find_peers_async(self, cfg):
        before = {p["peer_id"] for p in db.get_all_peers(self.core.db)}
        await search.send_discover_once(
            cfg.udp_port, self.core.my_peer_id, cfg.port, self.core.my_peer_name
        )
        await asyncio.sleep(5)
        after = {p["peer_id"] for p in db.get_all_peers(self.core.db)}
        new_peers = after - before
        if new_peers:
            self.notify.emit(f"Найдено новых пиров: {len(new_peers)}")
        else:
            self.notify.emit("Новые пиры не найдены")

    @Slot()
    def check_status(self):
        from network import heartbeat

        coro = self._check_status_async(heartbeat)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _check_status_async(self, heartbeat):
        peers = db.get_all_peers(self.core.db)
        if not peers:
            self.notify.emit("Список пиров пуст")
            return
        await heartbeat.check_peers_now(self.core)
        statuses = dict(self.core._peer_status)
        online = sum(1 for s in statuses.values() if s == "online")
        offline = sum(1 for s in statuses.values() if s == "offline")
        self.notify.emit(f"Онлайн: {online}, офлайн: {offline} из {len(peers)}")

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
                logger.info("ACCEPT transfer=%s peer=%s", str(transfer_id)[:8], str(t["peer_id"])[:8])
                writer = self._get_incoming_writer(t["peer_id"])
                coro1 = self._send_ack_async(t["peer_id"], writer)
                coro2 = self._receive_async(t["peer_id"], transfer_id, writer)
                if self._loop:
                    asyncio.run_coroutine_threadsafe(coro1, self._loop)
                    asyncio.run_coroutine_threadsafe(coro2, self._loop)
                self.transfersChanged.emit()
                return
        logger.warning("ACCEPT transfer not found id=%s", str(transfer_id)[:8])

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
                writer = self._get_incoming_writer(t["peer_id"])
                coro = self._send_reject_async(t["peer_id"], writer)
                if self._loop:
                    asyncio.run_coroutine_threadsafe(coro, self._loop)
                self.transfersChanged.emit()
                return

    @Slot(str)
    def search_peers(self, query):
        print(f"Поиск: {query}")
        cfg = self.core.config
        coro = search.send_discover_once(
            cfg.udp_port, self.core.my_peer_id, cfg.port, self.core.my_peer_name
        )
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
            logger.warning("SEND_ABORT peer not found id=%s", str(peer_id)[:8])
            return
        if ip_equals_self(peer["ip"]):
            logger.warning("SEND_ABORT ip belongs to self ip=%s", peer["ip"])
            print("Нельзя отправить файл самому себе")
            return
        logger.info("SEND_REQUEST peer=%s ip=%s port=%s file=%s", str(peer_id)[:8], peer["ip"], peer["port"], file_path)
        coro = self._send_file_async(peer_id, peer["ip"], peer["port"], file_path)
        if self._loop:
            asyncio.run_coroutine_threadsafe(coro, self._loop)
        else:
            logger.error("SEND_ABORT no event loop")

    async def _send_file_async(self, peer_id, ip, port, file_path):
        transfer_id = self.add_output_transfer(file_path, peer_id)

        def on_progress(percent):
            self._transfer_progress[transfer_id] = percent
            self.transferProgressChanged.emit()

        reader, writer = await connect.connect_to_peer(ip, port)
        if reader is None or writer is None:
            logger.error("SEND_CONNECT_FAILED ip=%s port=%s", ip, port)
            self._mark_output_status(transfer_id, "failed")
            return

        connection = (reader, writer)
        ok, reason = await transfer.send_file(
            connection, file_path, peer_id, self.core, progress_callback=on_progress
        )
        self._transfer_progress.pop(transfer_id, None)
        self.transferProgressChanged.emit()
        logger.info("SEND_DONE ok=%s reason=%s transfer=%s", ok, reason, str(transfer_id)[:8])
        self._mark_output_status(transfer_id, "completed" if ok else "failed")

    def _mark_output_status(self, transfer_id, status):
        for t in self.core._transfers:
            if t["transfer_id"] == transfer_id and t["direction"] == "out":
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

    async def _dial_peer(self, peer_id):
        """Открывает подключение к пиру (запасной путь, если входящего
        сокета, на котором пришёл META, уже нет). Возвращает writer."""
        peer = db.get_peer(self.core.db, peer_id)
        if not peer:
            return None
        reader, writer = await connect.connect_to_peer(peer["ip"], peer["port"])
        if reader is None or writer is None:
            return None
        return writer

    def _get_incoming_writer(self, peer_id):
        """Возвращает writer сокета, на котором пришёл META, чтобы отвечать
        отправителю по тому же соединению (без встречного подключения, которое
        не проходит за NAT/файрволом)."""
        writer = self.core._incoming_connections.get(peer_id)
        if writer is not None and not writer.is_closing():
            return writer
        self.core._incoming_connections.pop(peer_id, None)
        return None

    async def _send_ack_async(self, peer_id, writer=None):
        if writer is None:
            writer = await self._dial_peer(peer_id)
        if writer is not None and not writer.is_closing():
            await transfer.send_ack(self.core.my_peer_id, writer)

    async def _send_reject_async(self, peer_id, writer=None):
        if writer is None:
            writer = await self._dial_peer(peer_id)
        if writer is not None and not writer.is_closing():
            await transfer.send_reject(self.core.my_peer_id, writer)

    async def _send_chunk_ack_async(self, peer_id, chunk_id):
        writer = self._get_incoming_writer(peer_id)
        if writer is None:
            writer = await self._dial_peer(peer_id)
        if writer is not None and not writer.is_closing():
            ack = messages.create_ack(
                self.core.my_peer_id, "FILE_CHUNK", chunk_id=chunk_id
            )
            ok = await connect.send_message(writer, ack)
            if not ok:
                logger.warning("CHUNK_ACK_SEND_FAILED peer=%s chunk=%s", str(peer_id)[:8], chunk_id)
        else:
            logger.warning("CHUNK_ACK no connection peer=%s chunk=%s", str(peer_id)[:8], chunk_id)

    async def _receive_async(self, peer_id, transfer_id, writer=None):
        if writer is None:
            writer = await self._dial_peer(peer_id)
        if writer is None:
            peer = db.get_peer(self.core.db, peer_id)
            logger.error(
                "RECV_CONNECT_FAILED ip=%s port=%s",
                peer["ip"] if peer else "?",
                peer["port"] if peer else "?",
            )
            return
        output_dir = self._save_dir
        logger.info("RECV_START peer=%s transfer=%s save_dir=%s", str(peer_id)[:8], str(transfer_id)[:8], output_dir)

        def on_progress(percent):
            self._transfer_progress[transfer_id] = percent
            self.transferProgressChanged.emit()

        ok, reason = await transfer.recive_files(
            peer_id, writer, self, output_dir, progress_callback=on_progress
        )
        logger.info("RECV_DONE ok=%s reason=%s", ok, reason)
        self._transfer_progress.pop(transfer_id, None)
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
