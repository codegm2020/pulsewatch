"""PulseWatch — a small uptime-monitoring dashboard (Flask + SQLite)."""
from flask import Flask, request, jsonify, session, render_template

from . import db
from . import queries


def create_app():
    app = Flask(__name__)
    app.secret_key = "pulsewatch-dev-secret"

    @app.route("/")
    def index():
        conn = db.connect()
        monitors = [dict(r) for r in conn.execute(
            "SELECT id, name, host, status FROM monitors ORDER BY id"
        ).fetchall()]
        conn.close()
        return render_template("index.html", monitors=monitors,
                               user=session.get("user"))

    # search monitors by name
    @app.route("/search")
    def search():
        q = request.args.get("q", "")
        conn = db.connect()
        sql = "SELECT id, name, host, status FROM monitors WHERE name LIKE ?"
        rows = [dict(r) for r in conn.execute(sql, ('%' + q + '%',)).fetchall()]
        conn.close()
        return jsonify(results=rows)

    @app.route("/login", methods=["POST"])
    def login():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = db.connect()
        sql = ("SELECT id, username, role FROM users "
               "WHERE username = '%s' AND password = '%s'" % (username, password))
        row = conn.execute(sql).fetchone()
        conn.close()
        if row:
            session["user"] = {"id": row["id"], "username": row["username"], "role": row["role"]}
            return jsonify(ok=True, user=session["user"])
        return jsonify(ok=False), 401

    # check history for one monitor
    @app.route("/history")
    def history():
        monitor_id = request.args.get("monitor_id", "0")
        conn = db.connect()
        sql = "SELECT id, monitor_id, ts, status, latency_ms FROM checks WHERE monitor_id = " + monitor_id
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        conn.close()
        return jsonify(results=rows)

    # list monitors, optionally filtered by status or sorted by a column
    @app.route("/monitors")
    def monitors():
        status = request.args.get("status")
        sort = request.args.get("sort", "id")
        if status is not None:
            return jsonify(results=queries.monitors_by_status(status))
        conn = db.connect()
        sql = "SELECT id, name, host, status FROM monitors ORDER BY " + sort
        rows = [dict(r) for r in conn.execute(sql).fetchall()]
        conn.close()
        return jsonify(results=rows)

    @app.route("/add_monitor", methods=["POST"])
    def add_monitor():
        owner = request.form.get("owner", "anon")
        name = request.form.get("name", "")
        host = request.form.get("host", "")
        port = request.form.get("port", "443")
        conn = db.connect()
        conn.execute(
            "INSERT INTO monitors (owner, name, host, port, status) VALUES (?,?,?,?,?)",
            (owner, name, host, int(port) if str(port).isdigit() else 443, "unknown"),
        )
        conn.commit()
        conn.close()
        return jsonify(ok=True)

    # per-monitor summary for the dashboard
    @app.route("/summary")
    def summary():
        conn = db.connect()
        names = [r["name"] for r in conn.execute("SELECT name FROM monitors").fetchall()]
        conn.close()
        return jsonify(results=queries.summary_by_names(names))

    @app.route("/delete_monitor", methods=["POST"])
    def delete_monitor():
        mid = request.form.get("id", "0")
        conn = db.connect()
        conn.executescript("DELETE FROM monitors WHERE id = " + mid)
        conn.commit()
        conn.close()
        return jsonify(ok=True)

    # token-authenticated status endpoint for integrations
    @app.route("/api/status")
    def api_status():
        token = request.args.get("token", "")
        conn = db.connect()
        sql = "SELECT username, role FROM users WHERE api_token = '" + token + "'"
        row = conn.execute(sql).fetchone()
        conn.close()
        if row:
            return jsonify(ok=True, user=dict(row))
        return jsonify(ok=False), 403

    @app.route("/lookup")
    def lookup():
        host = request.args.get("host", "")
        return jsonify(results=queries.host_for_monitor(host))

    # most recent checks across all monitors
    @app.route("/recent")
    def recent():
        n = request.args.get("n", "5")
        try:
            limit = int(n)
        except ValueError:
            limit = 5
        conn = db.connect()
        rows = [dict(r) for r in conn.execute(
            "SELECT id, monitor_id, ts, status FROM checks ORDER BY id DESC LIMIT " + str(limit)
        ).fetchall()]
        conn.close()
        return jsonify(results=rows)

    return app


app = create_app()

if __name__ == "__main__":
    db.init_db()
    app.run(port=5000, debug=True)
