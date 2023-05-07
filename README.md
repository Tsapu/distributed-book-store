# Distributed book store
Mini-project 2: Building a distributed online book store with underlying chain replication LTAT.06.007

**Authors:** Davis Krumins

### Node discovery

Node discovery is achieved with Consul


## How to run

### Requirements
1. Consul
2. Python modules:
- python-consul
- grpcio
- grpcio-tools

First generate the gRPC python files:
```
python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. bookstore.proto
```

## How to run

1. Generate consul secret:
```
docker run consul:latest keygen
```
then fill in the secret in the config.json file, where you also need to specify your host IP address.

2. Start the master node:
```
consul agent --server --config-file consul_conf.json
python3 main.py
```
3. To join other nodes:
```
consul agent --retry-join=<master-node-ip> --bind=0.0.0.0 --advertise=<node-ip> --datacenter="bookstore-data-center" --encrypt=aPLfonbTEhvMnu1XYPBq3puInLPfic0ilO4mnqmT4I8= --data-dir=/var/consul
python3 main.py
```

```
consul agent --retry-join=172.20.10.4 --bind=0.0.0.0 --advertise=192.168.56.10 --datacenter="bookstore-data-center" --encrypt=aPLfonbTEhvMnu1XYPBq3puInLPfic0ilO4mnqmT4I8= --data-dir=/var/consul
python3 main.py
```

```
consul agent --dev --client=0.0.0.0

# consul agent --dev --bind=0.0.0.0 --advertise=172.20.10.4
```

Join the cluster on the other nodes:
1. Change the host (...)
2.  ```
	python main.py
	```
