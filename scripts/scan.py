#!/usr/bin/env python3
"""Localhost port scanner - shows listening ports with PID and process info."""

import json
import platform
import re
import subprocess
import sys


def usage():
    print("""Usage: run.sh [OPTIONS]

Options:
  --range START-END   Scan a specific port range (e.g. 3000-9000)
  --common            Scan only well-known ports 1-1024
  --format text|json  Output format (default: text)
  --help              Show this help message""")


def parse_args(argv):
    opts = {"format": "text", "range_start": None, "range_end": None}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--help":
            usage()
            sys.exit(0)
        elif arg == "--common":
            opts["range_start"] = 1
            opts["range_end"] = 1024
        elif arg == "--range":
            i += 1
            if i >= len(argv):
                print("Error: --range requires START-END argument", file=sys.stderr)
                sys.exit(1)
            parts = argv[i].split("-")
            if len(parts) != 2:
                print("Error: --range format must be START-END", file=sys.stderr)
                sys.exit(1)
            opts["range_start"] = int(parts[0])
            opts["range_end"] = int(parts[1])
        elif arg == "--format":
            i += 1
            if i >= len(argv):
                print("Error: --format requires text|json argument", file=sys.stderr)
                sys.exit(1)
            if argv[i] not in ("text", "json"):
                print("Error: --format must be text or json", file=sys.stderr)
                sys.exit(1)
            opts["format"] = argv[i]
        else:
            print(f"Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)
        i += 1
    return opts


def scan_macos():
    """Use lsof to find listening ports on macOS."""
    entries = []
    try:
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n", "-sTCP:LISTEN"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().splitlines()[1:]:
            cols = line.split()
            if len(cols) < 9:
                continue
            process = cols[0]
            pid = cols[1]
            # Name field is last, like *:8080 or 127.0.0.1:3000
            name_field = cols[8]
            match = re.search(r":(\d+)$", name_field)
            if match:
                port = int(match.group(1))
                entries.append({"proto": "TCP", "port": port, "pid": pid, "process": process})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Also check UDP with a separate lsof call
    try:
        result = subprocess.run(
            ["lsof", "-iUDP", "-P", "-n"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().splitlines()[1:]:
            cols = line.split()
            if len(cols) < 9:
                continue
            process = cols[0]
            pid = cols[1]
            name_field = cols[8]
            match = re.search(r":(\d+)$", name_field)
            if match:
                port = int(match.group(1))
                entries.append({"proto": "UDP", "port": port, "pid": pid, "process": process})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return entries


def scan_linux():
    """Use ss to find listening ports on Linux."""
    entries = []
    for proto, flag in [("TCP", "-tlnp"), ("UDP", "-ulnp")]:
        try:
            result = subprocess.run(
                ["ss", flag], capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.strip().splitlines()[1:]:
                cols = line.split()
                if len(cols) < 5:
                    continue
                local = cols[3] if proto == "TCP" else cols[3]
                match = re.search(r":(\d+)$", local)
                if not match:
                    continue
                port = int(match.group(1))
                pid_str = ""
                proc_str = ""
                # The process info is in the last column, like users:(("node",pid=1234,fd=5))
                for col in cols:
                    pm = re.search(r'\("([^"]+)",pid=(\d+)', col)
                    if pm:
                        proc_str = pm.group(1)
                        pid_str = pm.group(2)
                        break
                entries.append({"proto": proto, "port": port, "pid": pid_str or "-", "process": proc_str or "-"})
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    return entries


def scan_ports():
    """Dispatch to platform-specific scanner."""
    system = platform.system()
    if system == "Darwin":
        return scan_macos()
    elif system == "Linux":
        return scan_linux()
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)
        sys.exit(1)


def filter_ports(entries, opts):
    """Filter entries by port range if specified."""
    if opts["range_start"] is not None and opts["range_end"] is not None:
        lo, hi = opts["range_start"], opts["range_end"]
        entries = [e for e in entries if lo <= e["port"] <= hi]
    # Deduplicate by (proto, port, pid)
    seen = set()
    unique = []
    for e in entries:
        key = (e["proto"], e["port"], e["pid"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    unique.sort(key=lambda e: (e["port"], e["proto"]))
    return unique


def format_text(entries):
    """Format as a human-readable table."""
    header = f"{'Proto':<6} {'Port':>6}  {'PID':>8}  {'Process'}"
    sep = "-" * 50
    lines = [header, sep]
    for e in entries:
        lines.append(f"{e['proto']:<6} {e['port']:>6}  {e['pid']:>8}  {e['process']}")
    if not entries:
        lines.append("(no listening ports found)")
    return "\n".join(lines)


def format_json(entries):
    """Format as JSON."""
    return json.dumps({"ports": entries}, indent=2)


def main():
    opts = parse_args(sys.argv[1:])
    entries = scan_ports()
    entries = filter_ports(entries, opts)
    if opts["format"] == "json":
        print(format_json(entries))
    else:
        print(format_text(entries))


if __name__ == "__main__":
    main()
