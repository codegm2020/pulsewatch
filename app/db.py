"""SQLite layer for PulseWatch — connection, schema, and seed data."""
import os
import sqlite3

DB_PATH = os.environ.get("PULSEWATCH_DB", os.path.join(os.path.dirname(__file__), "pulsewatch.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT UNIQUE NOT NULL,
    password  TEXT NOT NULL,
    role      TEXT NOT NULL DEFAULT 'viewer',
    api_token TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS monitors (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    owner        TEXT NOT NULL,
    name         TEXT NOT NULL,
    host         TEXT NOT NULL,
    port         INTEGER NOT NULL DEFAULT 443,
    status       TEXT NOT NULL DEFAULT 'unknown',
    last_checked TEXT
);

CREATE TABLE IF NOT EXISTS checks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER NOT NULL,
    ts         TEXT NOT NULL,
    status     TEXT NOT NULL,
    latency_ms INTEGER
);
"""

# Seed data for local development.
SEED_USERS = [
    # username, password, role, api_token
    ("admin",   "s3cr3t-admin-key", "admin",  "tok_admin_9f13"),
    ("alice",   "alice-pw-01",       "editor", "tok_alice_44a2"),
    ("bob",     "bob-pw-02",         "viewer", "tok_bob_7c8e"),
]

SEED_MONITORS = [
    # owner, name, host, port, status
    ("admin", "Prod API",      "api.pulsewatch.io",   443, "up"),
    ("admin", "Marketing Site","www.pulsewatch.io",   443, "up"),
    ("alice", "Staging API",   "staging.internal",    8443, "down"),
    ("alice", "DB Replica",    "db-replica.internal", 5432, "up"),
    ("bob",   "Blog",          "blog.pulsewatch.io",  443, "degraded"),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(reset=True):
    """Create schema and seed data."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = connect()
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO users (username, password, role, api_token) VALUES (?,?,?,?)",
        SEED_USERS,
    )
    conn.executemany(
        "INSERT INTO monitors (owner, name, host, port, status) VALUES (?,?,?,?,?)",
        SEED_MONITORS,
    )
    # a few check-history rows per monitor
    rows = []
    for mid in range(1, len(SEED_MONITORS) + 1):
        for i in range(3):
            rows.append((mid, f"2026-09-1{i}T00:00:00", "up" if i % 2 == 0 else "down", 40 + i * 5))
    conn.executemany(
        "INSERT INTO checks (monitor_id, ts, status, latency_ms) VALUES (?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"initialized {DB_PATH}")
