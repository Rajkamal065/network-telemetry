"""
One command to run the whole system for a demo:

    python run_demo.py

It starts the backend (gRPC receiver + REST API + dashboard) and the agents
(5 simulated devices + this computer) as two separate processes, opens the
dashboard in your browser, and stops both when you press Ctrl+C.

Options:
    --no-laptop      do not use this computer as a real device
    --no-incidents   do not inject scripted problems (calm network)
    --no-browser     do not open the browser automatically
    --devices N      number of simulated devices (default 5)
    --fresh          delete the old database first
"""
import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def wait_for_backend(url, seconds=20):
    end = time.time() + seconds
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=1).read()
            return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--no-laptop", action="store_true")
    p.add_argument("--no-incidents", action="store_true")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--devices", type=int)
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--api-port", type=int, default=int(os.getenv("TELEMETRY_API_PORT", "8000")))
    args = p.parse_args()

    if args.fresh:
        for f in ROOT.glob("telemetry.db*"):
            f.unlink()

    backend_cmd = [sys.executable, "-m", "backend.main", "--api-port", str(args.api_port)]
    agents_cmd = [sys.executable, "-m", "agents.run_agents"]
    if args.no_laptop:
        agents_cmd.append("--no-laptop")
    if args.no_incidents:
        agents_cmd.append("--no-incidents")
    if args.devices:
        agents_cmd += ["--devices", str(args.devices)]

    def _terminate(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _terminate)     # also stop cleanly when killed, not only on Ctrl+C

    procs = []
    try:
        procs.append(subprocess.Popen(backend_cmd, cwd=ROOT))
        url = f"http://localhost:{args.api_port}/"
        if not wait_for_backend(url + "api/health"):
            print("Backend did not start. Is port 8000 or 50051 already in use?")
            return 1
        procs.append(subprocess.Popen(agents_cmd, cwd=ROOT))
        print(f"\n>>> Dashboard: {url}\n>>> Press Ctrl+C to stop everything.\n")
        if not args.no_browser:
            webbrowser.open(url)
        while True:
            time.sleep(1)
            if any(pr.poll() is not None for pr in procs):
                print("A component stopped, shutting down.")
                break
    except KeyboardInterrupt:
        pass
    finally:
        for pr in reversed(procs):
            if pr.poll() is None:
                pr.terminate()
        for pr in procs:
            try:
                pr.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pr.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
