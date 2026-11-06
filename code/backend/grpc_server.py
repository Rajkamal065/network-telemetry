"""gRPC server: the entry point where agents push their measurements."""
from concurrent import futures

import grpc

from telemetry.protoloader import pb2, pb2_grpc


class TelemetryServicer(pb2_grpc.TelemetryServicer):
    def __init__(self, ingestor):
        self.ingestor = ingestor

    def Stream(self, request_iterator, context):
        accepted = rejected = 0
        try:
            for metric in request_iterator:
                if self.ingestor.submit(metric):
                    accepted += 1
                else:
                    rejected += 1
        except grpc.RpcError:
            pass  # client went away; that is normal
        return pb2.Ack(accepted=accepted, rejected=rejected)

    def Publish(self, request, context):
        accepted = rejected = 0
        for metric in request.metrics:
            if self.ingestor.submit(metric):
                accepted += 1
            else:
                rejected += 1
        return pb2.Ack(accepted=accepted, rejected=rejected)


def create_grpc_server(ingestor, host="0.0.0.0", port=50051, max_workers=32):
    """Build (not start) the server. Returns (server, bound_port)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    pb2_grpc.add_TelemetryServicer_to_server(TelemetryServicer(ingestor), server)
    bound = server.add_insecure_port(f"{host}:{port}")
    if bound == 0:
        raise RuntimeError(f"could not bind gRPC port {port} (already in use?)")
    return server, bound
