import asyncio
import logging
import socket
import time
import uuid

from app import transfer
from data import database as db
from protocol import handler

logger = logging.getLogger(__name__)


class _Pending:
    def __init__(self):
        self.event = asyncio.Event()
        self.rejected = False
        self.error = False


class Config:
    def __init__(
        self,
        host="0.0.0.0",
        port=65432,
        udp_port=65433,
        bootstrap_ip=None,
        bootstrap_port=None,
        peer_name=None,
    ):
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.bootstrap_ip = bootstrap_ip
        self.bootstrap_port = bootstrap_port
        self.peer_name = peer_name or socket.gethostname()


class HermesApp:
    def __init__(
        self,
        conn,
        loop=None,
        on_transfer_changed=None,
        on_chunk_ack=None,
        config=None,
    ):
        self.db = conn
        self._loop = loop
        self.config = config if config is not None else Config()
        
        ident = db.get_identity(self.db)
        if ident and ident.get("peer_id"):
            self.my_peer_id = ident["peer_id"]
            self.my_peer_name = ident.get("peer_name") or self.config.peer_name or ident["peer_id"]
        else:
            self.my_peer_id = uuid.uuid4().hex
            self.my_peer_name = self.config.peer_name or self.my_peer_id
            db.save_identity(self.db, self.my_peer_id, self.my_peer_name)
            
        self._peer_status = {}
        self.pending_acks = {}
        self._incoming_connections = {}
        self._outbound_readers = {}
        self._transfers = []
        self.transfer_queue = []
        self.tcp_connections = []
        
        self._on_transfer_changed = on_transfer_changed
        self._on_chunk_ack = on_chunk_ack
        self._on_new_incoming = None
        self._on_sync_response = None
        self._on_peers_changed = None
        self._on_peer_status_changed = None

    def parse_message(self, raw_string):
        return handler.parse_message(raw_string)

    def update_peer_status(self, peer_id, status):
        self._peer_status[peer_id] = status
        self._peer_status = dict(self._peer_status)
        if self._on_peers_changed:
            self._on_peers_changed()
        if self._on_peer_status_changed:
            self._on_peer_status_changed()

    def get_status(self, peer_id):
        return self._peer_status.get(peer_id, "unknown")

    def get_all_status(self):
        return dict(self._peer_status)

    def get_all_peers(self, conn=None):
        return db.get_all_peers(self.db)

    def on_peer_discovered(self, peer_id, ip, port, name=None):
        if not peer_id:
            return
        peer_name = name or peer_id
        existing = db.get_peer(self.db, peer_id)
        if existing is None:
            db.add_peer(self.db, peer_id, peer_name, ip, port)
        else:
            db.update_peer(self.db, peer_id, ip=ip, port=port, peer_name=peer_name)
        db.delete_peer_with_address(self.db, peer_id, ip, port)
        db.update_last_seen(self.db, peer_id)
        self.update_peer_status(peer_id, "online")

    def register_pending(self, msg_type, peer_id, chunk_id=None):
        key = (peer_id, msg_type, chunk_id)
        logger.info(f"🔑 register_pending: key={key}")
        self.pending_acks[key] = _Pending()
        return key

    # 🔥 ИСПРАВЛЕНО: "Умный" поиск, если peer_id рассинхронизирован
    def resolve_pending(self, msg_type, peer_id, chunk_id=None):
        key = (peer_id, msg_type, chunk_id)
        logger.info(f"🔍 resolve_pending: ищу key={key}")
        
        pending = self.pending_acks.get(key)
        
        if pending is None:
            logger.warning(f"⚠️ Точный ключ не найден. Ищу по msg_type='{msg_type}' и chunk_id={chunk_id} (возможна рассинхронизация peer_id в БД)")
            for (p_id, m_type, c_id), p in self.pending_acks.items():
                if m_type == msg_type and c_id == chunk_id:
                    logger.info(f"✅ Найдено совпадение! Использую peer_id='{p_id}' вместо '{peer_id}'")
                    pending = p
                    key = (p_id, m_type, c_id)
                    break

        if pending is None:
            logger.error(f"❌ Ключ так и не найден в pending_acks!")
            return
        
        logger.info(f"✅ Ключ найден, вызываю event.set()")
        pending.event.set()
        logger.info(f"✅ event.set() выполнен")

    def reject_pending(self, peer_id):
        pending = self.pending_acks.get((peer_id, "META", None))
        if pending is not None:
            pending.rejected = True
            pending.event.set()

    def error_pending(self, peer_id):
        for (pid, msg_type, chunk_id), pending in self.pending_acks.items():
            if pid == peer_id:
                pending.error = True
                pending.event.set()

    async def wait_for_ack(self, msg_type, peer_id, chunk_id=None, timeout=10, max_retries=3, resend=None):
        key = (peer_id, msg_type, chunk_id)
        logger.info(f"⏳ wait_for_ack: key={key}, timeout={timeout}")
        
        for i in range(max_retries):
            pending = self.pending_acks.get(key)
            if pending is None:
                logger.error(f"❌ wait_for_ack: pending is None для key={key}")
                return (False, None)
            
            logger.info(f"🔄 Попытка {i+1}/{max_retries}: жду event.wait()")
            try:
                await asyncio.wait_for(pending.event.wait(), timeout)
                logger.info(f"✅ event.wait() разблокирован!")
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Таймаут на попытке {i+1}")
                if resend is not None:
                    resend()
                continue
            else:
                self.pending_acks.pop(key, None)
                if pending.rejected:
                    logger.info(f"❌ Получен REJECT")
                    return (False, "REJECT")
                if pending.error:
                    logger.info(f"❌ Получен ERROR")
                    return (False, "ERROR")
                logger.info(f"✅ ACK получен успешно")
                return (True, None)
        
        logger.error(f"❌ Все {max_retries} попыток исчерпаны")
        self.pending_acks.pop(key, None)
        return (False, None)

    def add_incoming_transfer(self, meta, peer_id):
        peer = db.get_peer(self.db, peer_id)
        peer_name = peer["peer_name"] if peer else peer_id
        transfer_id = uuid.uuid4().hex
        transfer_record = {
            "transfer_id": transfer_id,
            "direction": "in",
            "peer_id": peer_id,
            "peer_name": peer_name,
            "filename": meta["filename"],
            "file_size": meta["file_size"],
            "sha256": meta["sha256"],
            "chunks_count": meta["chunks_count"],
            "status": "pending",
            "timestamp": int(time.time()),
        }
        self._transfers.insert(0, transfer_record)
        self._transfers = list(self._transfers)
        transfer.init_receive_buffer(peer_id, transfer_record)
        if self._on_new_incoming:
            self._on_new_incoming(transfer_record)
        if self._on_transfer_changed:
            self._on_transfer_changed()

    def receive_chunk(self, peer_id, chunk_id, content):
        transfer.put_chunk(peer_id, chunk_id, content)
        if self._on_chunk_ack:
            self._on_chunk_ack(peer_id, chunk_id)

    def update_transfer_status(self, peer_id, status):
        for t in self._transfers:
            if t["peer_id"] == peer_id:
                t["status"] = status
        if self._on_transfer_changed:
            self._on_transfer_changed()

    def on_user_add_peer(self, name, ip, port):
        peer_id = uuid.uuid4().hex
        ok = db.add_peer(self.db, peer_id, name, ip, port)
        if ok and self._on_transfer_changed:
            self._on_transfer_changed()
        return ok

    def on_user_search_peers(self):
        pass

    def on_user_send_file(self, peer_id, filepath):
        pass

    async def send_sync_response(self, peer_id, resp):
        if self._on_sync_response:
            await self._on_sync_response(peer_id, resp)