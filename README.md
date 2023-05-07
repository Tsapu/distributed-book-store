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

Start the Consul agent which will allow nodes to dynamically discover each other:
```
consul agent -dev
```
