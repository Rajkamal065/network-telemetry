# Design notes

## 1. Problem

Collect bandwidth and latency of network devices in real time, move the data to
one place, store it, show it live, alert on problems, and let other tools read
history through an API - in a way that can grow to more devices and metrics.

## 2. Architecture and data flow

1. **Collector** (inside every agent) produces one `Metric` per interval:
   device id and type, timestamp, download and upload bits per second, link
   capacity, latency, packet loss.
2. **Agent** puts the reading into a local queue and streams it over one
   long-lived **gRPC client-streaming call** (`Telemetry.Stream`) to the backend.
   The message format is defined in `proto/telemetry.proto`. If the backend is
   down the agent keeps measuring (up to 1000 readings buffered) and reconnects
   with exponential back-off (1 s, 2 s, 4 s ... max 10 s).
3. **Backend gRPC server** validates each metric (`backend/ingest.py: validate`):
   rejects empty device ids and negative/NaN numbers, replaces missing or wildly
   wrong timestamps with server time, computes utilization.
4. **Ingest queue + writer thread** store metrics in SQLite in batches and run the
   alert engine. Receiving never waits for the disk. If the queue is full, new
   metrics are dropped and counted (`/api/health`) instead of slowing anything down.
5. **Alert engine** (`backend/alerts.py`) keeps a small state machine per
   (device, metric) with hysteresis (2 breaches to open, 3 healthy samples to close).
6. **REST API** (FastAPI) serves live values, history (auto-downsampled), CSV/JSON
   export, alerts, thresholds, and `/metrics` in Prometheus format.
7. **Dashboard** (`backend/static/dashboard.html`) is a single page with no external
   libraries (charts are drawn on a canvas), so it works offline. It polls the API every 2 s.
8. **Grafana (optional)** reads the Prometheus endpoint through Prometheus.

## 3. Mapping to RFC 9232 (Network Telemetry Framework)

RFC 9232 describes network telemetry as the whole process of generating,
exporting, collecting and consuming network data, and structures it into four
top-level modules by data source: management plane, control plane, forwarding
plane and external data telemetry. Each module has components for the data
source, configuration/subscription, data generation, and encoding/export.

| RFC 9232 idea | In this project |
|---|---|
| Management plane telemetry (device-level counters such as interface statistics; SNMP and gNMI/gRPC are examples of its protocols) | Interface byte counters -> bandwidth; the laptop collector reads real OS counters; simulated devices generate equivalent values |
| Data generation / processing at the device | Collector computes rates (bits per second) from counters, measures latency |
| Data encoding and export (push model) | Protobuf encoding, pushed through a gRPC stream |
| Data collection | gRPC server + ingest pipeline in the backend |
| Storage, analysis, consumption by applications | SQLite, alert engine, dashboard, REST API, Prometheus/Grafana |
| Control plane / forwarding plane / external data telemetry | Not implemented (listed as future work) |

Before using this table in the report, read Section 3 of the RFC yourself and
use its exact terminology; this table is a summary, not a quotation.

## 4. Why these choices

* **gRPC streaming + protobuf**: efficient, typed contract, one connection per device
  instead of one request per reading, and it is the same style of push used by gNMI.
* **SQLite**: zero setup, one file, fast enough for this scale. All SQL is in
  `backend/db.py`, so replacing it is a one-file change.
* **Batching writer**: one transaction per batch instead of per reading.
* **Own dashboard + optional Grafana**: the dashboard always works (no Docker);
  Grafana is available for the "or other tools" in the brief.
* **Simulated devices**: no hardware is available; the simulator models traffic
  waves, queueing delay that grows with load, loss under congestion, random
  spikes, and scripted incidents for demonstrations.
* **Push, not poll**: agents push measurements, so the backend does not need to
  know device addresses in advance and new devices appear automatically.

## 5. Data model

`metrics(device_id, device_type, interface, ts_ms, rx_bps, tx_bps, capacity_bps, util_pct, latency_ms, loss_pct)`
indexed on `(device_id, ts_ms)`; `devices` (first/last seen); `alerts` (open/resolved
with severity, value, peak, threshold, message, times); `settings` (thresholds).
Missing values (for example latency when the internet is down) are stored as NULL
and shown as gaps in the charts.

## 6. Extending the system

**New device**: start another agent with a new id. No backend change.

**New metric** (for example CPU load):
1. add a field to `Metric` in `proto/telemetry.proto` (delete the `gen/` folder or just run again; it regenerates)
2. fill it in the collector(s)
3. add a column in `backend/db.py` (`SCHEMA` and `METRIC_COLUMNS`) and carry it through `validate()` in `backend/ingest.py`
4. optionally add a threshold in `telemetry/config.py` and a line in `AlertEngine.evaluate`, and a chart in the dashboard

**New protocol (real devices)**: write a class that extends `Collector` (see
`agents/laptop.py`), whose `collect()` reads the device (for example SNMP
`ifHCInOctets` / `ifHCOutOctets` twice and divide by the time between reads, or a
gNMI subscription) and returns a `Metric`. The agent, transport, storage and
dashboard stay the same. SNMP and OpenTelemetry are named in the project brief as
options; they are not implemented here.

## 7. Limitations and honest notes

* Real routers and switches were not available; apart from the laptop, data is simulated.
* The laptop latency is a TCP connect time to a public DNS server, not an ICMP ping
  to the device; it measures the path to the internet.
* No TLS or authentication on gRPC and REST; do not expose the ports to the internet.
* Alert thresholds are global (same for all devices), not per device.
* The dashboard page was syntax-checked and run against the live API with a simulated
  browser environment, but chart appearance should be checked by eye in a browser.
* Grafana/Prometheus files are provided but need Docker to run.
