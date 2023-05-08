import consul
import grpc
import threading
from concurrent import futures
from bookstore_pb2_grpc import add_BookstoreServicer_to_server, add_HealthServicer_to_server
from bookstore_pb2_grpc import BookstoreServicer, HealthServicer
# from bookstore_pb2_grpc import BookstoreServicer
from bookstore_pb2 import Book

from util import generate_valid_node_port, generate_valid_proccess_port


class HealthServicer(HealthServicer):

    def Check(self, request, context):
        return bookstore_pb2.HealthCheckResponse(healthy=True)

class Pnode:
    def __init__(self, id, cl, host="localhost"):
        self.id = id
        self.cl = cl
        self.host = host
        self.register_process()

        self.server = None
    
    def register_process(self):
        self.port = generate_valid_proccess_port()
        self.cl.agent.service.register(
            name="bookstore-node",
            service_id=self.id,
            address=self.host,
            port=self.port,
            check=consul.Check.tcp(self.host, self.port, interval="10s", timeout="1s")
        )
        return True
        
    # def register_process(self):
    #     # for i in range(x):
    #     # Register the gRPC service with Consul
    #     # service_name = f"{self.node_id}-PS{i+1}"
    #     service_port = generate_valid_proccess_port()
    #     self.cl.agent.service.register(
    #         name=service_name,
    #         service_id=service_name,
    #         address=self.host,
    #         port=service_port,
    #         check=consul.Check.tcp(self.host, service_port, interval="10s", timeout="1s")
    #     )

        # Start the gRPC process server
        # process_thread = threading.Thread(target=self._start_server)
        # process_thread.start()
        # self._start_server()

    def start(self):
        # Start the gRPC process server
        process_thread = threading.Thread(target=self._start_server)
        process_thread.start()

    def _start_server(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_BookstoreServicer_to_server(BookstoreServicer(), server)
        add_HealthServicer_to_server(HealthServicer(), server)
        server.add_insecure_port(f'[::]:{self.port}')
        server.start()
        print(f"{self.id} listening on port {self.port}...")
        self.server = server # ref for stop
        self.server.wait_for_termination()

        # Deregister the service from Consul
        self.cl.agent.service.deregister(self.id)

    def stop(self):
        if self.server is not None:
            self.server.stop(0)
        return


if __name__ == "__main__":

    node = Pnode(id="node-1", service_name="bookstore-node", service_port=8510)
    node.start()



# c.agent.service.register(
#     name=service_name,
#     service_id=service_id,
#     address=service_address,
#     port=service_port,
#     check=consul.Check.http(f"http://{service_address}:{service_port}/health", interval="10s")
# )
