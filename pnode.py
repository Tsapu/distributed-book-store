import consul
import grpc
import threading
import time
from concurrent import futures
# import multiprocessing
from bookstore_pb2_grpc import add_BookstoreServicer_to_server, add_HealthServicer_to_server
from bookstore_pb2_grpc import BookstoreServicer, HealthServicer
# from bookstore_pb2_grpc import BookstoreServicer
import bookstore_pb2
from bookstore_pb2 import Book

from util import generate_valid_node_port, generate_valid_proccess_port

books = {
    "The Hitchhiker's Guide to the Galaxy": 42.0,
    "The Great Gatsby": 10.0,
    "Thirst": 15.0,
}

def trigger_propogation(self, successor):
    with grpc.insecure_channel(f"{successor['host']}:{successor['port']}") as channel:
        stub = bookstore_pb2_grpc.BookstoreStub(channel)
        for book in books:
            res = stub.AddBook(bookstore_pb2.Book(title=book.name, price=float(book.price)))

class HealthServicer(HealthServicer):
    def Check(self, request, context):
        return bookstore_pb2.HealthCheckResponse(healthy=True)

class BookstoreServicer(BookstoreServicer):

    def AddBook(self, request, context):
        
        books[request.title] = request.price
        for key, value in context.invocation_metadata():
            if key == 'successor':
                successor_id = value
        # Propogate stuff:
        # trigger_propogation(successor)

        return bookstore_pb2.AddBookResponse()
    
    def GetBook(self, request, context):
        if request.title in books:
            return Book(success=True, title=request.title, price=books[request.title])
            # Propogate stuff:
            # trigger_propogation(successor)
        else:
            return Book(success=False)
    
    def ListBooks(self, request, context):
        books_list = []
        for name, price in books.items():
            books_list.append(Book(title=name, price=price))
        response = bookstore_pb2.ListBooksResponse(books=books_list)
        # Propogate stuff:
        # trigger_propogation(successor)
        return response

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

    def get_successor(self):
        services = self.cl.agent.services()
        bookstore_services = [service for service in services.values() if service['Service'].startswith("bookstore-node")]
        # print(bookstore_services)
        pnodes = [{'id': service['ID'], 'host': service['Address'], 'port': service['Port'], 'meta': service['Meta'], 'tags': service['Tags']} for service in bookstore_services]
        
        # Find successor from the meta data:
        successor = list(filter(lambda pnode: pnode['meta']['PredecessorID'] == self.id, pnodes))
        if len(successor) == 0:
            print("No successor found")
            return None
        else:
            return successor[0]



if __name__ == "__main__":

    node = Pnode(id="node-1", service_name="bookstore-node", service_port=8510)
    node.start()