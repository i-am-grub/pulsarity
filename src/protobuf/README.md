# Pulsarity Protocol Buffers

This folder contains the definition files for the protocol buffers
used by the Pulsarity application and any companion software that
integrates with it over its various communication interfaces
(http, websocket, etc). The definitation files can be used to 
generate the implementation files for any programming language 
that supports protobufs.

## Compling Python Protocol Buffers

Follow the documentation for compiling Python modules from
the protocol buffer definition files found
[here](https://protobuf.dev/getting-started/pythontutorial/#compiling-protocol-buffers)

With the protocol buffer compiler installed to your system, the command that will 
typically be used to generate the python files from the definition files will similar to:

```bash
protoc --proto_path=src/protobuf --python_out=src/pulsarity/_protobuf --pyi_out=src/pulsarity/_protobuf src/protobuf/*.proto
```

> [!NOTE]
> This also generates the associated `.pyi` files used for static type checking
