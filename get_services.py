import requests

CONSUL_ADDRESS = "127.0.0.1"

def discover_nodes_with_consul():
    url = f'http://{CONSUL_ADDRESS}/v1/agent/services'
    response = requests.get(url)
    services = response.json()
    nodes = []
    for service in services.values():
        if service['Service'] == 'bookstore-node':
            nodes.append(service['Address'])
    return nodes