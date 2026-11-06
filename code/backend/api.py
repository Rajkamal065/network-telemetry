"""REST API + dashboard hosting (FastAPI).

Interactive documentation is generated automatically at /docs.
"""
import csv
import io
import math
from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse

from backend.alerts import validate_thresholds
from telemetry import config
from telemetry.util import now_ms, parse_time

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_POINTS_DEFAULT = 600
RAW_INTERVAL_S = 2.0  # at or below this bucket size we just return raw samples

POINT_FIELDS = ("ts_ms", "rx_bps", "tx_bps", "capacity_bps", "util_pct", "latency_ms", "loss_pct")
EXPORT_FIELDS = ("device_id", "device_type", "interface", "ts_ms", "iso_time", "rx_bps", "tx_bps",
                 "capacity_bps", "util_pct", "latency_ms", "loss_pct")


def _time_range(start, end, minutes):
    try:
        end_ms = parse_time(end, now_ms())
        start_ms = parse_time(start, None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if start_ms is None:
        start_ms = end_ms - int(minutes * 60 * 1000)
    if start_ms > end_ms:
        raise HTTPException(status_code=400, detail="start must be before end")
    return start_ms, end_ms


def _round(row, digits=3):
    return {k: (round(v, digits) if isinstance(v, float) else v) for k, v in row.items()}


def _iso(ms):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _esc(label):
    return str(label).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def create_app(db, ingestor, alerts) -> FastAPI:
    app = FastAPI(
        title="Network Telemetry Framework API",
        description="Query live and historical bandwidth / latency metrics, alerts and thresholds.",
        version="1.0.0",
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    # ---------------------------------------------------------------- helpers
    def device_status(last_seen_ms):
        return "online" if (now_ms() - last_seen_ms) <= config.OFFLINE_AFTER_S * 1000 else "offline"

    def active_alert_map():
        result = {}
        for a in db.query_alerts(state="active", limit=1000):
            entry = result.setdefault(a["device_id"], {"count": 0, "worst": None})
            entry["count"] += 1
            if a["severity"] == "critical" or entry["worst"] is None:
                entry["worst"] = a["severity"]
        return result

    def build_devices():
        latest = db.latest_per_device()
        amap = active_alert_map()
        out = []
        now = now_ms()
        for d in db.list_devices():
            lm = latest.get(d["device_id"])
            a = amap.get(d["device_id"], {"count": 0, "worst": None})
            out.append({
                "device_id": d["device_id"],
                "device_type": d["device_type"],
                "status": device_status(d["last_seen_ms"]),
                "first_seen_ms": d["first_seen_ms"],
                "last_seen_ms": d["last_seen_ms"],
                "seconds_since_last_data": round((now - d["last_seen_ms"]) / 1000, 1),
                "active_alerts": a["count"],
                "worst_severity": a["worst"],
                "latest": _round({k: lm[k] for k in POINT_FIELDS}) if lm else None,
            })
        return out

    # -------------------------------------------------------------- dashboard
    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(STATIC_DIR / "dashboard.html")

    # ----------------------------------------------------------------- health
    @app.get("/api/health", tags=["system"], summary="Service health and ingestion counters")
    def health():
        return {
            "status": "ok",
            "time_ms": now_ms(),
            "stored_metrics": db.count_metrics(),
            "ingest": ingestor.snapshot(),
        }

    # ---------------------------------------------------------------- devices
    @app.get("/api/devices", tags=["devices"], summary="All known devices with status and latest values")
    def devices():
        return {"devices": build_devices()}

    @app.get("/api/summary", tags=["devices"], summary="Network-wide numbers for the dashboard header")
    def summary():
        devs = build_devices()
        online = [d for d in devs if d["status"] == "online" and d["latest"]]
        lat = [d["latest"]["latency_ms"] for d in online if d["latest"]["latency_ms"] is not None]
        utils = [d["latest"]["util_pct"] for d in online if d["latest"]["util_pct"] is not None]
        active = db.query_alerts(state="active", limit=1000)
        return {
            "devices_total": len(devs),
            "devices_online": len(online),
            "devices_offline": sum(1 for d in devs if d["status"] == "offline"),
            "alerts_active": len(active),
            "alerts_critical": sum(1 for a in active if a["severity"] == "critical"),
            "alerts_warning": sum(1 for a in active if a["severity"] == "warning"),
            "total_rx_bps": round(sum(d["latest"]["rx_bps"] for d in online), 1),
            "total_tx_bps": round(sum(d["latest"]["tx_bps"] for d in online), 1),
            "avg_latency_ms": round(sum(lat) / len(lat), 2) if lat else None,
            "max_utilization_pct": round(max(utils), 2) if utils else None,
        }

    # ---------------------------------------------------------------- metrics
    @app.get("/api/metrics/latest", tags=["metrics"], summary="Most recent sample of every device")
    def metrics_latest():
        return {"metrics": {d["device_id"]: d["latest"] for d in build_devices() if d["latest"]}}

    @app.get("/api/metrics", tags=["metrics"],
             summary="History as time series per device (auto-downsampled for long ranges)")
    def metrics(
        device_id: Optional[str] = Query(None, description="only this device"),
        minutes: float = Query(15, gt=0, le=60 * 24 * 30, description="look back this many minutes (used when start is not given)"),
        start: Optional[str] = Query(None, description="epoch s/ms or ISO-8601"),
        end: Optional[str] = Query(None, description="epoch s/ms or ISO-8601 (default now)"),
        resolution: Optional[float] = Query(None, gt=0, description="bucket size in seconds; omit for automatic"),
        max_points: int = Query(MAX_POINTS_DEFAULT, ge=10, le=5000, description="target maximum points per device"),
    ):
        start_ms, end_ms = _time_range(start, end, minutes)
        range_s = (end_ms - start_ms) / 1000
        bucket = resolution
        if bucket is None:
            auto = math.ceil(range_s / max_points)
            bucket = auto if auto > RAW_INTERVAL_S else None
        if bucket and bucket > RAW_INTERVAL_S:
            rows = db.query_bucketed(start_ms, end_ms, bucket, device_id)
        else:
            bucket = None
            rows = db.query_raw(start_ms, end_ms, device_id)
        series = {}
        for r in rows:
            series.setdefault(r["device_id"], []).append(
                _round({k: r[k] for k in POINT_FIELDS}, 2))
        return {"start_ms": start_ms, "end_ms": end_ms, "resolution_s": bucket, "series": series}

    @app.get("/api/metrics/export", tags=["metrics"],
             summary="Download raw history as CSV or JSON (for reports and other tools)")
    def export(
        format: str = Query("csv", pattern="^(csv|json)$"),
        device_id: Optional[str] = None,
        minutes: float = Query(60, gt=0, le=60 * 24 * 30),
        start: Optional[str] = None,
        end: Optional[str] = None,
    ):
        start_ms, end_ms = _time_range(start, end, minutes)

        def rows():
            for r in db.iter_export(start_ms, end_ms, device_id):
                r.pop("id", None)
                r["iso_time"] = _iso(r["ts_ms"])
                yield r

        if format == "json":
            def gen_json():
                yield "["
                first = True
                for r in rows():
                    yield ("" if first else ",") + JSONResponse(content=_round(r, 4)).body.decode()
                    first = False
                yield "]"
            return StreamingResponse(gen_json(), media_type="application/json",
                                     headers={"Content-Disposition": 'attachment; filename="telemetry.json"'})

        def gen_csv():
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
            writer.writeheader()
            yield buf.getvalue()
            for r in rows():
                buf.seek(0)
                buf.truncate()
                writer.writerow(_round(r, 4))
                yield buf.getvalue()

        return StreamingResponse(gen_csv(), media_type="text/csv",
                                 headers={"Content-Disposition": 'attachment; filename="telemetry.csv"'})

    # ----------------------------------------------------------------- alerts
    @app.get("/api/alerts", tags=["alerts"], summary="Alert history (active and resolved)")
    def get_alerts(
        state: str = Query("all", pattern="^(all|active|resolved)$"),
        device_id: Optional[str] = None,
        minutes: Optional[float] = Query(None, gt=0, description="only alerts active within the last N minutes"),
        limit: int = Query(100, ge=1, le=1000),
    ):
        since = now_ms() - int(minutes * 60000) if minutes else None
        rows = db.query_alerts(state, device_id, since, limit)
        now = now_ms()
        for a in rows:
            end = a["resolved_ms"] or now
            a["state"] = "resolved" if a["resolved_ms"] else "active"
            a["duration_s"] = round(max(0, end - a["opened_ms"]) / 1000, 1)
        return {"alerts": [_round(a, 2) for a in rows]}

    @app.get("/api/thresholds", tags=["alerts"], summary="Current alert thresholds")
    def get_thresholds():
        return {"thresholds": alerts.get_thresholds(),
                "breaches_to_open": config.BREACHES_TO_OPEN, "oks_to_close": config.OKS_TO_CLOSE,
                "offline_after_s": config.OFFLINE_AFTER_S}

    @app.put("/api/thresholds", tags=["alerts"], summary="Change alert thresholds at runtime")
    def put_thresholds(body: dict = Body(..., examples=[{"latency_ms": {"warning": 60, "critical": 120}}])):
        try:
            validate_thresholds(body)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return {"thresholds": alerts.set_thresholds(body)}

    # ------------------------------------------------- Prometheus / Grafana
    @app.get("/metrics", tags=["system"], response_class=PlainTextResponse,
             summary="Prometheus text format (lets Grafana read the data through Prometheus)")
    def prometheus():
        lines = []

        def gauge(name, help_text, samples, kind="gauge"):
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {kind}")
            for labels, value in samples:
                lab = ",".join(f'{k}="{_esc(v)}"' for k, v in labels.items())
                lines.append(f"{name}{{{lab}}} {value}" if lab else f"{name} {value}")

        devs = build_devices()
        live = [d for d in devs if d["latest"]]

        def per_device(field):
            return [({"device": d["device_id"], "type": d["device_type"]}, d["latest"][field])
                    for d in live if d["latest"][field] is not None]

        gauge("telemetry_rx_bps", "Received bits per second", per_device("rx_bps"))
        gauge("telemetry_tx_bps", "Transmitted bits per second", per_device("tx_bps"))
        gauge("telemetry_utilization_percent", "Link utilization in percent", per_device("util_pct"))
        gauge("telemetry_latency_ms", "Round-trip latency in milliseconds", per_device("latency_ms"))
        gauge("telemetry_packet_loss_percent", "Packet loss in percent", per_device("loss_pct"))
        gauge("telemetry_device_up", "1 if the device sent data recently, else 0",
              [({"device": d["device_id"], "type": d["device_type"]}, 1 if d["status"] == "online" else 0)
               for d in devs])
        active = db.query_alerts(state="active", limit=1000)
        gauge("telemetry_alerts_active", "Number of active alerts",
              [({"severity": s}, sum(1 for a in active if a["severity"] == s))
               for s in ("warning", "critical")])
        ing = ingestor.snapshot()
        gauge("telemetry_ingest_received_total", "Metrics received by the backend", [({}, ing["received"])], "counter")
        gauge("telemetry_ingest_dropped_total", "Metrics dropped because the queue was full", [({}, ing["dropped"])], "counter")
        return "\n".join(lines) + "\n"

    return app
