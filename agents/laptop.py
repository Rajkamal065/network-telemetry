"""
Real device: your own computer.

Bandwidth: real, read from the operating system's network counters (psutil).
Latency:   real, measured as the time to open a TCP connection to a public DNS
           server (port 53). This works without administrator rights, unlike ping.
If the internet is not reachable, latency is reported as "not available" (-1)
and the dashboard simply shows a gap.
"""
import socket
import time

import psutil

from agents.base import Collector
from telemetry.protoloader import pb2

LATENCY_TARGETS = [("1.1.1.1", 53), ("8.8.8.8", 53)]


def tcp_connect_ms(host, port, timeout=0.7):
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError:
        return None
    return (time.perf_counter() - start) * 1000.0


def guess_capacity_bps():
    """Sum of the link speeds of active network interfaces; falls back to 100 Mbit/s."""
    best = 0
    try:
        for name, st in psutil.net_if_stats().items():
            if st.isup and st.speed and not name.lower().startswith(("lo", "loopback")):
                best = max(best, st.speed)   # speed is in Mbit/s
    except Exception:
        pass
    return (best if best > 0 else 100) * 1e6


class LaptopCollector(Collector):
    device_type = "host"

    def __init__(self, device_id=None, capacity_mbps=None):
        self.device_id = device_id or f"laptop-{socket.gethostname()}"[:40]
        self.interface = "all"
        self.capacity_bps = capacity_mbps * 1e6 if capacity_mbps else guess_capacity_bps()
        self._last = psutil.net_io_counters()
        self._last_t = time.monotonic()

    def collect(self):
        now_t = time.monotonic()
        counters = psutil.net_io_counters()
        dt = max(now_t - self._last_t, 1e-3)
        rx_bps = max(counters.bytes_recv - self._last.bytes_recv, 0) * 8 / dt
        tx_bps = max(counters.bytes_sent - self._last.bytes_sent, 0) * 8 / dt
        d_packets = (counters.packets_recv - self._last.packets_recv) + (counters.packets_sent - self._last.packets_sent)
        d_bad = (counters.errin - self._last.errin) + (counters.errout - self._last.errout) \
              + (counters.dropin - self._last.dropin) + (counters.dropout - self._last.dropout)
        loss = (d_bad / d_packets * 100.0) if d_packets > 0 else 0.0
        self._last, self._last_t = counters, now_t

        latency = None
        for host, port in LATENCY_TARGETS:
            latency = tcp_connect_ms(host, port)
            if latency is not None:
                break
        return pb2.Metric(
            device_id=self.device_id, device_type=self.device_type, interface=self.interface,
            timestamp_ms=int(time.time() * 1000),
            rx_bps=rx_bps, tx_bps=tx_bps, capacity_bps=self.capacity_bps,
            latency_ms=latency if latency is not None else -1.0,
            packet_loss_pct=min(loss, 100.0),
        )
