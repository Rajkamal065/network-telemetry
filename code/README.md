# Network Telemetry Framework — Source Code

This directory contains the complete source code implementation of the **Real-Time Network Telemetry Framework** adhering to RFC 9232 principles.

## Architecture & Directory Layout

- `proto/`: Protocol Buffers schema definition (`telemetry.proto`) specifying the 72-byte binary streaming contract.
- `gen/`: Precompiled Python gRPC stubs (`telemetry_pb2.py`, `telemetry_pb2_grpc.py`).
- `telemetry/`: Configuration, protocol buffer loader, and network utility helpers (`config.py`, `protoloader.py`, `util.py`).
- `agents/`: Dual-mode telemetry producers:
  - `laptop.py`: Collects physical OS network interface statistics via `psutil` and active TCP latency probing.
  - `simulated.py`: Generates realistic multi-tier enterprise router and switch traffic patterns with synthetic congestion injection.
  - `base.py`: Abstract base class and gRPC stream lifecycle management.
  - `run_agents.py`: Agent cluster process runner.
- `backend/`: High-throughput telemetry ingestion and presentation server:
  - `grpc_server.py`: High-performance gRPC receiver servicing push telemetry streams.
  - `ingest.py`: Thread-safe decoupled in-memory buffer queue (capacity 20,000).
  - `db.py`: SQLite batch persistence engine using Write-Ahead Logging (WAL).
  - `alerts.py`: Anti-flapping hysteresis alert evaluation engine (2-cycle thresholding).
  - `api.py`: FastAPI asynchronous REST endpoints (`/api/latest`, `/api/history`, `/api/alerts`, `/api/export`, `/metrics`).
  - `static/dashboard.html`: Real-time web dashboard with hardware-accelerated HTML5 canvas time-series graphs.
- `tests/`: 30 automated test cases verifying schema validation, queue overflow resilience, hysteresis state transitions, REST endpoints, and gRPC streaming recovery.
- `deploy/`: Containerization manifests (Docker Compose) and Prometheus/Grafana configurations.
- `run_demo.py`: One-command launcher starting backend and agents concurrently.
- `run_backend.py`: Dedicated backend process launcher.
- `run_agents.py`: Dedicated agent process launcher.

## Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Run the Full Interactive Demo
Launch the complete end-to-end framework (backend + 5 simulated devices + physical computer) in a single command:
```bash
python run_demo.py
```
This automatically starts the gRPC receiver (port `50051`), FastAPI REST server (port `8000`), opens the live web dashboard in your default browser at `http://localhost:8000`, and streams live telemetry.

Optional flags:
- `--no-laptop`: Exclude the host computer; stream only simulated network devices.
- `--no-incidents`: Run with normal background traffic without synthetic congestion spikes.
- `--devices N`: Adjust the number of simulated switches and routers (default: `5`).
- `--fresh`: Delete existing SQLite database before starting.

### 3. Run Automated Tests
Execute the comprehensive Pytest test suite:
```bash
python -m pytest tests/ -v
```
Expected output: **30 passed in ~17 seconds**.

