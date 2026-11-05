"""Backend entry point: gRPC receiver + ingest writer + alert monitor + REST API/dashboard."""
import argparse
import threading
import time

import uvicorn

from backend.alerts import AlertEngine
from backend.api import create_app
from backend.db import Database
from backend.grpc_server import create_grpc_server
from backend.ingest import Ingestor
from telemetry import config
from telemetry.util import now_ms


class Backend:
    """Wires all backend parts together. Used by main() and by the tests."""

    def __init__(self, db_path=config.DB_PATH, grpc_host=config.GRPC_HOST, grpc_port=config.GRPC_PORT):
        self.db = Database(db_path)
        # alerts left open by a previous run are stale now
        self.db.resolve_all_active(now_ms())
        self.alerts = AlertEngine(self.db)
        self.ingestor = Ingestor(self.db, self.alerts)
        self.grpc_server, self.grpc_port = create_grpc_server(
            self.ingestor, grpc_host, grpc_port, config.GRPC_MAX_WORKERS)
        self.app = create_app(self.db, self.ingestor, self.alerts)
        self._stop = threading.Event()
        self._monitor = threading.Thread(target=self._monitor_loop, name="monitor", daemon=True)

    def _monitor_loop(self):
        last_prune = 0.0
        while not self._stop.wait(1.0):
            try:
                self.alerts.check_offline(now_ms())
                if time.time() - last_prune > 600:  # every 10 minutes
                    cutoff = now_ms() - int(config.RETENTION_HOURS * 3600 * 1000)
                    self.db.prune(cutoff)
                    last_prune = time.time()
            except Exception as exc:
                print("monitor error:", exc)

    def start(self):
        self.ingestor.start()
        self.grpc_server.start()
        self._monitor.start()

    def stop(self):
        self._stop.set()
        self.grpc_server.stop(grace=2).wait()
        self.ingestor.stop()
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description="Network Telemetry backend")
    parser.add_argument("--db", default=config.DB_PATH, help="SQLite file (default: %(default)s)")
    parser.add_argument("--grpc-port", type=int, default=config.GRPC_PORT)
    parser.add_argument("--api-port", type=int, default=config.API_PORT)
    parser.add_argument("--host", default=config.API_HOST, help="address for the REST API/dashboard")
    args = parser.parse_args()

    backend = Backend(args.db, config.GRPC_HOST, args.grpc_port)
    backend.start()
    print(f"[backend] gRPC receiver listening on port {backend.grpc_port}")
    print(f"[backend] Dashboard:  http://localhost:{args.api_port}/")
    print(f"[backend] API docs:   http://localhost:{args.api_port}/docs")
    try:
        uvicorn.run(backend.app, host=args.host, port=args.api_port, log_level="warning")
    finally:
        backend.stop()


if __name__ == "__main__":
    main()
