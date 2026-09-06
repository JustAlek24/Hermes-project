import asyncio
import time
import uuid

from app import transfer
from data import database as db
from protocol import handler


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
    ):
        self.host = host
        self.port = port
        self.udp_port = udp_port
        self.bootstrap_ip = bootstrap_ip
        self.bootstrap_port = bootstrap_port


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
        self.my_peer_id = uuid.uuid4().hex
        self._peer_status = {}
        self.pending_acks = {}
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

    def on_peer_discovered(self, peer_id, ip, port):
        if not peer_id:
            return
        existing = db.get_peer(self.db, peer_id)
        if existing is None:
            db.add_peer(self.db, peer_id, peer_id, ip, port)
        else:
            db.update_peer(self.db, peer_id, ip=ip, port=port)
        db.update_last_seen(self.db, peer_id)
        self.update_peer_status(peer_id, "online")

    def register_pending(self, msg_type, peer_id, chunk_id=None):
        key = (peer_id, msg_type, chunk_id)

        self.pending_acks[key] = _Pending()

        return key

    def resolve_pending(self, msg_type, peer_id, chunk_id=None):
        pending = self.pending_acks.get((peer_id, msg_type, chunk_id))

        if pending is not None:
            pending.event.set()

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

    async def wait_for_ack(
        self, msg_type, peer_id, chunk_id=None, timeout=10, max_retries=3, resend=None
    ):
        key = (peer_id, msg_type, chunk_id)

        for i in range(max_retries):
            pending = self.pending_acks.get(key)

            if pending is None:
                return (False, None)

            try:
                await asyncio.wait_for(pending.event.wait(), timeout)
            except asyncio.TimeoutError:
                if resend is not None:
                    resend()
                continue
            else:
                self.pending_acks.pop(key, None)
                if pending.rejected:
                    return (False, "REJECT")
                if pending.error:
                    return (False, "ERROR")
                return (True, None)

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
