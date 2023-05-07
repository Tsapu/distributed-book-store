import sys
import consul
# import multiprocessing
import subprocess
import atexit
import configparser
from ipaddress import ip_address
# import random
from pnode import Pnode
from util import generate_valid_node_port

class InteractiveNode:
    def __init__(self, master, node_ip):
        # if ip_address(master) == "127.0.0.1":
        #     print("SAME")
        # else: print(False)
        # print(master)
        # print("127.0.0.1")
        self.pnodes = []
        self.consul_client = consul.Consul(
            #host=ip_address(master),
            host=master,
            dc="bookstore-data-center",
        )
        self.node_id = self.get_nr_of_nodes()
        self.ip = node_ip
        # node_port = generate_valid_node_port()
        # self.node = Pnode(
        #     node_id=self.node_id,
        #     # service_name="bookstore-node",
        #     # service_port=node_port,
        #     host=self.ip
        #     cl=self.consul_client
        # )
        # self.node.start()

    def parse_cmd(self, cmd):
        if cmd.startswith("init"): #and len(cmd.split()) == 2:
            if len(cmd.split()) != 2:
                print("Please specify the number of processes to create.")
                return
            nr_of_processes = cmd.split(" ")[1]
            print(f"Creating {nr_of_processes} local store processes...")

            self.create_processes(int(nr_of_processes))
            self.start_all_pnodes()
            
        elif cmd == "ps":
            print(self.get_all_pnodes())
    
    def create_processes(self, nr_of_processes):

        for i in range(nr_of_processes):
            service_name = f"Node{self.node_id}-PS{i+1}"
            pnode = Pnode(
                id=service_name,
                cl=self.consul_client,
                host=self.ip
            )
            self.pnodes.append(pnode)

    def get_all_pnodes(self):
        services = self.consul_client.agent.services()
        bookstore_services = [service for service in services.values() if service['Service'].startswith('bookstore-node')]
        nodes = [{'id': service['ID'], 'host': service['Address'], 'port': service['Port']} for service in bookstore_services]
        return nodes
    
    def get_nr_of_pnodes(self):
        return len(self.get_all_pnodes())
    
    def get_nr_of_nodes(self):
        return len(self.consul_client.catalog.nodes()[1])

    def start_all_pnodes(self):
        for pnode in self.pnodes:
            pnode.start()

    def stop_all_pnodes(self):
        for pnode in self.pnodes:
            pnode.stop()

if __name__ == "__main__":
    # id = random.randint(0, 1000)
    config = configparser.ConfigParser()
    config.read('config.ini')

    master_ip = config.get('ipconf', 'master')
    node_ip = config.get('ipconf', 'client')

    nodeface = InteractiveNode(master_ip, node_ip)

    # Start the Consul agent for our node
    try:
        consul_proc = subprocess.Popen(["consul", "agent", "--retry-join", str(master_ip), "--bind", "0.0.0.0", "--advertise", str(node_ip), "--datacenter", "bookstore-data-center", "--data-dir", "./.consul", "-node", f"Node-{nodeface.node_id}", "--disable-host-node-id"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        _, stderr = process.communicate()
        # print(stderr.decode())

        @atexit.register
        def stop_consul_agent():
            consul_proc.terminate()
    except:
        # this means the master is running on this node
        print("Consul agent is already running")
        nodeface.node_id = "1"


    # master_ip = config.get('ipconf', 'master')
    # print(master_ip)
    # node_ip = config.get('ipconf', 'client')
    # print(node_ip)

    # consul_client = consul.Consul(
    #         host=master_ip,
    #         dc="bookstore-data-center"
    #     )
        
    while True:
        cmd = input(f"Node-{nodeface.node_id}> ")
        if cmd == "quit" or cmd == "q":
            nodeface.stop_all_pnodes()
            break

        nodeface.parse_cmd(cmd)