import sys
import consul
# import multiprocessing
# import subprocess
import configparser
# import random
from pnode import Pnode
from util import generate_valid_node_port, generate_valid_proccess_port

class InteractiveNode:
    def __init__(self, master, node_ip):
        self.pnodes = []
        self.consul_client = consul.Consul(
            host=master,
            dc="bookstore-data-center"
        )
        self.node_id = self.get_nr_of_nodes() + 1
        self.ip = node_ip
        # node_port = generate_valid_node_port()
        # self.node = Pnode(
        #     node_id=self.node_id,
        #     # service_name="bookstore-node",
        #     # service_port=node_port,
        #     host=self.ip
        #     cl=self.consul_client
        # )
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
            service_name = f"{self.node_id}-PS{i+1}"
            pnode = Pnode(
                id=service_name,
                cl=self.consul_client,
                host=self.ip
            )
            pnodes.append(pnode)

            # processes.append(multiprocessing.Process(target=self.start_node))
        for pnode in pnodes:
            pnode.start()

    def get_all_nodes(self):
        services = self.consul_client.agent.services()
        bookstore_services = [service for service in services.values() if service['Service'].startswith('bookstore-node')]
        nodes = [{'node_id': service['ID'], 'host': service['Address'], 'port': service['Port']} for service in bookstore_services]
        return nodes
    
    def get_nr_of_nodes(self):
        return len(self.get_all_nodes())

if __name__ == "__main__":
    # id = random.randint(0, 1000)
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    nodeface = InteractiveNode(
        master=config.get('ipconf', 'master')
        node_ip=config.get('ipconf', 'client')
    )

    while True:
        cmd = input("> ")
        if cmd == "quit" or cmd == "q":
            nodeface.node.stop()
            break

        nodeface.parse_cmd(cmd)