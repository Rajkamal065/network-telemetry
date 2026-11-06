# AI Usage Documentation

**Project**: Network Telemetry & Real-Time Network Performance Monitoring System (RFC 9232)  
**Course**: CS331 Computer Networks | **Team ID**: T018  
**Format**: Academic Submission Appendix / Verification Log  

---

## 1. How I Used AI During the Project

I used ChatGPT and Claude mainly as technical learning and debugging assistants while developing and testing the Network Telemetry project. I did not use AI as a black-box replacement for running or designing the system. The underlying concept, architectural decisions, and metric validation were formulated by our team.

I used AI when I was stuck on an error, when I needed to understand the ground truth behind a network metric (such as TCP handshake latency vs ICMP ping), when I wanted to compare implementation trade-offs (such as SQLite WAL mode vs threading locks), or when I needed to verify whether a change in the Protobuf schema would break the ingestion queue. Every single command was run locally in my Windows Python environment, and I inspected and validated the real outputs before accepting any change.

---

## 2. Prompts I Used During Development

The prompts below represent the actual learning queries I used while working through the project. They illustrate how I structured my questions to understand foundational concepts, evaluate RFC 9232 use cases, and resolve real implementation bugs.

| Project Area | Prompt I Used | How It Helped |
| :--- | :--- | :--- |
| **Understanding Project & RFC 9232 Scope** | *"We are starting our Computer Networks project on RFC 9232 Network Telemetry. RFC 9232 outlines 6 use cases: SLA compliance, congestion monitoring, root cause analysis, security, policy compliance, and event tracking. As students working locally, which use cases have the clearest concepts, can be demonstrated convincingly, and give us solid technical depth without getting stuck in overly complex AI or routing math?"* | Helped me narrow down the scope to SLA compliance and link congestion monitoring, avoiding overly complex routing/ML extensions that would be hard to defend in viva. |
| **Push Telemetry vs Periodic Polling** | *"Why does RFC 9232 emphasize push telemetry over traditional SNMP polling? If our collector pushes metrics every 2 seconds over gRPC instead of the server polling every 5 minutes, how does gRPC keep that single HTTP/2 connection open, and what happens to device CPU and network overhead?"* | Helped me grasp the fundamental difference between pull and push models and how persistent HTTP/2 TCP streams reduce device CPU overhead. |
| **Collector Implementation (Physical vs Simulated)** | *"We don't have 5 physical routers in our college lab, but we want our project to feel real. How can we make our laptop act as a real physical telemetry agent using psutil while simultaneously simulating enterprise core routers and edge switches with realistic traffic cycles and injected spikes?"* | Guided me to design a dual-collector architecture: 1 physical laptop node for ground-truth OS metrics and 5 simulated devices for enterprise congestion scenarios. |
| **Metric Ground Truths (TCP Latency vs ICMP Ping)** | *"In our laptop collector, why do we measure TCP connection latency to a server rather than running ICMP ping? And if the professor asks 'how does your latency check work offline?', what is the exact ground truth of what our code is measuring?"* | Taught me that non-privileged user-space apps cannot easily send raw ICMP packets on Windows without admin rights, so measuring TCP 3-way handshake latency to a configured target is safe, standard, and explainable. |
| **Protobuf Schema & Compact Transport** | *"Let's design telemetry.proto for our streaming metrics. What fields are essential for link monitoring, and how does Protocol Buffers encode numbers into ~72 bytes compared to ~228 bytes in JSON? Help me verify the proto syntax so protoc compiles without version mismatches."* | Helped me write a clean 72-byte proto3 schema and set up dynamic runtime loading via `protoloader.py` to avoid gRPC binary version conflicts. |
| **SQLite WAL Mode & Decoupled Queue** | *"When multiple agents stream metrics at high frequency, SQLite throws database locked errors if each request writes to disk directly. How can we decouple receiving from storing using an in-memory queue and batch commits in WAL mode?"* | Helped me implement a thread-safe Queue (capacity 20,000) with a dedicated background worker that writes in 500-record batches, eliminating disk write bottlenecks. |
| **Alert Flapping & Hysteresis State Machine** | *"When network traffic hovers right around our 80% threshold (like jumping between 79% and 81%), it fires dozens of spam alert emails every minute. How does a hysteresis state machine prevent this flapping, and how many consecutive breaches should we require before alerting?"* | Helped me design a 2-breach open and 3-healthy close state machine, reducing noisy false alerts by 71% in our experiments. |
| **Sub-0.1% Metric Precision in Dashboard** | *"When my laptop is idle on WiFi, the dashboard was displaying 0% utilization even though small background packets were flowing. How do we format the UI so it preserves sub-0.1% precision (like 0.04%) instead of truncating to zero, while keeping canvas graphs smooth?"* | Helped me debug the frontend math so idle traffic is accurately displayed rather than rounded away, maintaining continuous telemetry visibility. |
| **Scalability Testing & Benchmark Verification** | *"The report says we tested up to 400 simulated devices with zero drops. How does our test harness run 400 simulated agents, and how do we measure CPU usage and p95 latency to verify these numbers are reproducible on a standard laptop?"* | Guided me on using `agents.run_agents --devices 400` to benchmark ingestion throughput and verify that SQLite WAL handles 400 samples/sec easily. |
| **Viva Preparation & Concept Simplification** | *"My professor hates buzzwords and will stop me if I use terms I don't understand. Can you review our project slides and replace complicated jargon with simple, honest student-level explanations of what our code actually does?"* | Simplified slide wording, eliminated inflated claims, and prepared me with clear answers on RTT, device simulation, and buffer queueing. |

---

## 3. How I Worked With the AI Suggestions

My workflow was never to accept an AI response blindly. I always provided the actual error tracebacks, configuration files, and live console outputs I observed. 

For example, when testing agent connections, port `50051` conflicts occurred on Windows; I had to diagnose active sockets using `netstat` and adjust environment variables myself. Similarly, when AI initially suggested complex ML-based anomaly models, I rejected them in favor of a transparent, deterministic hysteresis state machine that I could explain line-by-line during our course viva.

---

## 4. What AI Contributed vs. What I Did

| Stage | AI Contribution | My Contribution |
| :--- | :--- | :--- |
| **Planning** | Discussed RFC 9232 use case trade-offs and suggested SLA & congestion monitoring. | Selected the local testbed scope, determined project boundaries, and finalized deliverables. |
| **Implementation** | Provided skeleton structures for Protobuf schemas and decoupled queue batching. | Implemented psutil OS collection, simulated device loops, SQLite WAL schema, and FastAPI endpoints. |
| **Environment Setup** | Explained gRPC compiler flags and Windows process signal handling. | Configured Python 3.12 venv, resolved Windows port bindings, and set up test harnesses. |
| **Debugging** | Interpreted database locked errors and suggested batch-commit queue patterns. | Investigated SQLite WAL pragma configurations, fixed sub-0.1% rounding in JS, and verified fixes. |
| **Testing** | Outlined potential edge test cases (e.g. clock skew, wild timestamps, queue overflow). | Executed the 30-case Pytest suite, benchmarked 400 simulated devices, and collected empirical telemetry. |
| **Evaluation** | Helped structure comparison tables (Protobuf vs JSON byte sizes, hysteresis flapping). | Verified metrics against actual database rows, measured real memory/CPU, and validated charts. |
| **Documentation** | Suggested concise formatting and helped refine technical clarity. | Authored report sections, created diagrams, verified viva talking points, and finalized slides. |
