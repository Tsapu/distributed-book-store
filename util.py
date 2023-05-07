import socket
import random
from contextlib import closing
   
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, int(port))) == 0:
            return True
        else:
            return False

# Nodes use the range of 8500 to 8600
def generate_valid_node_port():
    # generate a random port 
    while True:
        node_port = random.randint(8500, 8600)
        if check_socket("localhost", node_port):
            continue
        else:
            break
    return node_port

# Processes use the range from 8600 to 8900
def generate_valid_proccess_port():
    # generate a random port 
    while True:
        node_port = random.randint(8600, 8900)
        if check_socket("localhost", node_port):
            continue
        else:
            break
    return node_port