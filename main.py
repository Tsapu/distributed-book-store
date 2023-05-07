import sys
import consul
import multiprocessing
from node import Node
from util import generate_valid_node_port, generate_valid_proccess_port

class InteractiveNode:
    def __init__(self):
        self.processes = []
        node_port = generate_valid_node_port()
        self.node = Node(node_id=f"node-{node_port}", service_name="bookstore-node", service_port=node_port)
        self.node.start()

    def parse_cmd(self, cmd):
        if cmd.startswith("ps"): #and len(cmd.split()) == 2:
            if len(cmd.split()) != 2:
                print("Please specify the number of processes to create.")
                return
            nr_of_processes = cmd.split(" ")[1]
            print(f"Creating {nr_of_processes} local store processes...")
            return
        elif cmd == "get_nodes":
            print(self.get_all_nodes())
    
    def create_processes(self, nr_of_processes):
        for i in range(nr_of_processes):
            proccess_port = generate_valid_proccess_port()
            processes.append(multiprocessing.Process(target=self.start_node))
        for process in processes:
            process.start()

    def get_all_nodes(self):
        services = self.node.consul_client.agent.services()
        bookstore_services = [service for service in services.values() if service['Service'].startswith('bookstore-node')]
        nodes = [{'node_id': service['ID'], 'host': service['Address'], 'port': service['Port']} for service in bookstore_services]
        return nodes

if __name__ == "__main__":

    nodeface = InteractiveNode()

    while True:
        cmd = input("> ")
        if cmd == "quit" or cmd == "q":
            nodeface.node.stop()
            break

        nodeface.parse_cmd(cmd)