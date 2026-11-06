# AI Learning Prompts & Dialogue Log

**Project**: Real-Time Network Telemetry Framework (RFC 9232)  
**Course**: CS331 Computer Networks | **Team ID**: T018  
**Format**: Pedagogical Student Inquiry Record & Ground-Truth Analysis  

---

## Overview

This document presents the chronological student learning journey during the conceptualization, design, implementation, and evaluation of the **Network Telemetry Framework**. The prompts are organized across 9 iterative phases to highlight the ground-truth technical questions asked, concepts learned, and engineering trade-offs evaluated.

---

### Phase 1: Project Scope & RFC 9232 Use Case Shortlisting

**🧑‍💻 Student Prompt:**
> *"Network telemetry usually assumes machines as data consumers rather than human operators. But we have to build a system that collects, stores, and visualizes network metrics in real time for a student project. The RFC 9232 mentions 6 use cases (SLA compliance, network optimization, event tracking, root cause analysis, security, policy compliance). Which of these has a clear underlying idea, can be demonstrated convincingly, and gives enough technical depth without getting stuck in heavy ML or proprietary hardware?"*

**💡 Concept Learned & Outcome:**
- Evaluated RFC 9232 Section 2.2 operational applications.
- Selected **SLA Compliance and Link Congestion Monitoring** as the core problem domain.
- Learned the architectural separation between the underlying telemetry transport pipeline (data generation $\rightarrow$ push export $\rightarrow$ storage) and the analytical application layer (SLA evaluation, alerting, and visualization).

---

### Phase 2: Push Streaming vs Periodic Polling Fundamentals

**🧑‍💻 Student Prompt:**
> *"Why does RFC 9232 push telemetry beat SNMP polling? If our collector pushes metrics every 2 seconds over gRPC instead of polling every 5 minutes, how does gRPC maintain that connection over HTTP/2, and what happens to network overhead?"*

**💡 Concept Learned & Outcome:**
- Traditional SNMP pull polling introduces polling latency, high management station CPU load, and averages out transient micro-bursts over 5-minute intervals.
- gRPC push streaming establishes a single persistent HTTP/2 TCP connection over which binary-encoded Protocol Buffer messages are streamed proactively at 2-second intervals with sub-second delivery latency and zero polling lag.

---

### Phase 3: Designing the Dual Collector (Physical vs Simulated)

**🧑‍💻 Student Prompt:**
> *"We don't have 5 physical Cisco routers in our college lab, but we want our project to feel real. How can we make our laptop act as a real physical telemetry agent using psutil while simultaneously simulating enterprise core routers and edge switches with realistic traffic cycles and injected spikes?"*

**💡 Concept Learned & Outcome:**
- Architected a **dual-collector system**:
  1. **1 Physical Host Agent**: Queries local OS network counters via `psutil` (bytes sent/received, packet drop counters, interface capacity) combined with active TCP connection probing.
  2. **5 Simulated Device Agents**: Generate parameterized diurnal enterprise traffic waves (2 core routers, 2 edge switches, 1 branch router) with automated congestion injection scenarios.

---

### Phase 4: Latency Ground Truths (TCP Connection vs ICMP Ping)

**🧑‍💻 Student Prompt:**
> *"In our laptop collector, why do we measure TCP connection latency to a server rather than running ICMP ping? And if the professor asks 'how does your latency check work offline?', what is the exact ground truth of what our code is measuring?"*

**💡 Concept Learned & Outcome:**
- Discovered that creating raw ICMP sockets requires administrator / root privileges on Windows and Linux, making it fragile in standard student environments.
- Measuring the time required to complete a TCP 3-way handshake (`socket.connect_ex`) to an active target measures true transport-layer connection latency without requiring elevated OS permissions.

---

### Phase 5: Protocol Buffers Compact Schema Design

**🧑‍💻 Student Prompt:**
> *"Let's design telemetry.proto for our streaming metrics. What fields are essential for link monitoring, and how does Protocol Buffers encode numbers into ~72 bytes compared to ~228 bytes in JSON? Help me verify the proto syntax so protoc compiles without version mismatches."*

**💡 Concept Learned & Outcome:**
- Authored `proto/telemetry.proto` defining a 72-byte binary streaming payload (device identifier, interface name, RX/TX bitrates, packet loss percentage, TCP latency, capacity, and timestamp).
- Built `telemetry/protoloader.py` to compile Protobuf stubs dynamically on startup, eliminating grpcio version incompatibility issues across different operating systems.

---

### Phase 6: Ingestion Pipeline & SQLite WAL Decoupling

**🧑‍💻 Student Prompt:**
> *"When multiple agents stream metrics at high frequency, SQLite throws database locked errors if each request writes to disk directly. How can we decouple receiving from storing using an in-memory queue and batch commits in WAL mode?"*

**💡 Concept Learned & Outcome:**
- Implemented an asynchronous `Ingestor` with a thread-safe 20,000-capacity Python `Queue`.
- Decoupled network ingestion from disk I/O: gRPC server threads enqueue incoming samples in under 1 ms, while a dedicated background writer thread flushes batches of 500 records into SQLite using Write-Ahead Logging (`PRAGMA journal_mode=WAL`).

---

### Phase 7: Anti-Flapping Hysteresis State Machine

**🧑‍💻 Student Prompt:**
> *"When network traffic hovers right around our 80% threshold (like jumping between 79% and 81%), it fires dozens of spam alert emails every minute. How does a hysteresis state machine prevent this flapping, and how many consecutive breaches should we require before alerting?"*

**💡 Concept Learned & Outcome:**
- Designed a sliding-window hysteresis state machine requiring **2 consecutive breach cycles** to transition an alert to `OPEN` and **3 consecutive healthy cycles** to transition to `RESOLVED`.
- Replay evaluation on noisy 1-hour utilization traces proved a **71% reduction** in false flapping alerts compared to instantaneous alerting.

---

### Phase 8: Sub-0.1% Metric Precision in Live Dashboard

**🧑‍💻 Student Prompt:**
> *"When my laptop is idle on WiFi, the dashboard was displaying 0% utilization even though small background packets were flowing. How do we format the UI so it preserves sub-0.1% precision (like 0.04%) instead of truncating to zero, while keeping canvas graphs smooth?"*

**💡 Concept Learned & Outcome:**
- Adjusted frontend formatting logic in `dashboard.html` to inspect raw bitrates and render `<0.1%` rather than truncating to `0%`, preserving continuous metric observability.
- Built hardware-accelerated HTML5 canvas line graphs for real-time time-series rendering without browser memory leaks.

---

### Phase 9: Scalability Benchmarking & Viva Defense

**🧑‍💻 Student Prompt:**
> *"The report says we tested up to 400 simulated devices with zero drops. How does our test harness run 400 simulated agents, and how do we measure CPU usage and p95 latency to verify these numbers are reproducible on a standard laptop?"*

**💡 Concept Learned & Outcome:**
- Benchmarked ingestion queue performance using `python -m agents.run_agents --devices 400`.
- Verified that 400 samples/sec consumes only 17.8% of a single CPU core and 62 MB of RAM, with p95 delivery latency under 26 ms and zero dropped queue samples.
- Prepared honest, defensible viva explanations distinguishing simulated software agents from physical network switching ASICs.
