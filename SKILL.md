---
name: port-scanner
description: Shows which localhost ports are in use and what processes are using them.
version: 0.1.0
license: Apache-2.0
---

# port-scanner

A localhost port scanner that shows which ports are currently in use, along with the PID, process name, and protocol (TCP/UDP) for each listening socket.

## Usage

```
./scripts/run.sh [OPTIONS]
```

## Options

| Flag | Description |
|------|-------------|
| `--range START-END` | Scan a specific port range (default: all listening ports) |
| `--common` | Scan only well-known ports 1-1024 |
| `--format text\|json` | Output format: human-readable table or JSON (default: text) |
| `--help` | Show usage information and exit |

## Output

### Text mode (default)

Displays a table with columns:

- **Proto** - TCP or UDP
- **Port** - The port number
- **PID** - Process ID of the listener
- **Process** - Name of the process

### JSON mode

Returns a JSON object with a `ports` array. Each entry contains `proto`, `port`, `pid`, and `process` fields.

## Platform Support

- **macOS** - Uses `lsof -i -P -n` to enumerate listening sockets.
- **Linux** - Uses `ss -tlnp` and `ss -ulnp` to enumerate listening sockets.

## Examples

```bash
# Show all listening ports
./scripts/run.sh

# Show only well-known ports as JSON
./scripts/run.sh --common --format json

# Show ports in a specific range
./scripts/run.sh --range 3000-9000
```
