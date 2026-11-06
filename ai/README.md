# AI Learning Dialogue & Development Prompts Log

**Course**: CS331 Computer Networks — Project 2  
**Project**: Real-Time Network Telemetry Framework (RFC 9232)  
**Team ID**: `T018`  
**Authors**: Avinash Reddy, Gella Jayarama Krishna, Sowpati Raj Kamal, Jangam Sanjay, Pulakurthi Manohar, Yalla Sai Teja  

---

## 1. Overview & Learning Approach

This document logs the interaction between our team and AI assistants (Claude and ChatGPT) during the conception, architectural design, implementation, and testing of our Network Telemetry project. 

Rather than treating AI as a code generator, our workflow was student-led and learning-focused:
1. **Conceptual Understanding First**: We studied the foundational networking concepts and RFC 9232 specifications, identified practical implementation challenges, and asked conceptual questions (often in our natural student phrasing and bilingual inquiries).
2. **Technical Scaffolding & Debugging**: Once the concept was clear, we asked for assistance with Protocol Buffer schemas, asynchronous queue concurrency, SQLite Write-Ahead Logging (WAL), and Pytest test cases.
3. **Local Execution & Verification**: Every script, collector, and database query was run locally in our Windows Python 3.12 environment. We directly inspected terminal logs, network interfaces, and database rows before adopting any code.

---

## 2. Top 10 Conceptual Learning Inquiries (Student Thought Process)

The prompts below capture how we worked through the core networking concepts, questioned ground truths, and formulated our system design.

---

### Prompt 1: Project Scope & Shortlisting RFC 9232 Use Cases

**🧑‍💻 Student Prompt:**
> *"Bhayya naku idhi help cheyyi... I am going through RFC 9232 (Network Telemetry Framework). Section 2.2 lo 6 different use cases unnayi: SLA compliance, network optimization, event tracking, root cause analysis, security, and policy compliance. Most traditional OAM tools were made for human operators using periodic polling, whereas network telemetry is designed to stream data continuously for automated systems.*
>
> *For our course project, we don't want to blindly pick something overly complex like AI routing or security anomaly detection that we cannot verify on our laptops. Which of these use cases has the clearest concepts, can be demonstrated convincingly, and gives us solid networking depth?"*

**💡 Concept Learned & Outcome:**
- Analyzed the six RFC 9232 use cases.
- Selected **SLA Compliance and Link Congestion Monitoring** as our core problem domain.
- Learned the architectural boundary: telemetry is the underlying push-based transport system, while SLA verification and threshold alerting are the analytical application running on top.

---

### Prompt 2: Push Telemetry vs Periodic SNMP Polling

**🧑‍💻 Student Prompt:**
> *"Explain me clearly from the start: asalu traditional SNMP polling ki RFC 9232 push telemetry ki main difference enti? Why is SNMP pull model considered bad for high-speed networks, and how does gRPC streaming keep a single persistent connection open without high overhead?"*

**💡 Concept Learned & Outcome:**
- SNMP pull polling requires the management station to periodically send request packets, creating high CPU overhead and smoothing out micro-bursts over 5-minute averages.
- gRPC push telemetry establishes a single persistent HTTP/2 TCP stream where edge devices stream compact binary metrics proactively every 2 seconds, exposing transient spikes within seconds.

---

### Prompt 3: Designing the Dual Collector (Physical Laptop + Simulated Topology)

**🧑‍💻 Student Prompt:**
> *"College lab lo real Cisco enterprise routers levu, but I don't want our project to be 100% fake simulation either. Can we make our laptop act as a real physical telemetry agent using psutil while simultaneously simulating enterprise routers and switches? How do they work together in one telemetry stream?"*

**💡 Concept Learned & Outcome:**
- Designed a **dual-collector architecture**:
  1. **Physical Host Agent**: Uses `psutil` to sample actual OS network interface counters (bytes received, bytes sent, packet drops, interface capacity).
  2. **Simulated Device Fleet**: Simulates 5 enterprise nodes (2 core routers, 2 edge switches, 1 branch router) generating diurnal sine-wave traffic and scripted congestion spikes.

---

### Prompt 4: Latency Ground Truths (TCP 3-Way Handshake vs ICMP Ping)

**🧑‍💻 Student Prompt:**
> *"In our laptop collector, latency check cheyadaniki ping vaduthunnama or something else? Does ping work offline or does it need internet? If Sir asks how we calculate latency in our code, what is the exact ground truth of what we are measuring?"*

**💡 Concept Learned & Outcome:**
- Discovered that creating raw ICMP sockets requires administrative / root privileges on Windows, which fails in standard non-root user environments.
- Instead, measuring the round-trip time required to establish a TCP connection (3-way handshake via `socket.create_connection`) measures true transport-layer connection latency safely and reliably without elevated OS permissions.

---

### Prompt 5: The Mystery of 0% Utilization on Active WiFi

**🧑‍💻 Student Prompt:**
> *"Bhayya why my utilization shows 0% on my laptop? Internet is working, browser is open, and YouTube is playing, but the dashboard table shows 0% utilization. Is the collector broken or is it a calculation issue?"*

**💡 Concept Learned & Outcome:**
- Discovered a metric fidelity issue: a modern WiFi interface has a capacity of 100 Mbit/s to 1 Gbit/s. Typical background traffic of 40–100 kbit/s represents only `0.04%` to `0.08%` link utilization.
- Standard integer or 1-decimal rounding was truncating `0.04%` to `0%`. Updated frontend logic to preserve sub-0.1% precision and display `<0.1%` when traffic is non-zero, maintaining continuous telemetry visibility.

---

### Prompt 6: Routers vs Switches vs Hosts in Network Telemetry

**🧑‍💻 Student Prompt:**
> *"Explain me what routers and switches are doing in this telemetry context. Why are we comparing router metrics with host metrics? How are interface counters and packet drops different between an edge switch and our physical laptop?"*

**💡 Concept Learned & Outcome:**
- Learned that core routers operate at high aggregated capacity with low baseline latency, edge switches experience localized access bursts and queueing delay, while end hosts primarily show asymmetric client traffic (high RX, low TX).
- Parameterized simulated devices with realistic capacities (100M, 200M, 1G) to reflect these real-world tier differences.

---

### Prompt 7: Protocol Buffers Compact Serialization vs JSON

**🧑‍💻 Student Prompt:**
> *"Why Protobuf instead of normal JSON or REST for telemetry streaming? 72 bytes payload vs 228 bytes JSON ante network lo bandwidth difference entha untundi when scaling to hundreds of devices?"*

**💡 Concept Learned & Outcome:**
- Protocol Buffers serialize typed fields into compact binary varints and field tags without transmitting repetitive string keys.
- Each telemetry sample is only **~72 bytes** in Protobuf versus **~228 bytes** in equivalent JSON—a 3.2× bandwidth reduction. Over 400 devices streaming at 1 sample/sec, this saves over 60 kB/s of raw bandwidth.

---

### Prompt 8: Ingestion Queueing & Resolving SQLite Database Locks

**🧑‍💻 Student Prompt:**
> *"Bhayya code lo database lock issue vasthondi. When multiple agents stream every 2 seconds, SQLite throws `sqlite3.OperationalError: database is locked`. How can we decouple gRPC network reception from database disk writing?"*

**💡 Concept Learned & Outcome:**
- Identified that concurrent thread writes to SQLite cause file lock contention.
- Implemented an asynchronous `Ingestor` with a thread-safe `queue.Queue(maxsize=20000)`. Incoming gRPC metrics are enqueued in under 1 ms in memory.
- A single background writer thread drains the queue in batches of up to 500 records, committing them to SQLite using **Write-Ahead Logging (`WAL` mode)** with zero dropped packets.

---

### Prompt 9: Anti-Flapping Hysteresis State Machine

**🧑‍💻 Student Prompt:**
> *"Alerts repeatedly trigger avtunnayi link 80% daggara unnapudu. When network utilization jumps between 79% and 81%, instantaneous thresholding triggers dozens of alert OPEN and RESOLVE notifications every minute. Hysteresis state machine tho false alerts ela stop cheyyali?"*

**💡 Concept Learned & Outcome:**
- Formulated a sliding-window hysteresis state machine:
  - Require **2 consecutive breach cycles** above threshold before opening an alert.
  - Require **3 consecutive healthy cycles** below threshold before resolving an alert.
- In trace-driven evaluation, this suppressed transient micro-noise, reducing false flapping alerts by **71%** (from 101/hr down to 29.6/hr).

---

### Prompt 10: Understanding the 400-Device Scalability Benchmark

**🧑‍💻 Student Prompt:**
> *"Can one laptop really handle 400 simulated devices? If Sir asks 'did you connect 400 physical routers in your lab?', how do I explain what our test harness actually benchmarked and why 0 packets were dropped?"*

**💡 Concept Learned & Outcome:**
- Formulated clear, honest technical defense:
  - We did *not* connect 400 physical hardware switches; we ran a software test harness generating 400 concurrent simulated agent streams communicating over real gRPC connections.
  - 400 devices sending 1 sample/sec = 400 samples/sec. With SQLite WAL batching, 400 records are written in less than one transaction per second, using only **17.8% of one CPU core** and **62 MB of RAM**.

---

## 3. Code Scaffolding & Implementation Prompts

Once the conceptual foundations were established, we used targeted technical prompts to scaffold, implement, and debug the production codebase.

---

### Prompt 11: Defining `proto/telemetry.proto` & Dynamic Loader

**🧑‍💻 Student Implementation Prompt:**
> *"Based on our metric requirements, write the Protobuf schema `proto/telemetry.proto`. Include service `Telemetry` with a client-streaming RPC `Stream(stream Metric) returns (StreamAck)`. Also, write `telemetry/protoloader.py` to compile the proto into `gen/` automatically on startup so team members don't have to run manual protoc commands."*

**🛠️ Generated Scaffolding & Outcome:**
- Generated `proto/telemetry.proto` (72-byte binary schema).
- Implemented `telemetry/protoloader.py` checking timestamps and compiling stubs dynamically using `grpc_tools.protoc`.

---

### Prompt 12: Implementing Physical Host Collector (`agents/laptop.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write `agents/laptop.py` subclassing our base `Collector`. Use `psutil.net_io_counters()` to calculate delta RX and TX bitrates. For latency, probe TCP connection time to `8.8.8.8:53` with a 1-second timeout. Ensure all returned fields match our Protobuf schema."*

**🛠️ Generated Scaffolding & Outcome:**
- Created `LaptopCollector` with rate calculation (`(bytes_cur - bytes_prev) * 8 / dt`) and non-privileged TCP handshake latency probing.

---

### Prompt 13: Implementing Multi-Node Simulation (`agents/simulated.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write `agents/simulated.py` supporting parameterized device profiles (`core-router`, `edge-switch`, `branch-router`). Implement a `start_incident(kind, duration)` method to inject temporary congestion spikes (utilization to 94%, latency multiplied by 6x, packet loss 3.5%) so we can test alert triggers."*

**🛠️ Generated Scaffolding & Outcome:**
- Implemented `SimulatedDevice` with base diurnal utilization and automated incident injection schedules repeating every 150 seconds.

---

### Prompt 14: Implementing Decoupled Queue Ingestor (`backend/ingest.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write `backend/ingest.py` implementing `Ingestor`. It must maintain an in-memory queue of capacity 20,000. `submit()` should be non-blocking. A background daemon thread should batch up to 500 records or flush every 0.5 seconds, inserting records into SQLite and passing them to the alert engine."*

**🛠️ Generated Scaffolding & Outcome:**
- Implemented thread-safe `Ingestor` class with batch queueing, lock-protected stats tracking (`received`, `dropped`, `stored`), and graceful thread shutdown.

---

### Prompt 15: Implementing Hysteresis Alerting Engine (`backend/alerts.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write `backend/alerts.py` implementing `AlertEngine`. For each device and metric (`utilization`, `latency`, `packet_loss`), track consecutive breaches and healthy cycles. Open alert only on 2 breaches; resolve only on 3 healthy samples. Also record offline alerts if a device stops reporting for over 10 seconds."*

**🛠️ Generated Scaffolding & Outcome:**
- Built `AlertEngine` state machine maintaining per-device sliding windows and persisting alert transitions (`ACTIVE`, `RESOLVED`, `OFFLINE`) to SQLite.

---

### Prompt 16: Live Dashboard with HTML5 Canvas (`dashboard.html`)

**🧑‍💻 Student Implementation Prompt:**
> *"Help me build the web dashboard in `backend/static/dashboard.html`. It should have KPI summary cards, a device interface table with animated utilization bars, sub-0.1% precision formatting (`<0.1%`), live HTML5 canvas line charts for bandwidth and latency, and a button to export historical telemetry to CSV."*

**🛠️ Generated Scaffolding & Outcome:**
- Developed responsive, single-page dashboard with vanilla JavaScript, real-time polling every 2 seconds, hardware-accelerated canvas graphs, and instant CSV generation.

---

### Prompt 17: Automated Pytest Suite (`tests/test_core.py` & `test_system.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write a comprehensive Pytest test suite covering: metric validation (wild timestamps, missing capacity), queue overflow resilience (dropping metrics safely without crash), hysteresis state transitions, and end-to-end gRPC streaming to REST API queries."*

**🛠️ Generated Scaffolding & Outcome:**
- Implemented 30 automated test cases across `tests/test_core.py` and `tests/test_system.py`. Verified that all 30 tests pass cleanly with 100% success rate.

---

### Prompt 18: Single-Command Demo Supervisor (`run_demo.py`)

**🧑‍💻 Student Implementation Prompt:**
> *"Write `run_demo.py` that launches the backend server (FastAPI + gRPC) and the agent cluster (laptop collector + 5 simulated devices) concurrently as subprocesses, waits for health check, opens the browser dashboard, and terminates all child processes cleanly on Ctrl+C."*

**🛠️ Generated Scaffolding & Outcome:**
- Created `run_demo.py` with cross-platform signal handling (`SIGINT`, `SIGTERM`), port readiness polling, and clean subprocess cleanup.

---

## 4. Summary: Student Intellectual Ownership vs. AI Scaffolding

| Project Stage | Team's Conceptual Formulation | AI Assistance Provided |
| :--- | :--- | :--- |
| **Scope & Concepts** | Decided on SLA compliance and link congestion detection on local testbed based on RFC 9232 review. | Outlined trade-offs between RFC 9232 operational applications. |
| **Transport Design** | Chose gRPC client-streaming over HTTP/2 with binary Protobuf to replace periodic SNMP polling. | Provided Protobuf syntax and dynamic runtime compiler script. |
| **Collector Architecture** | Designed dual-collector approach (real laptop OS counters + 5 simulated enterprise nodes). | Provided `psutil` sampling and TCP socket connection snippets. |
| **Ingestion Pipeline** | Formulated decoupled in-memory buffer queue to prevent SQLite concurrent lock contention. | Scaffolding for `queue.Queue` batching worker thread and WAL pragmas. |
| **Alert Logic** | Specified sliding-window hysteresis (2 breaches open, 3 healthy close) to eliminate 71% flapping noise. | Implemented dictionary-based state machine logic. |
| **User Interface** | Caught 0% rounding bug on idle links; mandated sub-0.1% precision and canvas charts. | Assisted with JavaScript canvas coordinate math and CSV blob generation. |
| **Testing & Evaluation** | Defined 30 verification cases (schema edge cases, queue overflow, gRPC streaming recovery). | Drafted test fixtures and assertion templates. |
