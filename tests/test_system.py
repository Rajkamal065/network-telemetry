"""Integration tests: real gRPC server + REST API in one process, agents talking to it."""
import time

import grpc
import pytest
from fastapi.testclient import TestClient

from agents.base import Agent
from agents.simulated import SimulatedDevice
from backend.main import Backend
from telemetry.protoloader import pb2, pb2_grpc
from telemetry.util import now_ms


@pytest.fixture
def backend(tmp_path):
    b = Backend(str(tmp_path / "t.db"), "127.0.0.1", 0)   # port 0 = pick a free port
    b.start()
    yield b
    b.stop()


@pytest.fixture
def client(backend):
    return TestClient(backend.app)


def publish(backend, metrics):
    with grpc.insecure_channel(f"127.0.0.1:{backend.grpc_port}") as ch:
        stub = pb2_grpc.TelemetryStub(ch)
        ack = stub.Publish(pb2.MetricBatch(metrics=metrics))
    assert backend.ingestor.flush()
    return ack


def m(device="r1", **kw):
    base = dict(device_id=device, device_type="router", interface="eth0", timestamp_ms=now_ms(),
                rx_bps=20e6, tx_bps=10e6, capacity_bps=100e6, latency_ms=12.0, packet_loss_pct=0.0)
    base.update(kw)
    return pb2.Metric(**base)


def test_publish_and_query(backend, client):
    ack = publish(backend, [m("r1"), m("r2", latency_ms=30), m("")])
    assert ack.accepted == 2 and ack.rejected == 1
    devices = client.get("/api/devices").json()["devices"]
    assert {d["device_id"] for d in devices} == {"r1", "r2"}
    assert all(d["status"] == "online" for d in devices)
    latest = client.get("/api/metrics/latest").json()["metrics"]
    assert latest["r2"]["latency_ms"] == pytest.approx(30)
    assert latest["r1"]["util_pct"] == pytest.approx(20.0)


def test_history_and_export(backend, client):
    now = now_ms()
    publish(backend, [m("r1", timestamp_ms=now - 4000), m("r1", timestamp_ms=now - 2000), m("r1", timestamp_ms=now)])
    series = client.get("/api/metrics?minutes=5&device_id=r1").json()["series"]
    assert len(series["r1"]) == 3
    csv_text = client.get("/api/metrics/export?minutes=5").text
    lines = [l for l in csv_text.strip().splitlines() if l]
    assert lines[0].startswith("device_id,") and len(lines) == 4
    js = client.get("/api/metrics/export?format=json&minutes=5").json()
    assert len(js) == 3 and js[0]["device_id"] == "r1"


def test_long_range_is_downsampled(backend, client):
    now = now_ms()
    publish(backend, [m("r1", timestamp_ms=now - i * 1000) for i in range(300)])
    data = client.get("/api/metrics?minutes=1440&max_points=50").json()
    assert data["resolution_s"] and data["resolution_s"] > 2
    assert len(data["series"]["r1"]) < 50


def test_bad_requests(client):
    assert client.get("/api/metrics?start=banana").status_code == 400
    assert client.get("/api/metrics?minutes=-1").status_code == 422
    assert client.get("/api/metrics/export?format=xml").status_code == 422
    r = client.put("/api/thresholds", json={"latency_ms": {"warning": 9, "critical": 3}})
    assert r.status_code == 422


def test_alert_flow_through_api(backend, client):
    publish(backend, [m("r1", rx_bps=95e6), m("r1", rx_bps=96e6)])
    alerts = client.get("/api/alerts?state=active").json()["alerts"]
    assert len(alerts) == 1 and alerts[0]["metric"] == "utilization_pct"
    assert client.get("/api/summary").json()["alerts_critical"] == 1
    # change thresholds at runtime and check they are served back
    r = client.put("/api/thresholds", json={"utilization_pct": {"warning": 50, "critical": 99}})
    assert r.status_code == 200
    assert client.get("/api/thresholds").json()["thresholds"]["utilization_pct"]["critical"] == 99


def test_prometheus_endpoint_is_valid(backend, client):
    prom = pytest.importorskip("prometheus_client.parser")
    publish(backend, [m("r1"), m('weird "name"')])
    text = client.get("/metrics").text
    families = {f.name: f for f in prom.text_string_to_metric_families(text)}
    assert "telemetry_utilization_percent" in families
    assert len(families["telemetry_device_up"].samples) == 2


def test_dashboard_is_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Network Telemetry Dashboard" in r.text


def test_agent_streams_to_backend_over_grpc(backend, client):
    dev = SimulatedDevice("sim-test", capacity_mbps=100)
    agent = Agent(dev, f"127.0.0.1:{backend.grpc_port}", interval=0.2, quiet=True).start()
    try:
        deadline = time.time() + 8
        while time.time() < deadline and backend.db.count_metrics() < 5:
            time.sleep(0.2)
    finally:
        agent.stop()
    assert backend.db.count_metrics() >= 5
    assert any(d["device_id"] == "sim-test" for d in client.get("/api/devices").json()["devices"])


def test_agent_survives_backend_restart(tmp_path):
    """The agent must reconnect by itself when the backend comes back."""
    b1 = Backend(str(tmp_path / "t.db"), "127.0.0.1", 0)
    b1.start()
    port = b1.grpc_port
    agent = Agent(SimulatedDevice("sim-resilient"), f"127.0.0.1:{port}", interval=0.2, quiet=True).start()
    try:
        deadline = time.time() + 6
        while time.time() < deadline and b1.db.count_metrics() < 3:
            time.sleep(0.2)
        assert b1.db.count_metrics() >= 3
        b1.stop()
        time.sleep(1.5)                                   # backend is down now
        b2 = Backend(str(tmp_path / "t2.db"), "127.0.0.1", port)
        b2.start()
        try:
            deadline = time.time() + 20
            while time.time() < deadline and b2.db.count_metrics() < 3:
                time.sleep(0.3)
            assert b2.db.count_metrics() >= 3, "agent did not reconnect"
        finally:
            b2.stop()
    finally:
        agent.stop()


def test_device_goes_offline(backend, client, monkeypatch):
    from telemetry import config
    monkeypatch.setattr(config, "OFFLINE_AFTER_S", 1.0)
    publish(backend, [m("r1")])
    time.sleep(2.5)                                       # monitor thread checks every second
    dev = client.get("/api/devices").json()["devices"][0]
    assert dev["status"] == "offline"
    active = client.get("/api/alerts?state=active").json()["alerts"]
    assert any(a["metric"] == "device_offline" for a in active)


def test_queue_overflow_is_counted_not_fatal(backend):
    backend.ingestor.queue.maxsize = 1
    backend.ingestor._stop.set()           # stop the writer so the queue stays full
    backend.ingestor._thread.join(timeout=3)
    results = [backend.ingestor.submit(m("r1")) for _ in range(5)]
    assert results.count(False) >= 3
    assert backend.ingestor.snapshot()["dropped"] >= 3
