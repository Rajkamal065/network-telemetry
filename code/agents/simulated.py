"""
Simulated router / switch.

It produces believable numbers without real hardware:
  * bandwidth follows a smooth wave (like busy and quiet hours) plus random noise
  * latency grows when the link is busy (queues fill up) and has rare random spikes
  * packet loss appears only when the link is almost full
  * incidents can be injected on purpose (to demonstrate alerts in the demo):
        "congestion"  -> traffic jumps close to the link capacity
        "latency"     -> latency jumps to a high value
        "loss"        -> packet loss appears
"""
import math
import random
import time

from agents.base import Collector
from telemetry.protoloader import pb2


class SimulatedDevice(Collector):
    def __init__(self, device_id, device_type="router", capacity_mbps=1000.0,
                 base_util=0.30, base_latency_ms=8.0, seed=None, interface="eth0"):
        self.device_id = device_id
        self.device_type = device_type
        self.interface = interface
        self.capacity_bps = capacity_mbps * 1e6
        self.base_util = base_util
        self.base_latency_ms = base_latency_ms
        self.rng = random.Random(seed if seed is not None else device_id)
        self.phase = self.rng.uniform(0, 2 * math.pi)
        self.period_s = self.rng.uniform(90, 180)       # one "busy/quiet" cycle
        self.incident = None                           # (kind, ends_at_epoch_s)
        self._latency_spike_until = 0.0

    # ------------------------------------------------------------ incidents
    def start_incident(self, kind, duration_s):
        if kind not in ("congestion", "latency", "loss"):
            raise ValueError(kind)
        self.incident = (kind, time.time() + duration_s)

    def _active_incident(self, now):
        if self.incident and now < self.incident[1]:
            return self.incident[0]
        self.incident = None
        return None

    # -------------------------------------------------------------- measure
    def collect(self):
        now = time.time()
        wave = math.sin(2 * math.pi * now / self.period_s + self.phase)
        util = self.base_util + 0.18 * wave + self.rng.gauss(0, 0.03)
        incident = self._active_incident(now)
        if incident == "congestion":
            util = 0.93 + self.rng.uniform(-0.03, 0.05)
        util = min(max(util, 0.02), 0.99)

        # directions: usually download heavy
        rx = util * self.capacity_bps * self.rng.uniform(0.92, 1.0)
        tx = util * self.capacity_bps * self.rng.uniform(0.35, 0.6)

        # latency: base + queueing delay that explodes near full load + noise
        queueing = 25.0 * (util ** 4) / max(0.05, 1.02 - util)
        latency = self.base_latency_ms + queueing + abs(self.rng.gauss(0, 1.2))
        if now > self._latency_spike_until and self.rng.random() < 0.01:
            self._latency_spike_until = now + self.rng.uniform(2, 5)   # rare short spike
        if now < self._latency_spike_until:
            latency += self.rng.uniform(30, 70)
        if incident == "latency":
            latency = self.rng.uniform(170, 230)

        loss = 0.0
        if util > 0.92:
            loss = self.rng.uniform(2.2, 4.0)      # congested link drops packets
        if incident == "loss":
            loss = self.rng.uniform(5.5, 9.0)

        return pb2.Metric(
            device_id=self.device_id, device_type=self.device_type, interface=self.interface,
            timestamp_ms=int(now * 1000),
            rx_bps=rx, tx_bps=tx, capacity_bps=self.capacity_bps,
            latency_ms=latency, packet_loss_pct=loss,
        )


# The default network used by the demo
DEFAULT_FLEET = [
    dict(device_id="core-router-1", device_type="router", capacity_mbps=1000, base_util=0.35, base_latency_ms=4),
    dict(device_id="core-router-2", device_type="router", capacity_mbps=1000, base_util=0.28, base_latency_ms=5),
    dict(device_id="edge-switch-1", device_type="switch", capacity_mbps=100, base_util=0.40, base_latency_ms=2),
    dict(device_id="edge-switch-2", device_type="switch", capacity_mbps=100, base_util=0.30, base_latency_ms=3),
    dict(device_id="branch-router", device_type="router", capacity_mbps=200, base_util=0.25, base_latency_ms=22),
]

# Scheduled demo incidents: (seconds after start, device_id, kind, duration seconds)
# The whole schedule repeats every DEMO_CYCLE_S seconds.
DEMO_CYCLE_S = 150
DEMO_SCHEDULE = [
    (20, "edge-switch-1", "congestion", 25),
    (60, "core-router-1", "latency", 25),
    (100, "branch-router", "loss", 20),
]
