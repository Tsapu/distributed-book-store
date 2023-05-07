import consul
import grpc
import threading
from concurrent import futures
from bookstore_pb2_grpc import add_BookstoreServicer_to_server, add_HealthServicer_to_server
from bookstore_pb2_grpc import BookstoreServicer, HealthServicer
# from bookstore_pb2_grpc import BookstoreServicer
from bookstore_pb2 import Book

class HealthServicer(HealthServicer):

    def Check(self, request, context):
        return bookstore_pb2.HealthCheckResponse(healthy=True)

class Node:
    def __init__(self, node_id, service_name, service_port, host="localhost"):
        self.node_id = node_id
        self.service_name = service_name
        self.service_port = service_port
        self.consul_client = consul.Consul()

        self.host = host
        self.server = None
        
    def start(self):
        # Register the gRPC service with Consul
        self.consul_client.agent.service.register(
            name=self.service_name,
            service_id=self.node_id,
            address=self.host,
            port=self.service_port,
            check=consul.Check.tcp(self.host, self.service_port, interval="10s", timeout="1s")
        )

        # Start the gRPC server
        server_thread = threading.Thread(target=self._start_server)
        server_thread.start()
        
        # self._start_server()

    def _start_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_BookstoreServicer_to_server(BookstoreServicer(), server)
        add_HealthServicer_to_server(HealthServicer(), server)
        server.add_insecure_port(f'[::]:{self.service_port}')
        server.start()
        print(f"Node {self.node_id} listening on port {self.service_port}...")
        self.server = server # ref for stop
        self.server.wait_for_termination()

        # Deregister the service from Consul
        self.consul_client.agent.service.deregister(self.node_id)

    def stop(self):
        if self.server is not None:
            self.server.stop(0)
        return


if __name__ == "__main__":

    node = Node(node_id="node-1", service_name="bookstore-node", service_port=8510)
    node.start()



# c.agent.service.register(
#     name=service_name,
#     service_id=service_id,
#     address=service_address,
#     port=service_port,
#     check=consul.Check.http(f"http://{service_address}:{service_port}/health", interval="10s")
# )
