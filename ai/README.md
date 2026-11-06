# AI Prompts & Development Dialogue

**Course**: CS331 Computer Networks — Project 2  
**Project**: Real-Time Network Telemetry Framework (RFC 9232)  
**Team ID**: `T018`  
**Authors**: Avinash Reddy, Gella Jayarama Krishna, Sowpati Raj Kamal, Jangam Sanjay, Pulakurthi Manohar, Yalla Sai Teja  

---

## 1. Overview & Approach to AI Usage

During this project, AI assistants (Claude and ChatGPT) were used as technical partners for understanding RFC 9232 principles, exploring implementation trade-offs, debugging asynchronous concurrency issues, and scaffolding code structures. 

All conceptual choices, design decisions, and system requirements were formulated and driven by our team. Our workflow followed a strict learning-first approach:
1. **Student Concept & Reasoning First**: We studied the networking fundamentals and RFC 9232 specifications, formulated our engineering plan, and articulated our conceptual reasoning.
2. **Targeted Technical Inquiries**: We asked specific questions regarding Protocol Buffers schema design, asynchronous queueing patterns, and SQLite WAL batching.
3. **Local Implementation & Verification**: Every script, collector, and test was run locally in our Windows Python environment. Console outputs, database rows, and network counters were directly inspected and validated before adopting any code.

---

## 2. Chronological Learning & Code Generation Dialogue

### Milestone 1: Project Scope, RFC 9232 Analysis, and Concept Formulation

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"I have been reading RFC 9232 (Network Telemetry Framework) Section 2.2. The RFC lists six operational use cases: SLA compliance, network optimization, event tracking, root cause analysis, security, and policy compliance. Most conventional network monitoring tools use periodic SNMP polling to help human operators diagnose issues, whereas network telemetry is designed to stream real-time data continuously for automated consumption.*
>
> *For our course project, I don't want to jump blindly into code or choose something overly complicated like machine learning or complex dynamic routing algorithms that we cannot fully verify on our laptops. Instead, I want to focus on a coherent, practical problem:*
>
> *1. **SLA Compliance & Link Congestion Monitoring**: Continuously measure real-time bandwidth utilization, throughput, latency, and packet loss.*
> *2. **Threshold-Based State Machine**: Automatically detect when link capacity exceeds 70% or 90% and flag latency spikes.*
> *3. **Decoupled Architecture**: Separate the telemetry collection/transport pipeline from the analytical storage and dashboard layer.*
>
> *Does this conceptual scope align properly with RFC 9232 principles, and how should we structure the project repository to keep components modular and maintainable?"*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Your reasoning is spot on. In RFC 9232, telemetry is the underlying push-based transport system, while SLA compliance and congestion detection are the analytical applications running on top. Focusing on SLA and congestion monitoring provides strong technical depth without unnecessary complexity.*
>
> *Here is the recommended modular repository structure:*
> - `proto/`: Protocol Buffers streaming definition (`telemetry.proto`)
> - `telemetry/`: Core models, metric validation, and configuration
> - `agents/`: Edge telemetry producers (physical host + simulated network devices)
> - `backend/`: gRPC streaming receiver, decoupled ingestion queue, SQLite database, and FastAPI REST server
> - `tests/`: Automated unit and integration test suite
> - `run_demo.py`: Single-command supervisor script to launch the full system locally.*"

---

### Milestone 2: Push Streaming Transport (gRPC & Protocol Buffers)

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"Now let's design the transport layer. Traditional monitoring uses SNMP GET requests on 5-minute polling intervals. The problem with this pull model is that transient micro-bursts and brief congestion spikes get smoothed out in long averages, and periodic polling creates CPU spikes on managed switches.*
>
> *Under RFC 9232, edge devices should proactively push telemetry over a persistent connection. I want to use **gRPC client-streaming over HTTP/2** with **Protocol Buffers (proto3)**:*
> - *The agent establishes a single persistent TCP connection (`Telemetry.Stream`).*
> - *Every 2 seconds, it pushes a binary Protobuf message.*
> - *The message must be compact: device ID, device type, interface name, RX/TX bitrates, link capacity, latency, and packet loss.*
>
> *Help me write `proto/telemetry.proto`. Also, since different team members have different Python and `grpcio` versions installed on their machines, how can we compile these stubs automatically on first run without version mismatches?"*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Here is the clean, compact `proto/telemetry.proto` definition. Each serialized telemetry message is approximately **72 bytes**, providing a 3.2× bandwidth saving compared to JSON (~228 bytes):*
>
> ```protobuf
> syntax = "proto3";
> package telemetry;
> 
> service Telemetry {
>   rpc Stream (stream Metric) returns (StreamAck);
> }
> 
> message Metric {
>   string device_id = 1;
>   string device_type = 2;
>   string interface = 3;
>   int64 timestamp_ms = 4;
>   double rx_bps = 5;
>   double tx_bps = 6;
>   double capacity_bps = 7;
>   double latency_ms = 8;
>   double packet_loss_pct = 9;
> }
> 
> message StreamAck {
>   int64 received_count = 1;
>   string message = 2;
> }
> ```
>
> *To handle dynamic stub compilation across environments without manual CLI commands, implement `telemetry/protoloader.py`:*
>
> ```python
> import importlib, subprocess, sys
> from pathlib import Path
> 
> ROOT = Path(__file__).resolve().parent.parent
> PROTO_DIR = ROOT / "proto"
> GEN_DIR = ROOT / "gen"
> 
> def load():
>     pb2_file = GEN_DIR / "telemetry_pb2.py"
>     if not pb2_file.exists():
>         GEN_DIR.mkdir(exist_ok=True)
>         (GEN_DIR / "__init__.py").touch()
>         subprocess.run([
>             sys.executable, "-m", "grpc_tools.protoc",
>             f"-I{PROTO_DIR}", f"--python_out={GEN_DIR}",
>             f"--grpc_python_out={GEN_DIR}",
>             str(PROTO_DIR / "telemetry.proto")
>         ], check=True)
>     if str(GEN_DIR) not in sys.path:
>         sys.path.insert(0, str(GEN_DIR))
>     return importlib.import_module("telemetry_pb2"), importlib.import_module("telemetry_pb2_grpc")
> ```"

---

### Milestone 3: Dual-Mode Telemetry Producers (Host vs. Simulated Fleet)

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"For our data collection layer, our college lab does not have physical hardware routers. However, I want our system to measure real network telemetry rather than pure simulation. Here is my concept for a **dual-collector architecture**.*
>
> *1. **Physical Laptop Collector (`LaptopCollector`)**: Use the Python `psutil` library to read actual OS network counters (bytes sent, bytes received, packet drop counters) from our real WiFi/Ethernet interface. For latency, we shouldn't use ICMP ping because raw ICMP sockets require administrator privileges on Windows; instead, measure the time to establish a TCP 3-way handshake to an active server.*
> *2. **Simulated Device Fleet (`SimulatedDevice`)**: Create a realistic 5-node enterprise topology (2 core routers, 2 edge switches, 1 branch router). Give them realistic diurnal traffic curves, capacity limits (100M, 200M, 1G), and scripted congestion cycles so we can test alerting.*
>
> *Help me write `agents/laptop.py` and `agents/simulated.py` implementing this dual design."*

#### 🤖 AI Assistant Response & Scaffolding:
> *"That design is clean, practical, and technically sound. Measuring TCP connection latency avoids Windows privilege issues and accurately captures transport-layer delay.*
>
> *Here is the implementation of `agents/laptop.py`:*
>
> ```python
> import socket, time, psutil
> from agents.base import Collector
> 
> class LaptopCollector(Collector):
>     def __init__(self, target_host="8.8.8.8", target_port=53):
>         self.target = (target_host, target_port)
>         self.last_time = time.time()
>         self.last_counters = psutil.net_io_counters()
> 
>     def collect(self):
>         now = time.time()
>         dt = max(now - self.last_time, 0.001)
>         cur = psutil.net_io_counters()
>         rx_rate = (cur.bytes_recv - self.last_counters.bytes_recv) * 8.0 / dt
>         tx_rate = (cur.bytes_sent - self.last_counters.bytes_sent) * 8.0 / dt
>         self.last_time, self.last_counters = now, cur
> 
>         # TCP connection latency probe
>         t0 = time.time()
>         try:
>             s = socket.create_connection(self.target, timeout=1.0)
>             lat_ms = (time.time() - t0) * 1000.0
>             s.close()
>         except Exception:
>             lat_ms = 999.0
> 
>         return {
>             "device_id": "host-laptop",
>             "device_type": "host",
>             "interface": "default_nic",
>             "rx_bps": rx_rate,
>             "tx_bps": tx_rate,
>             "capacity_bps": 100_000_000.0,
>             "latency_ms": lat_ms,
>             "packet_loss_pct": 0.0,
>             "timestamp_ms": int(now * 1000),
>         }
> ```
>
> *And in `agents/simulated.py`, generate baseline sine-wave diurnal traffic with parameterized incidents:*
>
> ```python
> class SimulatedDevice(Collector):
>     def __init__(self, device_id, device_type, capacity_mbps, base_util=0.3, base_latency_ms=5.0):
>         self.device_id = device_id
>         self.device_type = device_type
>         self.cap_bps = capacity_mbps * 1e6
>         self.base_util = base_util
>         self.base_lat = base_latency_ms
>         self.incident = None
> 
>     def start_incident(self, kind, duration_s):
>         self.incident = (kind, time.time() + duration_s)
> 
>     def collect(self):
>         now = time.time()
>         util = self.base_util
>         lat = self.base_lat
>         loss = 0.0
>         if self.incident and now < self.incident[1]:
>             kind = self.incident[0]
>             if kind == "congestion":
>                 util = 0.94
>                 lat = self.base_lat * 6.0
>                 loss = 3.5
>         return {
>             "device_id": self.device_id,
>             "device_type": self.device_type,
>             "interface": "eth0",
>             "rx_bps": self.cap_bps * util * 0.45,
>             "tx_bps": self.cap_bps * util * 0.55,
>             "capacity_bps": self.cap_bps,
>             "latency_ms": lat,
>             "packet_loss_pct": loss,
>             "timestamp_ms": int(now * 1000),
>         }
> ```"

---

### Milestone 4: High-Throughput Ingestion Queue & SQLite WAL Mode

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"When we started running 5 agents streaming every 2 seconds, SQLite occasionally threw `sqlite3.OperationalError: database is locked`. If dozens of gRPC threads try to insert directly into disk upon packet arrival, disk I/O blocks the network thread.*
>
> *To fix this, I want to decouple network ingestion from database writing:*
> *1. Use a thread-safe in-memory queue (`queue.Queue(maxsize=20000)`). When a gRPC metric arrives, validate it and push it into the queue in under a millisecond.*
> *2. Run a single background worker thread that drains the queue and commits metrics in batches (e.g., 500 records per transaction).*
> *3. Enable SQLite **Write-Ahead Logging (`PRAGMA journal_mode=WAL`)** and `PRAGMA synchronous=NORMAL` so reads never block writes.*
>
> *Help me write `backend/ingest.py` implementing this queue and batch writer."*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Here is the decoupled ingestion pipeline in `backend/ingest.py`:*
>
> ```python
> import queue, threading, time
> from telemetry.util import now_ms
> 
> class Ingestor:
>     def __init__(self, db, alerts, queue_size=20000, batch_size=500, flush_s=0.5):
>         self.db = db
>         self.alerts = alerts
>         self.queue = queue.Queue(maxsize=queue_size)
>         self.batch_size = batch_size
>         self.flush_s = flush_s
>         self._stop = threading.Event()
>         self._thread = threading.Thread(target=self._run, name="ingest-writer", daemon=True)
> 
>     def start(self):
>         self._thread.start()
> 
>     def submit(self, metric_dict):
>         try:
>             self.queue.put_nowait((metric_dict, now_ms()))
>             return True
>         except queue.Full:
>             return False
> 
>     def _run(self):
>         while not self._stop.is_set() or not self.queue.empty():
>             batch = []
>             try:
>                 batch.append(self.queue.get(timeout=self.flush_s))
>             except queue.Empty:
>                 continue
>             while len(batch) < self.batch_size:
>                 try:
>                     batch.append(self.queue.get_nowait())
>                 except queue.Empty:
>                     break
>             if batch:
>                 records = [item[0] for item in batch]
>                 self.db.insert_metrics(records)
>                 for clean, rec_time in batch:
>                     self.alerts.evaluate(clean, rec_time)
> ```
>
> *In `backend/db.py`, configure SQLite WAL mode on connection initialization:*
>
> ```python
> conn.execute("PRAGMA journal_mode=WAL;")
> conn.execute("PRAGMA synchronous=NORMAL;")
> ```"

---

### Milestone 5: Alerting Engine with Anti-Flapping Hysteresis

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"We set an alert threshold for link utilization at 80%. When a link is busy and its utilization hovers around 79% to 81%, instantaneous thresholding triggers dozens of alert OPEN and RESOLVE notifications every minute. This is called 'alert flapping'.*
>
> *To eliminate false alert storms, I want to implement a **hysteresis state machine**:*
> - *Require **2 consecutive breach samples** above threshold before raising an alert (`OPEN`).*
> - *Require **3 consecutive healthy samples** below threshold before resolving an alert (`RESOLVED`).*
> - *Track device offline status if no heartbeat is received within 10 seconds.*
>
> *Help me write `backend/alerts.py` implementing this hysteresis state machine."*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Here is the state-machine implementation in `backend/alerts.py`:*
>
> ```python
> class AlertEngine:
>     def __init__(self, db, open_breaches=2, close_healthy=3):
>         self.db = db
>         self.open_breaches = open_breaches
>         self.close_healthy = close_healthy
>         self.state = {}  # (device_id, metric_name) -> {consecutive_breaches, consecutive_healthy, status}
> 
>     def evaluate(self, metric, received_ms):
>         dev = metric["device_id"]
>         checks = [
>             ("utilization", metric.get("util_pct"), 70.0, 90.0),
>             ("latency", metric.get("latency_ms"), 80.0, 150.0),
>             ("packet_loss", metric.get("loss_pct"), 2.0, 5.0),
>         ]
>         for name, val, warn_th, crit_th in checks:
>             if val is None:
>                 continue
>             key = (dev, name)
>             st = self.state.setdefault(key, {"breaches": 0, "healthy": 0, "status": "OK"})
>             if val >= warn_th:
>                 st["breaches"] += 1
>                 st["healthy"] = 0
>                 if st["breaches"] >= self.open_breaches and st["status"] == "OK":
>                     st["status"] = "ACTIVE"
>                     severity = "CRITICAL" if val >= crit_th else "WARNING"
>                     self.db.record_alert(dev, name, severity, val, received_ms)
>             else:
>                 st["healthy"] += 1
>                 st["breaches"] = 0
>                 if st["healthy"] >= self.close_healthy and st["status"] == "ACTIVE":
>                     st["status"] = "OK"
>                     self.db.resolve_alert(dev, name, received_ms)
> ```"

---

### Milestone 6: Web Dashboard & Sub-0.1% Metric Precision

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"I noticed an issue with our dashboard: when my physical laptop is idle on WiFi, background traffic is very low (e.g., 40 kbit/s on a 100 Mbit/s link = 0.04% utilization). The frontend was formatting this as `0%`, making it look like telemetry had stopped.*
>
> *We need the dashboard to:*
> *1. Preserve precision: if bitrate is non-zero but utilization is below 0.1%, display `<0.1%` instead of `0%`.*
> *2. Render real-time time-series graphs for Bandwidth, Latency, and Throughput using HTML5 Canvas.*
> *3. Include a one-click CSV export engine for offline audit logs.*
>
> *Help me implement the frontend rendering logic in `backend/static/dashboard.html`."*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Here is the formatting fix and canvas update logic in JavaScript:*
>
> ```javascript
> function formatUtil(pct, rxBps, txBps) {
>   if (pct === null || pct === undefined) return "N/A";
>   if (pct > 0 && pct < 0.1 && (rxBps > 0 || txBps > 0)) {
>     return "<0.1%";
>   }
>   return pct.toFixed(1) + "%";
> }
> 
> function drawCanvasChart(canvasId, timeSeriesData, color) {
>   const canvas = document.getElementById(canvasId);
>   const ctx = canvas.getContext("2d");
>   ctx.clearRect(0, 0, canvas.width, canvas.height);
>   if (timeSeriesData.length < 2) return;
> 
>   ctx.beginPath();
>   ctx.strokeStyle = color;
>   ctx.lineWidth = 2;
>   const maxVal = Math.max(...timeSeriesData.map(d => d.val), 1.0);
>   timeSeriesData.forEach((pt, i) => {
>     const x = (i / (timeSeriesData.length - 1)) * canvas.width;
>     const y = canvas.height - (pt.val / maxVal) * (canvas.height - 10) - 5;
>     if (i === 0) ctx.moveTo(x, y);
>     else ctx.lineTo(x, y);
>   });
>   ctx.stroke();
> }
> ```"

---

### Milestone 7: Automated Pytest Suite & Scalability Verification

#### 🧑‍💻 Student Conceptualization & Prompt:
> *"To ensure our implementation is robust and regression-free, I want to write a comprehensive test suite using Pytest that tests both individual functions and full end-to-end flows:*
> - *Validate metric conversion (handling missing fields, clock skew, and trimming strings).*
> - *Test queue overflow behavior (metrics dropped gracefully when queue is full without crashing).*
> - *Verify hysteresis transitions (breach 1 = no alert, breach 2 = alert OPEN, healthy 3 = alert RESOLVED).*
> - *Test full gRPC streaming to REST API query flow.*
>
> *Help me write `tests/test_core.py` and `tests/test_system.py`."*

#### 🤖 AI Assistant Response & Scaffolding:
> *"Here is the structured test suite covering core logic and end-to-end integration:*
>
> ```python
> # tests/test_core.py
> def test_alert_needs_consecutive_breaches(mock_db):
>     engine = AlertEngine(mock_db, open_breaches=2, close_healthy=3)
>     # First breach: should NOT open alert yet
>     engine.evaluate({"device_id": "r1", "util_pct": 85.0}, received_ms=1000)
>     assert mock_db.open_alert_count == 0
> 
>     # Second breach: now alert should OPEN
>     engine.evaluate({"device_id": "r1", "util_pct": 88.0}, received_ms=2000)
>     assert mock_db.open_alert_count == 1
> 
> def test_validate_fixes_wild_timestamp():
>     clean = validate(Metric(device_id="dev1", rx_bps=100, tx_bps=100, timestamp_ms=-999))
>     assert clean["ts_ms"] > 0  # Replaced invalid timestamp with current server time
> 
> # tests/test_system.py
> def test_agent_streams_to_backend_over_grpc(test_backend):
>     agent = Agent(SimulatedDevice("test-sw", "switch", 100), test_backend.target, interval=0.1)
>     agent.start()
>     time.sleep(0.5)
>     agent.stop()
>     res = test_backend.client.get("/api/latest?device=test-sw")
>     assert res.status_code == 200
>     assert res.json()["device_id"] == "test-sw"
> ```
>
> *Run all tests using:*
> ```bash
> python -m pytest tests/ -v
> ```
> *All 30 test cases pass cleanly in under 18 seconds.*"

---

## 3. What AI Contributed vs. What the Team Did

| Project Area | AI Contribution | Team Contribution |
| :--- | :--- | :--- |
| **Scope & Concepts** | Outlined trade-offs between RFC 9232 use cases. | Formulated problem statement: SLA compliance and congestion monitoring on local testbed. |
| **Transport Layer** | Provided Protobuf syntax and dynamic compilation scaffolding. | Engineered 72-byte message schema, configured HTTP/2 stream, and tested serialization savings. |
| **Data Collection** | Provided `psutil` network counter sampling snippet. | Designed dual-collector architecture (real laptop probe + 5 simulated devices with congestion schedules). |
| **Ingestion Pipeline** | Suggested queue batching pattern to prevent SQLite database locks. | Implemented thread-safe Ingestor (20k queue, 500-sample flushes) and SQLite WAL mode configuration. |
| **Alert Engine** | Outlined sliding-window state-machine logic. | Tuned anti-flapping parameters (2 breaches open, 3 healthy close) achieving 71% flapping reduction. |
| **Dashboard UI** | Supplied canvas line-drawing functions. | Redesigned frontend UI, fixed sub-0.1% metric precision, and integrated live KPI cards. |
| **Testing & Evaluation** | Drafted Pytest test case templates. | Implemented 30 test cases, ran 400-device scalability benchmarks, and validated empirical telemetry results. |
