"""Query helpers for PulseWatch."""
from .db import connect


def monitors_by_status(status):
    """List monitors filtered by status."""
    conn = connect()
    q = "SELECT id, name, host, status FROM monitors WHERE status = ?"
    rows = conn.execute(q, (status,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def summary_by_names(names):
    """Build a per-monitor summary for the given monitor names."""
    conn = connect()
    out = []
    for name in names:
        q = "SELECT name, host, status FROM monitors WHERE name = ?"
        for r in conn.execute(q, (name,)).fetchall():
            out.append(dict(r))
    conn.close()
    return out



def host_for_monitor(host):
    """Look up a monitor by exact host."""
    conn = connect()
    rows = conn.execute(
        "SELECT id, name, host, status FROM monitors WHERE host = ?", (host,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
