"""
Start a fleet of agents in one process.

    python -m agents.run_agents                 # 5 simulated devices + your laptop
    python -m agents.run_agents --no-laptop     # simulated devices only
    python -m agents.run_agents --no-incidents  # calm network, no scripted problems
    python -m agents.run_agents --devices 20    # 20 simulated devices (scalability test)

To run a single device in its own terminal (shows that agents are independent):

    python -m agents.run_agents --only core-router-1 --no-laptop
"""
import argparse
import time

from agents.base import Agent
from agents.laptop import LaptopCollector
from agents.simulated import DEFAULT_FLEET, DEMO_CYCLE_S, DEMO_SCHEDULE, SimulatedDevice
from telemetry import config


def build_fleet(count=None, only=None):
    specs = [dict(s) for s in DEFAULT_FLEET]
    if count and count > len(specs):
        for i in range(len(specs), count):
            specs.append(dict(device_id=f"sim-device-{i + 1:03d}",
                              device_type="switch" if i % 2 else "router",
                              capacity_mbps=[100, 200, 1000][i % 3],
                              base_util=0.2 + (i % 5) * 0.08, base_latency_ms=2 + i % 9))
    elif count:
        specs = specs[:count]
    if only:
        specs = [s for s in specs if s["device_id"] in only]
    return [SimulatedDevice(**s) for s in specs]


def main():
    p = argparse.ArgumentParser(description="Run telemetry agents")
    p.add_argument("--target", default=config.BACKEND_TARGET, help="backend gRPC address (default %(default)s)")
    p.add_argument("--interval", type=float, default=config.COLLECT_INTERVAL, help="seconds between readings")
    p.add_argument("--devices", type=int, help="number of simulated devices (default 5)")
    p.add_argument("--only", nargs="+", help="run only these simulated device ids")
    p.add_argument("--no-laptop", action="store_true", help="do not add this computer as a real device")
    p.add_argument("--laptop-only", action="store_true", help="only this computer, no simulated devices")
    p.add_argument("--no-incidents", action="store_true", help="never inject scripted problems")
    args = p.parse_args()

    agents, devices = [], {}
    if not args.laptop_only:
        for dev in build_fleet(args.devices, args.only):
            devices[dev.device_id] = dev
            agents.append(Agent(dev, args.target, args.interval))
    if not args.no_laptop:
        agents.append(Agent(LaptopCollector(), args.target, args.interval))
    if not agents:
        raise SystemExit("nothing to run")

    for a in agents:
        a.start()
    print(f"[agents] {len(agents)} agents running, sending to {args.target} every {args.interval}s. Ctrl+C to stop.")
    if devices and not args.no_incidents:
        print(f"[agents] demo incidents are ON (they repeat every {DEMO_CYCLE_S}s so you can see alerts fire)")

    started = time.time()
    done = set()
    try:
        while True:
            time.sleep(0.5)
            if args.no_incidents:
                continue
            t = (time.time() - started) % DEMO_CYCLE_S
            cycle = int((time.time() - started) // DEMO_CYCLE_S)
            for at, dev_id, kind, duration in DEMO_SCHEDULE:
                key = (cycle, at, dev_id)
                if t >= at and key not in done and dev_id in devices:
                    done.add(key)
                    devices[dev_id].start_incident(kind, duration)
                    print(f"[agents] INCIDENT: {kind} on {dev_id} for {duration}s")
    except KeyboardInterrupt:
        pass
    finally:
        for a in agents:
            a.stop()


if __name__ == "__main__":
    main()
