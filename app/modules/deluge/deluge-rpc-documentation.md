# Deluge RPC Documentation

Complete reference for interacting with Deluge via RPC.

## Connecting

``` python
from deluge_client import DelugeRPCClient
client = DelugeRPCClient("127.0.0.1", 58846, "username", "password")
client.connect()
```

...
