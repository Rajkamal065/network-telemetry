"""
Ingestion pipeline: gRPC handlers -> validate -> queue -> writer thread -> SQLite + alerts.

The queue decouples receiving from storing: gRPC threads never wait for the disk,
and the writer saves many metrics in one transaction (much faster than one by one).
If devices ever send faster than we can store, the queue fills up and new metrics
are dropped and counted (visible in /api/health) instead of slowing the network.
"""
import math
import queue
import threading
import time

from telemetry import config
from telemetry.util import now_ms

MAX_ID_LEN = 64
MAX_CLOCK_SKEW_MS = 5 * 60 * 1000


def _clean_text(text, default, limit=MAX_ID_LEN):
    text = (text or "").strip()
    text = "".join(ch for ch in text if ch.isprintable())
    return (text or default)[:limit]


def validate(m, received_ms=None):
    """Convert a protobuf Metric (or any object with the same attributes) into a
    clean dict. Returns None if the metric is unusable."""
    received_ms = received_ms or now_ms()
    device_id = _clean_text(m.device_id, "")
    if not device_id:
        return None
    for value in (m.rx_bps, m.tx_bps):
        if not math.isfinite(value) or value < 0:
            return None
    cap = m.capacity_bps if math.isfinite(m.capacity_bps) and m.capacity_bps > 0 else None
    util = None
    if cap:
        util = max(m.rx_bps, m.tx_bps) / cap * 100.0
        util = min(util, 1000.0)
    latency = m.latency_ms if math.isfinite(m.latency_ms) and m.latency_ms >= 0 else None
    loss = m.packet_loss_pct if math.isfinite(m.packet_loss_pct) and m.packet_loss_pct >= 0 else None
    if loss is not None:
        loss = min(loss, 100.0)
    ts = m.timestamp_ms
    if ts <= 0 or abs(ts - received_ms) > MAX_CLOCK_SKEW_MS:
        ts = received_ms  # agent clock missing or far off: trust the server clock
    return {
        "device_id": device_id,
        "device_type": _clean_text(m.device_type, "unknown", 32),
        "interface": _clean_text(m.interface, "", 32),
        "ts_ms": int(ts),
        "rx_bps": float(m.rx_bps),
        "tx_bps": float(m.tx_bps),
        "capacity_bps": cap,
        "util_pct": util,
        "latency_ms": latency,
        "loss_pct": loss,
    }


class Ingestor:
    def __init__(self, db, alerts, queue_size=20000, batch_size=500, flush_s=0.5):
        self.db = db
        self.alerts = alerts
        self.queue = queue.Queue(maxsize=queue_size)
        self.batch_size = batch_size
        self.flush_s = flush_s
        self.stats = {"received": 0, "rejected": 0, "dropped": 0, "stored": 0, "last_error": None}
        self._stats_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="ingest-writer", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)

    def _bump(self, key, n=1):
        with self._stats_lock:
            self.stats[key] += n

    def submit(self, pb_metric):
        """Called by gRPC handlers. Returns True if accepted."""
        received = now_ms()
        self._bump("received")
        clean = validate(pb_metric, received)
        if clean is None:
            self._bump("rejected")
            return False
        try:
            self.queue.put_nowait((clean, received))
        except queue.Full:
            self._bump("dropped")
            return False
        return True

    def snapshot(self):
        with self._stats_lock:
            data = dict(self.stats)
        data["queue_size"] = self.queue.qsize()
        return data

    def flush(self, timeout=5.0):
        """Block until everything queued so far is stored (used by tests)."""
        end = time.time() + timeout
        while time.time() < end:
            if self.queue.empty() and not getattr(self, "_busy", False):
                return True
            time.sleep(0.02)
        return False

    def _run(self):
        while not self._stop.is_set() or not self.queue.empty():
            batch = []
            try:
                batch.append(self.queue.get(timeout=self.flush_s))
            except queue.Empty:
                continue
            self._busy = True
            while len(batch) < self.batch_size:
                try:
                    batch.append(self.queue.get_nowait())
                except queue.Empty:
                    break
            try:
                self.db.insert_metrics([c for c, _ in batch])
                self._bump("stored", len(batch))
                for clean, received in batch:
                    self.alerts.evaluate(clean, received)
            except Exception as exc:  # never let the writer thread die
                with self._stats_lock:
                    self.stats["last_error"] = repr(exc)
            finally:
                self._busy = False
