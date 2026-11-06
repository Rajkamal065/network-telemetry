# Network Telemetry Framework — Source Code

This directory contains the complete source code implementation of the **Real-Time Network Telemetry Framework** adhering to RFC 9232 principles.

## Architecture & Directory Layout

- `proto/`: Protocol Buffers schema definition (`telemetry.proto`) specifying the 72-byte binary streaming contract.
- `gen/`: Precompiled Python gRPC stubs (`telemetry_pb2.py`, `telemetry_pb2_grpc.py`).
- `telemetry/`: Core domain models, telemetry validation logic, sliding-window hysteresis alerting engine, and SQLite WAL database storage.
- `agents/`: Dual-mode telemetry producers:
  - `host_collector.py`: Collects physical OS network interface statistics via `psutil` and active TCP latency probing.
  - `simulated_collector.py`: Generates realistic multi-tier enterprise router and switch traffic patterns with synthetic congestion injection.
  - `run_agents.py`: Orchestrates agent lifecycle and streaming over persistent gRPC HTTP/2 channels.
- `backend/`: Fast, asynchronous telemetry receiver and presentation server:
  - `grpc_server.py`: High-throughput gRPC collector servicing client push streams.
  - `api.py`: FastAPI asynchronous REST endpoints (`/api/latest`, `/api/history`, `/api/alerts`, `/api/export`, `/metrics`).
  - `web/`: Real-time web dashboard with hardware-accelerated HTML5 canvas time-series graphs.
- `tests/`: 30 automated test cases verifying schema validation, queue overflow resilience, hysteresis state transitions, REST endpoints, and gRPC streaming recovery.
- `deploy/`: Containerization manifests and systemd unit configurations.
- `run_demo.py`: One-click supervisor process launching the backend and multi-agent cluster concurrently.

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

