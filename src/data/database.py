import sqlite3
import time
from pathlib import Path


def init_db():
    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = BASE_DIR / "peers.db"
    connection = sqlite3.connect(DB_PATH)
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
    connection.commit()
    return connection


def add_peer(conn, peer_id, peer_name, ip, port):
    if peer_name is None or peer_id is None or ip is None or port is None:
        return False
    if int(port) < 0 or int(port) > 99999:
        return False
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
    cur = conn.cursor()
    cur.execute("DELETE FROM storage WHERE peer_id = ?", (peer_id,))
    conn.commit()
    cur.execute("SELECT peer_id FROM storage WHERE peer_id = ?", (peer_id,))
    return cur.fetchone() is None


def update_last_seen(conn, peer_id):
    cur = conn.cursor()
    last_seen = time.time()
    cur.execute(
        "UPDATE storage SET last_seen = ? WHERE peer_id = ?", (last_seen, peer_id)
    )
    conn.commit()

def get_peers_since(conn, timestamp):
    list_for_since = []
    all_peers = get_all_peers(conn)
    for value in all_peers:
        if value.get("updated_at") > timestamp:
             list_for_since.append(value)
    return list_for_since

def apply_sync(conn, peer_list):
    cur = conn.cursor()
    our_list_peers = get_all_peers(conn)
    counter = 0
    index = {}
    for row in our_list_peers:
        index[row["peer_id"]] = row
    for incoming in peer_list:
        old = index.get(incoming["peer_id"])
        if old is None:
            if add_peer(conn, incoming["peer_id"], incoming["peer_name"], incoming["ip"], incoming["port"]):
                counter += 1
        elif incoming["version"] > old["version"] or (incoming["version"] == old["version"] and incoming["updated_at"] > old["updated_at"]):
            cur.execute("UPDATE storage SET peer_name = ?, ip = ?, port = ?,updated_at = ?, version = ? WHERE peer_id = ?",
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

def main():
    connect = init_db()
    '''print(add_peer(connect, "2", "Козявка", "124.124.4.4", "44555"))
    print(add_peer(connect, "1", "Чмо_В_Ипотеке", "192.168.1.1", "8080"))
    print(add_peer(connect, "2", "Диванный_Эксперт", "10.0.0.1", "3000"))
    print(add_peer(connect, "3", "Гнида", "172.16.0.1", "666"))
    print(add_peer(connect, "4", "Овощ", "192.168.2.28", "2828"))
    print(add_peer(connect, "5", "Дибил", "10.10.10.66", "911"))
    print(add_peer(connect, "6", "Очкошник", "192.168.31.1", "4242"))
    print(add_peer(connect, "7", "Бездарность", "172.18.0.1", "5555"))
    print(add_peer(connect, "8", "Скотина бессовестная", "10.255.255.1", "1984"))
    print(add_peer(connect, "9", "Гандон", "192.168.100.2", "2000"))
    print(add_peer(connect, "10", "У меня идеи закончились", "172.25.0.1", "1488"))
    print(get_peer(connect, "2"))'''
    #print(get_all_peers(connect))
    #print(update_peer(connect, "2", ip="444.444.1.1", peername="Goluboy", port="40555"))
    #print(update_peer(connect, "2", ip="444.444.1.1", peername="Goluboy", port="40555"))
    #print(update_peer(connect, "2", ip="444.444.1.1", peername="Goluboy", port="40555"))
    print(add_peer(connect, "301", "local A", "10.0.0.1", "1000"))     # True, version 1
    print(add_peer(connect, "302", "local B", "10.0.0.2", "1001"))     # True, version 1
    print(update_peer(connect, "302", ip="10.0.0.22"))                  # True, version 102 стала 2

    #пир отсутствует локально -> 1 
    print(apply_sync(connect, [{"peer_id": "303", "peer_name": "new guy", "ip": "10.0.0.3", "port": "1002",
                            "last_seen": 0, "updated_at": 100, "version": 1}]))
    #входящий новее (5 > 1) -> 1 
    print(apply_sync(connect, [{"peer_id": "301", "peer_name": "A v5", "ip": "10.0.0.9", "port": "1000",
                            "last_seen": 0, "updated_at": 200, "version": 5}]))
    #входящий старее (1 < 2) -> 0 
    print(apply_sync(connect, [{"peer_id": "302", "peer_name": "stale B", "ip": "9.9.9.9", "port": "9999",
                            "last_seen": 0, "updated_at": 50, "version": 1}]))

    #print(get_peers_since(connect, timestamp=1787760232))

if __name__ == "__main__":
    main()
