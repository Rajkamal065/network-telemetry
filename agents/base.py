"""
Base agent: measures a device every interval and streams the readings to the
backend over one long-lived gRPC connection.

Reliability built in:
  * readings go into a local queue first, so a slow or dead backend never blocks measuring
  * if the connection breaks, the agent reconnects with a growing delay (1s, 2s, 4s ... max 10s)
  * while disconnected, readings wait in the queue (up to BUFFER_SIZE, oldest dropped first)
"""
import queue
import threading
import time

import grpc

from telemetry import config
from telemetry.protoloader import pb2, pb2_grpc

BUFFER_SIZE = 1000


class Collector:
    """Anything that can produce one reading. Subclass and implement collect()."""
    device_id = "unknown"
    device_type = "unknown"

    def collect(self):
        """Return a pb2.Metric."""
        raise NotImplementedError


class Agent:
    def __init__(self, collector, target=config.BACKEND_TARGET, interval=config.COLLECT_INTERVAL,
                 quiet=False):
        self.collector = collector
        self.target = target
        self.interval = interval
        self.quiet = quiet
        self._queue = queue.Queue(maxsize=BUFFER_SIZE)
        self._stop = threading.Event()
        self.sent = 0
        self.connected = False
        self._threads = []

    def log(self, text):
        if not self.quiet:
            print(f"[{self.collector.device_id}] {text}", flush=True)

    # ------------------------------------------------------------- measuring
    def _measure_loop(self):
        next_time = time.monotonic()
        while not self._stop.is_set():
            try:
                metric = self.collector.collect()
                try:
                    self._queue.put_nowait(metric)
                except queue.Full:
                    try:
                        self._queue.get_nowait()   # drop the oldest
                    except queue.Empty:
                        pass
                    self._queue.put_nowait(metric)
            except Exception as exc:
                self.log(f"collect failed: {exc!r}")
            next_time += self.interval
            self._stop.wait(max(0.0, next_time - time.monotonic()))

    # -------------------------------------------------------------- sending
    def _metric_iter(self):
        while not self._stop.is_set():
            try:
                metric = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self.sent += 1
            yield metric

    def _send_loop(self):
        delay = 1.0
        while not self._stop.is_set():
            channel = grpc.insecure_channel(self.target)
            stub = pb2_grpc.TelemetryStub(channel)
            try:
                grpc.channel_ready_future(channel).result(timeout=3)
                self.connected = True
                self.log(f"connected to backend {self.target}")
                delay = 1.0
                stub.Stream(self._metric_iter())      # blocks until stopped or broken
            except (grpc.FutureTimeoutError, grpc.RpcError) as exc:
                if self.connected:
                    self.log("connection lost, will retry")
                self.connected = False
            finally:
                channel.close()
            if not self._stop.is_set():
                self._stop.wait(delay)
                delay = min(delay * 2, 10.0)

    # ------------------------------------------------------------ lifecycle
    def start(self):
        for fn, name in ((self._measure_loop, "measure"), (self._send_loop, "send")):
            t = threading.Thread(target=fn, name=f"{self.collector.device_id}-{name}", daemon=True)
            t.start()
            self._threads.append(t)
        return self

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=3)

    def run_forever(self):
        self.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
