import sqlite3
from pathlib import Path

def init_db():

    BASE_DIR = Path(__file__).resolve().parent
    DB_PATH = BASE_DIR / "peers.db"
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    query_create = '''
    CREATE TABLE IF NOT EXISTS storage(
        peer_id TEXT PRIMARY KEY, 
        peer_name TEXT,
        ip TEXT,
        port INTEGER,
        last_seen INTEGER,
        updated_at INTEGER,
        version INTEGER
        );
    '''
    cursor.execute(query_create)
    connection.commit()
    return connection


def main():
    init_db()

if __name__ == "__main__":
    main()