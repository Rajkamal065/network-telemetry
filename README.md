# Real-Time Network Telemetry Framework (RFC 9232)

**CS331 Computer Networks — Final Project Submission**  
**Department of Computer Science & Engineering**  
**Team ID:** `T018`

---

## Team Members

| Name | Roll Number | Primary Contribution |
| :--- | :--- | :--- |
| **Avinash Reddy** | `23110123` | Protocol Buffers schema design & gRPC transport |
| **Gella Jayarama Krishna** | `23110115` | Multi-agent network simulation & congestion injection |
| **Sowpati Raj Kamal** | `23110319` | SQLite ingestion pipeline, queueing & FastAPI backend |
| **Jangam Sanjay** | `23110144` | Hysteresis state machine & threshold alerting engine |
| **Pulakurthi Manohar** | `23110259` | Real-time web dashboard & HTML5 canvas visualizer |
| **Yalla Sai Teja** | `23110366` | Experimental evaluation, test harness & performance benchmarking |

---

## Repository Structure

In accordance with the Project 2 submission requirements, the repository is structured as follows:

```text
network-telemetry/
├── README.md                      # Root documentation and reproduction guide
├── code/                          # All source code, tests, and configuration
│   ├── proto/                     # Protocol Buffers schema (telemetry.proto)
│   ├── gen/                       # Generated Python gRPC stubs
│   ├── telemetry/                 # Core models, validation, alert logic, DB storage
│   ├── agents/                    # Host (psutil) and simulated device producers
│   ├── backend/                   # gRPC receiver, FastAPI REST server, live dashboard
│   ├── tests/                     # 30 automated Pytest test cases (100% passing)
│   ├── deploy/                    # Containerization manifests and Docker Compose
│   ├── docs/                      # RFC 9232 architectural design specification
│   ├── run_demo.py                # One-command full system demo launcher
│   ├── requirements.txt           # Production dependencies
│   ├── requirements-dev.txt       # Testing dependencies
│   └── README.md                  # Detailed code execution instructions
├── report/                        # Final academic project report
│   ├── Network_Telemetry_Report.pdf  # 9-page IEEE 2-column report (PDF)
│   └── README.md                  # Report overview, abstract, and section index
├── ppt/                           # Presentation slide decks
│   ├── Network_Telemetry_Presentation.pptx # Submittable 6-slide deck (.pptx)
│   ├── Network_Telemetry_Presentation.pdf  # High-resolution widescreen slide deck (PDF)
│   ├── generate_presentation_pdf.py       # Reproducible PDF slide generator script
│   ├── generate_pptx.py                   # Reproducible PPTX slide generator script
│   ├── presentation_slides.html           # Standalone interactive HTML presentation
│   └── README.md                  # Slide outline, topics, and presenter notes
└── ai/                            # Transparent AI prompts and development dialogue
    └── README.md                  # Comprehensive student learning inquiry and code generation dialogue
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Git

### 2. Setup & Installation
```bash
# Clone the repository
git clone https://github.com/Rajkamal065/network-telemetry.git
cd network-telemetry/code

# Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Run the Complete System Demo
Launch the entire telemetry ecosystem (gRPC receiver, REST backend, live browser dashboard, physical laptop collector, and 5 simulated network devices) with a single command:

```bash
python run_demo.py
```

- **Live Dashboard**: Opens automatically at `http://localhost:8000`
- **gRPC Ingestion Server**: Active on `localhost:50051`
- **Scripted Fault Injection**: Injects automated congestion on `edge-switch-1` at 20s, latency spikes on `core-router-1` at 60s, and packet loss on `branch-router` at 100s to demonstrate real-time alerting and automatic recovery.
- Press `Ctrl+C` to terminate all background collector and server processes cleanly.

### 4. Run Automated Test Suite
To verify the complete framework, run the 30 automated test cases:

```bash
python -m pytest tests/ -v
```

**Result:** `30 passed in ~17s` (100% pass rate).

---

## System Architecture & RFC 9232 Compliance

The framework implements the continuous push telemetry model defined in **RFC 9232** (*Network Telemetry Framework*):

```text
 +---------------------------------------------------------+
 |             Data Collection Layer (Agents)              |
 |  - Host Collector: psutil OS counters + TCP ping        |
 |  - Simulated Cluster: 2 Core Routers, 2 Edge Switches,  |
 |    1 Branch Router (periodic traffic + injected faults) |
 +---------------------------------------------------------+
                             │
                             ▼  Persistent HTTP/2 gRPC Push Stream
 +---------------------------------------------------------+
 |             Transport Layer (Protobuf / gRPC)           |
 |  - 72-byte binary Protocol Buffer payloads              |
 |  - 2-second streaming cadence over persistent TCP       |
 +---------------------------------------------------------+
                             │
                             ▼
 +---------------------------------------------------------+
 |           Ingestion & Storage Layer (Backend)           |
 |  - High-throughput gRPC Receiver                        |
 |  - Thread-safe Decoupled In-Memory Queue (20,000 cap)   |
 |  - Asynchronous Batch Writer (500 records/flush)        |
 |  - SQLite Database with Write-Ahead Logging (WAL)       |
 +---------------------------------------------------------+
                             │
                             ▼
 +---------------------------------------------------------+
 |          Alerting, Analysis & Presentation Layer        |
 |  - Hysteresis Alerting Engine (2-cycle anti-flapping)   |
 |  - FastAPI REST Endpoints (/api/latest, /api/history)   |
 |  - Hardware-Accelerated HTML5 Canvas Real-Time Charts   |
 |  - Single-Click Audit-Ready CSV & JSON Export           |
 +---------------------------------------------------------+
```

---

## Key Quantitative Experimental Findings

| Metric / Benchmark | Result | Evaluation Significance |
| :--- | :--- | :--- |
| **Max Concurrent Devices** | **400 devices** | Zero dropped packets at 400 samples/sec; p95 latency remains below 26 ms. |
| **Payload Compactness** | **~72 bytes/sample** | 85.6% bandwidth reduction compared to verbose text/JSON polling payloads. |
| **Congestion Alert Time** | **2.8 seconds** | Fast detection of link saturation within 1 to 2 sampling cycles. |
| **Flapping Suppression** | **71% reduction** | Consecutive-breach hysteresis reduced false alert triggers from 101/hr to 29.6/hr. |
| **Automated Test Coverage** | **30 / 30 Passed** | Comprehensive test coverage across Protobuf encoding, queue overflow, and REST APIs. |

---

## Links to Submission Artifacts

- **Report PDF**: [report/Network_Telemetry_Report.pdf](./report/Network_Telemetry_Report.pdf) *(Updated with Appendix B Prompts Table, 9 Pages)*
- **Presentation Slides (PPTX)**: [ppt/Network_Telemetry_Presentation.pptx](./ppt/Network_Telemetry_Presentation.pptx)
- **Presentation Slides (PDF)**: [ppt/Network_Telemetry_Presentation.pdf](./ppt/Network_Telemetry_Presentation.pdf)
- **AI Prompts & Development Dialogue**: [ai/README.md](./ai/README.md)
