import sys
import random
import time
import json
import consul
# import multiprocessing
import subprocess
import atexit
import configparser
from ipaddress import ip_address
from pnode import Pnode
from util import generate_valid_node_port

class InteractiveNode:
    def __init__(self, master, node_ip):
        self.master = master
        self.ip = node_ip

        self.pnodes = []
        self.dc = "bookstore-data-center"
        self.pname = "bookstore-node"

        self.consul_client = consul.Consul(
            #host=ip_address(master),
            host=self.master,
            dc=self.dc,
        )
        self.node_id = self.get_nr_of_nodes() + 1
        self.kv = self.consul_client.kv

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
            pnodes = self.get_all_pnodes()
            for pnode in pnodes: print(pnode)

        elif cmd == "ls":
            nodes = self.get_all_nodes()
            for node in nodes: print(node)
        
        elif cmd == "chain":
            self.create_replication_chain()

        elif cmd == "ls-chain":
            self.list_chain()
    
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
        bookstore_services = [service for service in services.values() if service['Service'].startswith(self.pname)]
        # print(bookstore_services)
        nodes = [{'id': service['ID'], 'host': service['Address'], 'port': service['Port'], 'meta': service['Meta'], 'tags': service['Tags']} for service in bookstore_services]
        return nodes
    
    def get_nr_of_pnodes(self):
        return len(self.get_all_pnodes())

    def get_all_nodes(self):
        nodes = self.consul_client.catalog.nodes()[1]
        node_list = []
        for node in nodes:
            node_list.append({'node': node['Node'], 'dc': node['Datacenter'], 'host': node['Address']})
        return node_list
    
    def get_nr_of_nodes(self):
        return len(self.get_all_nodes())

    def create_replication_chain(self):
        chain_key = "replication-chain"
        # Check if chain already exists
        # kv = self.consul_client.kv
        chain_exists = self.kv.get(chain_key)[1] is not None
        if chain_exists:
            return "Chain already exists"
        
        # Get ALL active nodes for the given service in the datacenter
        service_pnodes = self.consul_client.catalog.service(self.pname, dc=self.dc)[1]

        if not service_pnodes:
            print("No active pnodes found for service: ", self.pname)
            return

        # Shuffle the list of nodes to randomize the selection
        random.shuffle(service_pnodes)

        # Select a random head and tail for the chain
        head = tail = random.choice(service_pnodes)

        # Create the chain by selecting a random successor for each node
        chain = []
        visited = set()
        while True:
            chain.append(tail)
            visited.add(tail['ServiceID'])
            successors = [pnode for pnode in service_pnodes if pnode['ServiceID'] != tail['ServiceID'] and pnode['ServiceID'] not in visited]
            if not successors:
                break
            tail = random.choice(successors)
        
        meta_data = {}
        for i, pnode in enumerate(chain):
            pnode['ServiceTags'] = ['replica']
            if i == 0:
                meta_data['PredecessorID'] = None
                pnode['ServiceTags'] = ['head']
            else:
                meta_data['PredecessorID'] = chain[i-1]['ServiceID']
                
            if i == len(chain)-1:
                meta_data['SuccessorID'] = None
                pnode['ServiceTags'] = ['tail']
            else:
                meta_data['SuccessorID'] = chain[i+1]['ServiceID']      

            # Register the pnode with its updated metadata
            service_id = pnode['ServiceID']
            service_address = pnode['Address']
            service_port = pnode['ServicePort']
            service_tags = pnode['ServiceTags']
            check = consul.Check.tcp(service_address, service_port, interval="10s", timeout="1s")
            self.consul_client.agent.service.register(name=self.pname, service_id=service_id, address=service_address, port=service_port, tags=service_tags, check=check, meta = meta_data)

        # Store the chain in the KV store
        chain_data = json.dumps(chain)
        # kv.put(chain_key, chain_data)

    def list_chain(self):
        pnodes = self.get_all_pnodes()
        chain = []

        head = list(filter(lambda pnode: "head" in pnode['tags'], pnodes))
        if len(head) == 0:
            print("No head found")
            return
        else: head = head[0]
        print(head)
        chain.append(f"{head['id']}(head)")
        while len(chain) < len(pnodes):
            for pnode in pnodes:
                if pnode['meta']['PredecessorID'] == head['id']:
                    chain.append(pnode['id'])
                    head = pnode
                    break
        chain[-1] = chain[-1] + "(tail)"
        print("\nChain:")
        print("---")
        print(" -> ".join(chain))
        print("---")

        # for pnode in pnodes:
        #     if "head" in pnode['tags']:
        #         next = pnode['meta']['SuccessorID']
        #         break

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
    # try:
    consul_proc = subprocess.Popen(["consul", "agent", "--retry-join", str(master_ip), "--bind", "0.0.0.0", "--advertise", str(node_ip), "--datacenter", "bookstore-data-center", "--data-dir", "./.consul", "-node", f"Node-{nodeface.node_id}", "--disable-host-node-id"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    @atexit.register
    def stop_consul_agent():
        consul_proc.terminate()

    nodeface.node_id = 1
    # 

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