"""
SQLite storage layer.

All SQL lives in this file, so the rest of the project never writes SQL.
One connection is shared and protected by a lock (SQLite is fast enough for
this workload; writes are also batched by the Ingestor).
"""
import json
import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id    TEXT    NOT NULL,
    device_type  TEXT    NOT NULL DEFAULT 'unknown',
    interface    TEXT    NOT NULL DEFAULT '',
    ts_ms        INTEGER NOT NULL,
    rx_bps       REAL    NOT NULL,
    tx_bps       REAL    NOT NULL,
    capacity_bps REAL,
    util_pct     REAL,
    latency_ms   REAL,
    loss_pct     REAL
);
CREATE INDEX IF NOT EXISTS idx_metrics_dev_ts ON metrics(device_id, ts_ms);
CREATE INDEX IF NOT EXISTS idx_metrics_ts     ON metrics(ts_ms);

CREATE TABLE IF NOT EXISTS devices (
    device_id     TEXT PRIMARY KEY,
    device_type   TEXT NOT NULL,
    first_seen_ms INTEGER NOT NULL,
    last_seen_ms  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT    NOT NULL,
    metric      TEXT    NOT NULL,
    severity    TEXT    NOT NULL,
    value       REAL,
    peak_value  REAL,
    threshold   REAL,
    message     TEXT    NOT NULL,
    opened_ms   INTEGER NOT NULL,
    resolved_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_alerts_open ON alerts(resolved_ms, opened_ms);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

METRIC_COLUMNS = ("device_id", "device_type", "interface", "ts_ms", "rx_bps", "tx_bps",
                  "capacity_bps", "util_pct", "latency_ms", "loss_pct")


class Database:
    def __init__(self, path: str = "telemetry.db"):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------ metrics
    def insert_metrics(self, rows):
        """rows: list of dicts with the METRIC_COLUMNS keys."""
        if not rows:
            return
        values = [tuple(r[c] for c in METRIC_COLUMNS) for r in rows]
        last_seen = {}
        for r in rows:
            d = last_seen.setdefault(r["device_id"], [r["device_type"], r["ts_ms"], r["ts_ms"]])
            d[1] = min(d[1], r["ts_ms"])
            d[2] = max(d[2], r["ts_ms"])
        with self._lock:
            self._conn.executemany(
                "INSERT INTO metrics (" + ",".join(METRIC_COLUMNS) + ") VALUES (?,?,?,?,?,?,?,?,?,?)",
                values)
            for dev, (dtype, first, last) in last_seen.items():
                self._conn.execute(
                    "INSERT INTO devices(device_id, device_type, first_seen_ms, last_seen_ms) "
                    "VALUES (?,?,?,?) ON CONFLICT(device_id) DO UPDATE SET "
                    "device_type=excluded.device_type, "
                    "last_seen_ms=MAX(last_seen_ms, excluded.last_seen_ms)",
                    (dev, dtype, first, last))
            self._conn.commit()

    def latest_per_device(self):
        sql = """
        SELECT m.* FROM metrics m
        JOIN (SELECT device_id, MAX(ts_ms) AS mts FROM metrics GROUP BY device_id) x
          ON m.device_id = x.device_id AND m.ts_ms = x.mts
        GROUP BY m.device_id
        """
        with self._lock:
            return {r["device_id"]: dict(r) for r in self._conn.execute(sql)}

    def list_devices(self):
        with self._lock:
            return [dict(r) for r in self._conn.execute(
                "SELECT * FROM devices ORDER BY device_id")]

    def query_raw(self, start_ms, end_ms, device_id=None, limit=50000):
        sql = ("SELECT device_id, ts_ms, rx_bps, tx_bps, capacity_bps, util_pct, latency_ms, loss_pct "
               "FROM metrics WHERE ts_ms BETWEEN ? AND ?")
        args = [start_ms, end_ms]
        if device_id:
            sql += " AND device_id = ?"
            args.append(device_id)
        sql += " ORDER BY ts_ms LIMIT ?"
        args.append(limit)
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args)]

    def query_bucketed(self, start_ms, end_ms, bucket_s, device_id=None):
        """Average the data into buckets of bucket_s seconds (downsampling)."""
        size = int(bucket_s * 1000)
        sql = ("SELECT device_id, (ts_ms / ?) * ? AS ts_ms, "
               "AVG(rx_bps) AS rx_bps, AVG(tx_bps) AS tx_bps, AVG(capacity_bps) AS capacity_bps, "
               "AVG(util_pct) AS util_pct, AVG(latency_ms) AS latency_ms, AVG(loss_pct) AS loss_pct "
               "FROM metrics WHERE ts_ms BETWEEN ? AND ?")
        args = [size, size, start_ms, end_ms]
        if device_id:
            sql += " AND device_id = ?"
            args.append(device_id)
        sql += " GROUP BY device_id, (ts_ms / ?) ORDER BY ts_ms"
        args.append(size)
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args)]

    def iter_export(self, start_ms, end_ms, device_id=None, chunk=5000):
        """Yield every raw row in the range, in chunks (used for CSV export)."""
        last_id = 0
        while True:
            sql = ("SELECT id, device_id, device_type, interface, ts_ms, rx_bps, tx_bps, capacity_bps, "
                   "util_pct, latency_ms, loss_pct FROM metrics "
                   "WHERE id > ? AND ts_ms BETWEEN ? AND ?")
            args = [last_id, start_ms, end_ms]
            if device_id:
                sql += " AND device_id = ?"
                args.append(device_id)
            sql += " ORDER BY id LIMIT ?"
            args.append(chunk)
            with self._lock:
                rows = [dict(r) for r in self._conn.execute(sql, args)]
            if not rows:
                return
            last_id = rows[-1]["id"]      # remember BEFORE yielding (callers may modify rows)
            for r in rows:
                yield r

    def prune(self, older_than_ms):
        with self._lock:
            cur = self._conn.execute("DELETE FROM metrics WHERE ts_ms < ?", (older_than_ms,))
            self._conn.execute(
                "DELETE FROM alerts WHERE resolved_ms IS NOT NULL AND resolved_ms < ?", (older_than_ms,))
            self._conn.commit()
            return cur.rowcount

    def count_metrics(self):
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]

    # ------------------------------------------------------------------- alerts
    def open_alert(self, device_id, metric, severity, value, threshold, message, opened_ms):
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO alerts(device_id, metric, severity, value, peak_value, threshold, message, opened_ms) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (device_id, metric, severity, value, value, threshold, message, opened_ms))
            self._conn.commit()
            return cur.lastrowid

    def update_alert(self, alert_id, severity=None, peak_value=None, threshold=None, message=None):
        sets, args = [], []
        for col, val in (("severity", severity), ("peak_value", peak_value),
                         ("threshold", threshold), ("message", message)):
            if val is not None:
                sets.append(f"{col} = ?")
                args.append(val)
        if not sets:
            return
        args.append(alert_id)
        with self._lock:
            self._conn.execute(f"UPDATE alerts SET {', '.join(sets)} WHERE id = ?", args)
            self._conn.commit()

    def resolve_alert(self, alert_id, resolved_ms):
        with self._lock:
            self._conn.execute("UPDATE alerts SET resolved_ms = ? WHERE id = ?", (resolved_ms, alert_id))
            self._conn.commit()

    def resolve_all_active(self, resolved_ms):
        with self._lock:
            self._conn.execute("UPDATE alerts SET resolved_ms = ? WHERE resolved_ms IS NULL", (resolved_ms,))
            self._conn.commit()

    def query_alerts(self, state="all", device_id=None, since_ms=None, limit=200):
        sql = "SELECT * FROM alerts WHERE 1=1"
        args = []
        if state == "active":
            sql += " AND resolved_ms IS NULL"
        elif state == "resolved":
            sql += " AND resolved_ms IS NOT NULL"
        if device_id:
            sql += " AND device_id = ?"
            args.append(device_id)
        if since_ms is not None:
            sql += " AND (resolved_ms IS NULL OR resolved_ms >= ?)"
            args.append(since_ms)
        sql += " ORDER BY opened_ms DESC, id DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args)]

    # ----------------------------------------------------------------- settings
    def get_setting(self, key, default=None):
        with self._lock:
            row = self._conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set_setting(self, key, value):
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES (?,?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, json.dumps(value)))
            self._conn.commit()
