import sqlite3
import threading
import time
from pathlib import Path

_lock = threading.RLock()


def init_db():
    with _lock:
        BASE_DIR = Path(__file__).resolve().parent
        DB_PATH = BASE_DIR / "peers.db"
        connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = connection.cursor()

        query_create = """
        CREATE TABLE IF NOT EXISTS storage(
            peer_id TEXT PRIMARY KEY, 
            peer_name TEXT,
            ip TEXT,
            port INTEGER,
            last_seen INTEGER,
            updated_at INTEGER,
            version INTEGER
            );
        """
        cursor.execute(query_create)
        query_create_identity = """
        CREATE TABLE IF NOT EXISTS identity(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            peer_id TEXT,
            peer_name TEXT,
            updated_at INTEGER
            );
        """
        cursor.execute(query_create_identity)
        connection.commit()
        return connection


def get_identity(conn):
    with _lock:
        cur = conn.cursor()
        cur.execute("SELECT peer_id, peer_name, updated_at FROM identity WHERE id = 1")
        row = cur.fetchone()
        if not row:
            return None
        return {"peer_id": row[0], "peer_name": row[1], "updated_at": row[2]}


def save_identity(conn, peer_id, peer_name):
    with _lock:
        cur = conn.cursor()
        updated_at = int(time.time())
        cur.execute(
            "INSERT OR REPLACE INTO identity (id, peer_id, peer_name, updated_at)"
            " VALUES (1, ?, ?, ?)",
            (peer_id, peer_name, updated_at),
        )
        conn.commit()


def add_peer(conn, peer_id, peer_name, ip, port):
    if peer_name is None or peer_id is None or ip is None or port is None:
        return False
    if int(port) < 0 or int(port) > 99999:
        return False
    with _lock:
        cur = conn.cursor()
        updated_at = int(time.time())
        last_seen = 0
        version = 1
        query = """INSERT INTO storage (peer_id, peer_name, ip, port, last_seen, updated_at, version) 
        VALUES(?, ?, ?, ?, ?, ?, ?)"""
        cur.execute("SELECT peer_id FROM storage WHERE peer_id = ?", (peer_id,))
        if cur.fetchone() is not None:
            return False
        cur.execute(query, (peer_id, peer_name, ip, port, last_seen, updated_at, version))
        conn.commit()
        return True


def get_peer(conn, peer_id):
    with _lock:
        cur = conn.cursor()
        cur.execute("SELECT * FROM storage WHERE peer_id = ?", (peer_id,))
        data = cur.fetchone()
        if not data:
            return None
        words_for_dict = [
            "peer_id",
            "peer_name",
            "ip",
            "port",
            "last_seen",
            "updated_at",
            "version",
        ]
        zip_dict = zip(words_for_dict, data)
        final_dict = dict(zip_dict)
        return final_dict


def get_all_peers(conn):
    with _lock:
        cur = conn.cursor()
        cur.execute("SELECT * FROM storage")
        all_users_data = cur.fetchall()
        words_for_dict = [
            "peer_id",
            "peer_name",
            "ip",
            "port",
            "last_seen",
            "updated_at",
            "version",
        ]
        zip_list = []
        for data in all_users_data:
            zip_list.append(zip(words_for_dict, data))
        final_dict = []
        for data_dict in zip_list:
            final_dict.append(dict(data_dict))
        return final_dict


def update_peer(conn, peer_id, **kwargs):
    with _lock:
        cur = conn.cursor()
        allowed_fields = {"ip", "peer_name", "port"}
        filtered_kwargs = {
            key: value for key, value in kwargs.items() if key in allowed_fields
        }
        if not filtered_kwargs:
            return False

        fields_to_check = list(filtered_kwargs.keys())
        select_query = f"SELECT {', '.join(fields_to_check)} FROM storage WHERE peer_id = ?"
        cur.execute(select_query, (peer_id,))
        old_values = cur.fetchone()
        if old_values is None:
            return False

        set_parts = []
        values = []
        for field_name, field_value in filtered_kwargs.items():
            set_parts.append(f"{field_name} = ?")
            values.append(field_value)

        updated_at = time.time()
        set_parts.append("updated_at = ?")
        values.append(updated_at)

        cur.execute("SELECT version FROM storage WHERE peer_id = ?", (peer_id,))
        row = cur.fetchone()
        if row is None:
            return False
        version = row[0]
        set_parts.append("version = ?")
        values.append(version)

        set_clause = ", ".join(set_parts)
        query = f"UPDATE storage SET {set_clause} WHERE peer_id = ?"
        values.append(peer_id)
        cur.execute(query, values)
        conn.commit()
        cur.execute(select_query, (peer_id,))
        new_values = cur.fetchone()
        if old_values == new_values:
            return False
        version = version + 1
        query_for_incr_version = """UPDATE storage SET version = ? WHERE peer_id = ?"""
        cur.execute(query_for_incr_version, (version, peer_id))
        conn.commit()
        return True


def delete_peer(conn, peer_id):
    with _lock:
        cur = conn.cursor()
        cur.execute("DELETE FROM storage WHERE peer_id = ?", (peer_id,))
        conn.commit()
        cur.execute("SELECT peer_id FROM storage WHERE peer_id = ?", (peer_id,))
        return cur.fetchone() is None


def update_last_seen(conn, peer_id):
    with _lock:
        cur = conn.cursor()
        last_seen = time.time()
        cur.execute(
            "UPDATE storage SET last_seen = ? WHERE peer_id = ?", (last_seen, peer_id)
        )
        conn.commit()


def delete_peer_with_address(conn, peer_id, ip, port):
    """Удаляет строки того же адреса (ip, port), но с другим peer_id.
    Чистит дубликаты, накопившиеся от старых запусков (идентичность менялась
    при каждом перезапуске). Один адрес = один пир."""
    with _lock:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM storage WHERE ip = ? AND port = ? AND peer_id <> ?",
            (ip, port, peer_id),
        )
        conn.commit()


def get_peers_since(conn, timestamp):
    with _lock:
        list_for_since = []
        all_peers = get_all_peers(conn)
        for value in all_peers:
            if value.get("updated_at") > timestamp:
                list_for_since.append(value)
        return list_for_since


def apply_sync(conn, peer_list):
    with _lock:
        cur = conn.cursor()
        our_list_peers = get_all_peers(conn)
        counter = 0
        index = {}
        for row in our_list_peers:
            index[row["peer_id"]] = row
        for incoming in peer_list:
            old = index.get(incoming["peer_id"])
            if old is None:
                if add_peer(
                    conn,
                    incoming["peer_id"],
                    incoming["peer_name"],
                    incoming["ip"],
                    incoming["port"],
                ):
                    counter += 1
            elif incoming["version"] > old["version"] or (
                incoming["version"] == old["version"]
                and incoming["updated_at"] > old["updated_at"]
            ):
                cur.execute(
                    "UPDATE storage SET peer_name = ?, ip = ?, port = ?,updated_at = ?, version = ? WHERE peer_id = ?",
                    (
                        incoming["peer_name"],
                        incoming["ip"],
                        incoming["port"],
                        incoming["updated_at"],
                        incoming["version"],
                        incoming["peer_id"],
                    ),
                )
                counter += 1
        conn.commit()
        return counter


if __name__ == "__main__":
    print("Use init_db() from main.py")
