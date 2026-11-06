"""
Threshold-based alerting.

For every (device, metric) pair we keep a tiny state machine:

    healthy --(N breaches in a row)--> ALERT OPEN (warning or critical)
    ALERT OPEN --(M healthy samples in a row)--> RESOLVED

N and M (config.BREACHES_TO_OPEN / OKS_TO_CLOSE) stop the system from raising
an alert for one single noisy sample ("flapping").

Besides the three performance metrics, a "device_offline" alert is raised when a
device that was sending data goes silent.
"""
import threading

from telemetry import config
from telemetry.util import is_finite_number, now_ms as _now_ms

# metric name -> (human label, unit)
METRIC_LABELS = {
    "utilization_pct": ("Bandwidth utilization", "%"),
    "latency_ms": ("Latency", "ms"),
    "packet_loss_pct": ("Packet loss", "%"),
    "device_offline": ("Device offline", "s"),
}
SEVERITY_RANK = {"warning": 1, "critical": 2}


def validate_thresholds(data):
    """Check and normalise a thresholds dict. Raises ValueError with a clear message."""
    if not isinstance(data, dict):
        raise ValueError("thresholds must be an object")
    clean = {}
    for metric, levels in data.items():
        if metric not in config.DEFAULT_THRESHOLDS:
            raise ValueError(f"unknown metric '{metric}', allowed: {sorted(config.DEFAULT_THRESHOLDS)}")
        if not isinstance(levels, dict):
            raise ValueError(f"{metric}: expected {{'warning': x, 'critical': y}}")
        warn = levels.get("warning", config.DEFAULT_THRESHOLDS[metric]["warning"])
        crit = levels.get("critical", config.DEFAULT_THRESHOLDS[metric]["critical"])
        if not (is_finite_number(warn) and is_finite_number(crit)):
            raise ValueError(f"{metric}: warning and critical must be numbers")
        if warn <= 0 or crit <= 0:
            raise ValueError(f"{metric}: thresholds must be positive")
        if warn >= crit:
            raise ValueError(f"{metric}: warning ({warn}) must be lower than critical ({crit})")
        clean[metric] = {"warning": float(warn), "critical": float(crit)}
    return clean


class AlertEngine:
    def __init__(self, db):
        self.db = db
        self._lock = threading.RLock()
        self._state = {}        # (device, metric) -> dict
        self._last_seen = {}    # device -> ms of last data (only devices seen since start)
        stored = db.get_setting("thresholds", {})
        merged = {m: dict(v) for m, v in config.DEFAULT_THRESHOLDS.items()}
        try:
            for m, v in validate_thresholds(stored).items():
                merged[m] = v
        except ValueError:
            pass
        self.thresholds = merged

    # ------------------------------------------------------------ thresholds
    def get_thresholds(self):
        with self._lock:
            return {m: dict(v) for m, v in self.thresholds.items()}

    def set_thresholds(self, data):
        clean = validate_thresholds(data)
        with self._lock:
            for m, v in clean.items():
                self.thresholds[m] = v
            self.db.set_setting("thresholds", self.thresholds)
            return {m: dict(v) for m, v in self.thresholds.items()}

    # ----------------------------------------------------------- evaluation
    def _classify(self, metric, value):
        t = self.thresholds[metric]
        if value >= t["critical"]:
            return "critical", t["critical"]
        if value >= t["warning"]:
            return "warning", t["warning"]
        return None, None

    def _state_for(self, key):
        return self._state.setdefault(key, {"breaches": 0, "oks": 0, "alert_id": None,
                                            "severity": None, "peak": None})

    def _message(self, metric, severity, value, threshold):
        label, unit = METRIC_LABELS[metric]
        return f"{label} {value:.1f}{unit} reached {severity} level (threshold {threshold:g}{unit})"

    def evaluate(self, m, received_ms=None):
        """m: validated metric dict (see ingest.validate). Call once per sample.
        received_ms is when the backend got it (used for offline detection)."""
        device, ts = m["device_id"], m["ts_ms"]
        with self._lock:
            self._last_seen[device] = received_ms if received_ms is not None else _now_ms()
            # if the device was marked offline, it is back now
            self._resolve_offline(device, ts)
            for metric, key in (("utilization_pct", "util_pct"),
                                ("latency_ms", "latency_ms"),
                                ("packet_loss_pct", "loss_pct")):
                value = m.get(key)
                if value is None:
                    continue
                self._step(device, metric, value, ts)

    def _step(self, device, metric, value, ts):
        st = self._state_for((device, metric))
        severity, threshold = self._classify(metric, value)
        if severity:
            st["oks"] = 0
            st["breaches"] += 1
            if st["alert_id"] is None:
                if st["breaches"] >= config.BREACHES_TO_OPEN:
                    msg = self._message(metric, severity, value, threshold)
                    st["alert_id"] = self.db.open_alert(device, metric, severity, value, threshold, msg, ts)
                    st["severity"], st["peak"] = severity, value
            else:
                changed = {}
                if severity != st["severity"]:
                    st["severity"] = severity
                    changed.update(severity=severity, threshold=threshold,
                                   message=self._message(metric, severity, value, threshold))
                if value > (st["peak"] or 0):
                    st["peak"] = value
                    changed["peak_value"] = value
                if changed:
                    self.db.update_alert(st["alert_id"], **changed)
        else:
            st["breaches"] = 0
            if st["alert_id"] is not None:
                st["oks"] += 1
                if st["oks"] >= config.OKS_TO_CLOSE:
                    self.db.resolve_alert(st["alert_id"], ts)
                    st.update(alert_id=None, severity=None, peak=None, oks=0)

    # -------------------------------------------------------------- offline
    def _resolve_offline(self, device, ts):
        st = self._state.get((device, "device_offline"))
        if st and st["alert_id"] is not None:
            self.db.resolve_alert(st["alert_id"], ts)
            st.update(alert_id=None, severity=None, peak=None)

    def check_offline(self, now_ms):
        """Called every second or two by a background thread."""
        limit_ms = config.OFFLINE_AFTER_S * 1000
        with self._lock:
            for device, seen in list(self._last_seen.items()):
                silent_ms = now_ms - seen
                st = self._state_for((device, "device_offline"))
                if silent_ms > limit_ms and st["alert_id"] is None:
                    msg = f"No data received from {device} for {silent_ms / 1000:.0f}s - device may be down"
                    st["alert_id"] = self.db.open_alert(
                        device, "device_offline", "critical", silent_ms / 1000,
                        config.OFFLINE_AFTER_S, msg, now_ms)
                    st["severity"] = "critical"
