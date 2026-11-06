"""Settings shared by backend and agents. Every value can be overridden with an
environment variable, so you never have to edit code to change a port."""
import os

GRPC_HOST = os.getenv("TELEMETRY_GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("TELEMETRY_GRPC_PORT", "50051"))
API_HOST = os.getenv("TELEMETRY_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("TELEMETRY_API_PORT", "8000"))

# Where agents send data (the backend's gRPC address)
BACKEND_TARGET = os.getenv("TELEMETRY_BACKEND", "127.0.0.1:50051")

DB_PATH = os.getenv("TELEMETRY_DB", "telemetry.db")

# How often agents measure, in seconds
COLLECT_INTERVAL = float(os.getenv("TELEMETRY_INTERVAL", "2"))

# A device is "offline" if the backend heard nothing for this many seconds
OFFLINE_AFTER_S = float(os.getenv("TELEMETRY_OFFLINE_AFTER", "10"))

# Old data is deleted after this many hours (keeps the database small)
RETENTION_HOURS = float(os.getenv("TELEMETRY_RETENTION_HOURS", "48"))

# Default alert thresholds (can be changed at runtime through the REST API)
DEFAULT_THRESHOLDS = {
    "utilization_pct": {"warning": 70.0, "critical": 90.0},
    "latency_ms":      {"warning": 80.0, "critical": 150.0},
    "packet_loss_pct": {"warning": 2.0,  "critical": 5.0},
}

# An alert opens only after this many breaches in a row (avoids one-sample flapping)
BREACHES_TO_OPEN = int(os.getenv("TELEMETRY_BREACHES_TO_OPEN", "2"))
# ... and closes after this many healthy samples in a row
OKS_TO_CLOSE = int(os.getenv("TELEMETRY_OKS_TO_CLOSE", "3"))

# Maximum number of agents that can stream at the same time (one gRPC worker thread each)
GRPC_MAX_WORKERS = int(os.getenv("TELEMETRY_GRPC_WORKERS", "64"))
