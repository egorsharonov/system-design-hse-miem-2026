import os
import random
import time
from datetime import datetime

import psycopg2


WRITE_DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_WRITE_PORT", "5002"),
    "sslmode": "disable",
    "dbname": os.getenv("PG_DATABASE", "postgres"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "target_session_attrs": "read-write",
}

READ_DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_READ_PORT", "5001"),
    "sslmode": "disable",
    "dbname": os.getenv("PG_DATABASE", "postgres"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "postgres"),
    "target_session_attrs": "any",
}

EVENT_TYPES = ["login", "logout", "click", "purchase", "view_page", "error"]
MAX_TICKS = int(os.getenv("MAX_TICKS", "0"))


def now():
    return datetime.now().strftime("%H:%M:%S")


def connect(config, label):
    conn = psycopg2.connect(**config)
    conn.autocommit = False
    print(f"[{now()}] CONNECTED {label} via localhost:{config['port']}")
    return conn


def get_random_owner(cursor):
    cursor.execute("SELECT owner_name FROM owners ORDER BY RANDOM() LIMIT 1;")
    result = cursor.fetchone()
    return result[0] if result else "Unknown"


def insert_event(conn):
    with conn.cursor() as cur:
        owner = get_random_owner(cur)
        event = random.choice(EVENT_TYPES)
        cur.execute(
            "INSERT INTO events (event_name, owner_name) VALUES (%s, %s) RETURNING id",
            (event, owner),
        )
        event_id = cur.fetchone()[0]
    conn.commit()
    print(f"[{now()}] WRITE primary: inserted id={event_id}, event={event}, owner={owner}")


def read_latest(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, event_name, owner_name FROM events ORDER BY id DESC LIMIT 3")
        rows = cur.fetchall()
    print(f"[{now()}] READ replicas: last ids={[row[0] for row in rows]}")


def close_quietly(conn):
    if conn is not None and not conn.closed:
        conn.close()


def main():
    print("--- STARTING PATRONI TRAFFIC GENERATOR ---")
    print(f"write endpoint: localhost:{WRITE_DB_CONFIG['port']}")
    print(f"read endpoint:  localhost:{READ_DB_CONFIG['port']}")

    write_conn = None
    read_conn = None
    tick = 0

    while True:
        try:
            if write_conn is None or write_conn.closed:
                write_conn = connect(WRITE_DB_CONFIG, "write")
            insert_event(write_conn)
        except psycopg2.OperationalError as error:
            print(f"[{now()}] WRITE CONNECTION LOST, failover may be in progress: {error}")
            close_quietly(write_conn)
            write_conn = None
        except Exception as error:
            print(f"[{now()}] WRITE ERROR: {error}")
            close_quietly(write_conn)
            write_conn = None

        if tick % 2 == 0:
            try:
                if read_conn is None or read_conn.closed:
                    read_conn = connect(READ_DB_CONFIG, "read")
                read_latest(read_conn)
            except psycopg2.OperationalError as error:
                print(f"[{now()}] READ CONNECTION LOST, replica endpoint may be changing: {error}")
                close_quietly(read_conn)
                read_conn = None
            except Exception as error:
                print(f"[{now()}] READ ERROR: {error}")
                close_quietly(read_conn)
                read_conn = None

        tick += 1
        if MAX_TICKS > 0 and tick >= MAX_TICKS:
            print(f"[{now()}] FINISHED after {MAX_TICKS} ticks")
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
