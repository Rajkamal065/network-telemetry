"""Unit tests: validation, database, alert engine, time parsing."""
import pytest

from backend.alerts import AlertEngine, validate_thresholds
from backend.db import Database
from backend.ingest import validate
from telemetry import config
from telemetry.protoloader import pb2
from telemetry.util import now_ms, parse_time


def metric(device="r1", rx=10e6, tx=5e6, cap=100e6, lat=10.0, loss=0.0, ts=None):
    return pb2.Metric(device_id=device, device_type="router", interface="eth0",
                      timestamp_ms=ts or now_ms(), rx_bps=rx, tx_bps=tx,
                      capacity_bps=cap, latency_ms=lat, packet_loss_pct=loss)


# ------------------------------------------------------------------ validation
def test_validate_computes_utilization():
    c = validate(metric(rx=50e6, tx=10e6, cap=100e6))
    assert c["util_pct"] == pytest.approx(50.0)


def test_validate_rejects_bad_input():
    assert validate(metric(device="")) is None
    assert validate(metric(rx=-1)) is None
    assert validate(metric(rx=float("nan"))) is None


def test_validate_handles_missing_values():
    c = validate(metric(cap=0, lat=-1, loss=-1))
    assert c["util_pct"] is None and c["latency_ms"] is None and c["loss_pct"] is None


def test_validate_fixes_wild_timestamp():
    c = validate(metric(ts=1000))   # 1970
    assert abs(c["ts_ms"] - now_ms()) < 5000


def test_validate_trims_device_name():
    c = validate(metric(device="  r1\n  "))
    assert c["device_id"] == "r1"


# -------------------------------------------------------------------- database
def make_db_with_rows(n=10, device="r1", start=1_000_000, step=2000):
    db = Database(":memory:")
    rows = []
    for i in range(n):
        m = validate(metric(device=device, ts=start + i * step), received_ms=start + i * step)
        rows.append(m)
    db.insert_metrics(rows)
    return db, rows


def test_db_insert_and_latest():
    db, rows = make_db_with_rows()
    latest = db.latest_per_device()
    assert latest["r1"]["ts_ms"] == rows[-1]["ts_ms"]
    assert db.count_metrics() == 10
    assert db.list_devices()[0]["device_id"] == "r1"


def test_db_bucketing_averages():
    db, _ = make_db_with_rows(n=10, start=1_000_000, step=1000)
    rows = db.query_bucketed(1_000_000, 1_010_000, bucket_s=5)
    assert 2 <= len(rows) <= 3
    assert all(r["util_pct"] == pytest.approx(10.0) for r in rows)


def test_db_export_pages_through_everything():
    db, _ = make_db_with_rows(n=25)
    got = list(db.iter_export(0, 10**13, chunk=7))
    assert len(got) == 25


def test_db_prune():
    db, _ = make_db_with_rows(n=10, start=1000, step=1000)
    removed = db.prune(5500)
    assert removed == 5 and db.count_metrics() == 5


# ---------------------------------------------------------------------- alerts
@pytest.fixture
def engine():
    return AlertEngine(Database(":memory:"))


def feed(engine, values, device="r1", key="util_pct", start=1_000_000):
    t = start
    for v in values:
        engine.evaluate({"device_id": device, "ts_ms": t, "util_pct": None, "latency_ms": None,
                         "loss_pct": None, **{key: v}}, received_ms=t)
        t += 1000
    return t


def test_alert_needs_consecutive_breaches(engine):
    feed(engine, [95])                       # one spike only
    assert engine.db.query_alerts("active") == []
    feed(engine, [95, 95])
    active = engine.db.query_alerts("active")
    assert len(active) == 1 and active[0]["severity"] == "critical"


def test_alert_escalates_and_resolves(engine):
    feed(engine, [75, 75])                   # warning
    assert engine.db.query_alerts("active")[0]["severity"] == "warning"
    feed(engine, [95])                       # escalate
    a = engine.db.query_alerts("active")[0]
    assert a["severity"] == "critical" and a["peak_value"] == 95
    feed(engine, [10] * config.OKS_TO_CLOSE)  # back to normal
    assert engine.db.query_alerts("active") == []
    assert len(engine.db.query_alerts("resolved")) == 1


def test_no_alert_for_normal_values(engine):
    feed(engine, [10, 20, 30, 40, 50] * 3)
    assert engine.db.query_alerts() == []


def test_latency_alert(engine):
    feed(engine, [200, 200], key="latency_ms")
    a = engine.db.query_alerts("active")[0]
    assert a["metric"] == "latency_ms" and a["severity"] == "critical"


def test_alert_is_per_device(engine):
    feed(engine, [95, 95], device="a")
    feed(engine, [10, 10], device="b")
    devices = {a["device_id"] for a in engine.db.query_alerts("active")}
    assert devices == {"a"}


def test_offline_alert_and_recovery(engine):
    t = feed(engine, [10], device="r1", start=now_ms())
    engine.check_offline(now_ms() + int(config.OFFLINE_AFTER_S * 1000) + 5000)
    active = engine.db.query_alerts("active")
    assert len(active) == 1 and active[0]["metric"] == "device_offline"
    engine.evaluate({"device_id": "r1", "ts_ms": now_ms(), "util_pct": 10, "latency_ms": None, "loss_pct": None})
    assert engine.db.query_alerts("active") == []


def test_threshold_validation():
    with pytest.raises(ValueError):
        validate_thresholds({"latency_ms": {"warning": 200, "critical": 100}})
    with pytest.raises(ValueError):
        validate_thresholds({"nonsense": {"warning": 1, "critical": 2}})
    with pytest.raises(ValueError):
        validate_thresholds({"latency_ms": {"warning": "a", "critical": 2}})
    ok = validate_thresholds({"latency_ms": {"warning": 50, "critical": 100}})
    assert ok["latency_ms"]["critical"] == 100.0


def test_thresholds_persist_across_restart(tmp_path):
    path = str(tmp_path / "t.db")
    e1 = AlertEngine(Database(path))
    e1.set_thresholds({"latency_ms": {"warning": 40, "critical": 90}})
    e2 = AlertEngine(Database(path))
    assert e2.get_thresholds()["latency_ms"]["warning"] == 40


# ------------------------------------------------------------------- time util
def test_parse_time_variants():
    assert parse_time("1700000000") == 1700000000000
    assert parse_time("1700000000000") == 1700000000000
    assert parse_time("2023-11-14T22:13:20Z") == 1700000000000
    assert parse_time(None, 5) == 5
    with pytest.raises(ValueError):
        parse_time("yesterday-ish")


def test_db_export_survives_callers_modifying_rows():
    """Regression: the API removes the 'id' key from each row while streaming."""
    db, _ = make_db_with_rows(n=25)
    got = []
    for r in db.iter_export(0, 10**13, chunk=7):
        r.pop("id")
        got.append(r)
    assert len(got) == 25
