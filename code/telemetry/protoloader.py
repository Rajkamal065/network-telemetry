"""
Loads the gRPC code generated from proto/telemetry.proto.

Why this file exists: the generated files depend on the exact grpcio/protobuf
versions installed on YOUR machine. So instead of shipping generated files that
might not match, we generate them on first run (takes about a second) into the
folder "gen/" and import them from there.
"""
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
GEN_DIR = ROOT / "gen"


def _generate():
    GEN_DIR.mkdir(exist_ok=True)
    (GEN_DIR / "__init__.py").touch()
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={GEN_DIR}",
        f"--grpc_python_out={GEN_DIR}",
        str(PROTO_DIR / "telemetry.proto"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("protoc failed:\n" + result.stderr)


def load():
    """Return (telemetry_pb2, telemetry_pb2_grpc), generating them if needed."""
    pb2_file = GEN_DIR / "telemetry_pb2.py"
    grpc_file = GEN_DIR / "telemetry_pb2_grpc.py"
    proto_file = PROTO_DIR / "telemetry.proto"
    stale = (not pb2_file.exists() or not grpc_file.exists()
             or pb2_file.stat().st_mtime < proto_file.stat().st_mtime)
    if stale:
        _generate()
    # generated grpc file does "import telemetry_pb2", so GEN_DIR must be on sys.path
    if str(GEN_DIR) not in sys.path:
        sys.path.insert(0, str(GEN_DIR))
    try:
        pb2 = importlib.import_module("telemetry_pb2")
        pb2_grpc = importlib.import_module("telemetry_pb2_grpc")
    except Exception:
        # generated with a different library version -> regenerate once
        _generate()
        for name in ("telemetry_pb2", "telemetry_pb2_grpc"):
            sys.modules.pop(name, None)
        pb2 = importlib.import_module("telemetry_pb2")
        pb2_grpc = importlib.import_module("telemetry_pb2_grpc")
    return pb2, pb2_grpc


pb2, pb2_grpc = load()
