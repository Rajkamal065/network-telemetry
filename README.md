# Network Telemetry Framework

A small but complete telemetry system for network devices. Agents measure
bandwidth and latency of routers and switches every 2 seconds, stream the
readings over **gRPC** to a central backend, which stores them in a database,
raises **threshold alerts**, serves a **live web dashboard** and a **REST API**
for history and export. An optional **Grafana** dashboard is included.

Reference: RFC 9232, *Network Telemetry Framework* (see docs/DESIGN.md for how
this project maps to it).

```
 +--------------------+        gRPC stream         +-------------------------------------------+
 | Agent: core-router |  ------------------------> |  BACKEND (one Python program)             |
 | Agent: edge-switch |   (protobuf messages,      |                                           |
 | Agent: ...         |    one long connection)    |  gRPC server -> validate -> queue         |
 | Agent: this laptop |                            |        -> writer thread -> SQLite         |
 +--------------------+                            |                    \-> alert engine       |
   simulated devices +                             |                                           |
   one real device                                 |  REST API (FastAPI)  <-- dashboard (web)  |
                                                   |  /api/...   /metrics (Prometheus)         |
                                                   +-------------------------------------------+
                                                                         |
                                                       optional: Prometheus -> Grafana
```

## 1. Quick start

You need **Python 3.10 or newer** and internet once (to install libraries).

```
cd network-telemetry

# create an isolated environment (recommended)
python -m venv .venv
# Windows:            .venv\Scripts\activate
# Linux / macOS:      source .venv/bin/activate

pip install -r requirements.txt

python run_demo.py
```

`run_demo.py` starts the backend and the agents and opens the dashboard at
**http://localhost:8000**. Press Ctrl+C in the terminal to stop everything.

Useful options: `--no-laptop` (skip your real computer), `--no-incidents`
(calm network), `--fresh` (delete old data), `--devices 20` (more devices).

If `python` does not work on your machine, try `python3` or `py`.

## 2. What you will see (demo script)

1. **Dashboard** - 5 simulated devices (2 routers, 2 switches, 1 branch router) and
   your laptop. Cards on top, device table, four live charts, alert list.
2. **Scripted incidents** (they repeat every 150 s, so you can wait for them):
   * ~20 s after start: congestion on `edge-switch-1` -> utilization, latency and loss alerts
   * ~60 s: latency spike on `core-router-1`
   * ~100 s: packet loss on `branch-router`
   Alerts appear in the alert list and device table, and disappear (resolved)
   after the problem ends.
3. **Real device** - the `laptop-<yourname>` line is real: open a video or download
   a file and watch its throughput move.
4. **Change a threshold** at the bottom of the dashboard (e.g. latency warning
   at 20 ms) and watch new alerts appear - no restart needed.
5. **REST API** at http://localhost:8000/docs - try `GET /api/metrics`, and download
   history with the *Export CSV* link.
6. **Scalability**: in a second terminal run `python run_agents.py --devices 30 --no-laptop`
   - 30 more agents join without any change to the backend.
7. **Resilience**: stop the backend (Ctrl+C on only that process if you run the
   parts separately), start it again - agents reconnect by themselves.

## 3. Running the parts separately (3 terminals)

```
python run_backend.py                 # terminal 1: receiver + API + dashboard
python run_agents.py                  # terminal 2: 5 simulated devices + laptop
python run_agents.py --only core-router-1 --no-laptop     # a single device on its own
```

Agents can run on other computers too: point them at the backend with
`python run_agents.py --target <backend-ip>:50051`.

## 4. REST API

Interactive documentation with a "Try it out" button: **http://localhost:8000/docs**

| Endpoint | What it gives |
|---|---|
| `GET /api/health` | service status and ingestion counters (received / stored / dropped) |
| `GET /api/devices` | every device: status (online/offline), last data, latest values, active alerts |
| `GET /api/summary` | network-wide numbers (devices online, alerts, total traffic, average latency) |
| `GET /api/metrics/latest` | newest sample of each device |
| `GET /api/metrics?minutes=60&device_id=...` | history as one time series per device; long ranges are averaged into buckets automatically (`resolution`, `max_points`, `start`, `end` also available) |
| `GET /api/metrics/export?format=csv&minutes=120` | download raw history as CSV or JSON for reports |
| `GET /api/alerts?state=active` | alerts (`active`, `resolved`, `all`), with duration and peak value |
| `GET /api/thresholds` / `PUT /api/thresholds` | read or change alert thresholds at runtime (saved in the database) |
| `GET /metrics` | the same data in Prometheus format (for Grafana) |

Time values accept epoch seconds, epoch milliseconds or ISO-8601 (`2026-11-05T10:30:00Z`).

Example:

```
curl "http://localhost:8000/api/metrics?minutes=10&device_id=core-router-1"
curl -X PUT http://localhost:8000/api/thresholds -H "Content-Type: application/json" \
     -d '{"latency_ms": {"warning": 50, "critical": 100}}'
```

## 5. Alerts

Default thresholds (change them on the dashboard or with `PUT /api/thresholds`):

| Metric | Warning | Critical |
|---|---|---|
| Bandwidth utilization (% of link capacity) | 70 | 90 |
| Latency (ms) | 80 | 150 |
| Packet loss (%) | 2 | 5 |

* An alert **opens** after 2 breaches in a row and **closes** after 3 healthy samples
  in a row, so one noisy reading does not cause a false alarm.
* Severity can escalate (warning -> critical) while an alert is open; the highest value is kept as `peak_value`.
* A **device_offline** alert (critical) opens when a device that was sending data stays silent for 10 s.
* Utilization = `max(download, upload) / link capacity` (links are full-duplex).

## 6. Optional: Grafana

Needs Docker. Start the Python system first (`python run_demo.py`), then:

```
cd deploy
docker compose up
```

Open http://localhost:3000 (user `admin`, password `admin`). The dashboard
"Network Telemetry" is already provisioned. Flow: backend `/metrics` -> Prometheus
(scrapes every 2 s) -> Grafana. If you do not have Docker, skip this: the built-in
dashboard already covers every requirement.

## 7. Tests

```
pip install -r requirements-dev.txt
python -m pytest tests -q
```

The tests cover validation, database, alert logic, the REST API, a real gRPC
server with real agents, agent reconnection after a backend restart, offline
detection and queue overflow.

## 8. Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `TELEMETRY_API_PORT` | 8000 | dashboard / REST port |
| `TELEMETRY_GRPC_PORT` | 50051 | gRPC port agents send to |
| `TELEMETRY_BACKEND` | 127.0.0.1:50051 | where agents send |
| `TELEMETRY_DB` | telemetry.db | database file |
| `TELEMETRY_INTERVAL` | 2 | seconds between measurements |
| `TELEMETRY_OFFLINE_AFTER` | 10 | seconds of silence before a device is "offline" |
| `TELEMETRY_RETENTION_HOURS` | 48 | older data is deleted automatically |
| `TELEMETRY_GRPC_WORKERS` | 64 | maximum number of agents streaming at once |

## 9. Project layout

```
proto/telemetry.proto      the message format (the contract between agents and backend)
telemetry/                 shared code: config, proto loader (generates gRPC code on first run), helpers
agents/                    base agent (streaming, buffering, reconnect), simulated device, laptop collector
backend/                   gRPC server, ingest queue + writer, SQLite layer, alert engine, REST API, dashboard page
deploy/                    optional Prometheus + Grafana (docker compose)
tests/                     unit and integration tests
docs/DESIGN.md             design, RFC 9232 mapping, how to extend, limitations
run_demo.py                one command to run everything
```

## 10. Troubleshooting

* **"port already in use"** - another program uses 8000 or 50051. Use
  `python run_demo.py --api-port 8080` and/or set `TELEMETRY_GRPC_PORT=50052`
  (agents then need `TELEMETRY_BACKEND=127.0.0.1:50052` too).
* **Latency of the laptop shows "-"** - no internet, so the probe to 1.1.1.1:53 fails. The
  bandwidth numbers still work.
* **Laptop link capacity looks wrong** - capacity is guessed from the network card speed
  (Wi-Fi often reports it differently). Fix it in `agents/laptop.py` (`capacity_mbps`) or
  create `LaptopCollector(capacity_mbps=300)`.
* **Windows firewall popup** - allow Python on private networks; everything is local.
* **Dashboard empty** - agents are not running or cannot reach the backend; check
  the agents terminal for "connected to backend".

## 11. Known limitations

* Devices are **simulated** (plus your laptop); no real SNMP/gNMI polling yet - see
  docs/DESIGN.md for how a real-device collector plugs in.
* gRPC runs without TLS and the REST API has no login. Fine for a lab, not for production.
* One SQLite file on one machine. It is enough for dozens of devices; for large
  networks, swap in a time-series database (the SQL is isolated in `backend/db.py`).
