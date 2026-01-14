#!/usr/bin/env python3
"""
Port Management Utility

Manage ports for projects with port allocation tracking.

Usage:
    # Show all projects and allocations
    python3 ports.py show

    # Check for port conflicts
    python3 ports.py check

    # Check if a specific port is available
    python3 ports.py available 3000

    # Allocate a new port in current project
    python3 ports.py allocate api 2
"""

import argparse
import json
import re
import socket
import subprocess
import sys
from pathlib import Path

# Import config - handle both installed and development scenarios
try:
    from config import get_config, get_catalog_file, get_categories
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_catalog_file, get_categories


def load_project_config():
    """Load ports.json from current directory or return None"""
    ports_file = Path.cwd() / "ports.json"
    if ports_file.exists():
        with open(ports_file) as f:
            return json.load(f)
    return None


def save_project_config(config):
    """Save configuration to ports.json in current directory"""
    ports_file = Path.cwd() / "ports.json"
    with open(ports_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Saved to {ports_file}")


def is_port_in_use(port):
    """Check if a port is currently in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True


def get_port_process(port):
    """Get the process using a port (if any)"""
    try:
        # Try ss with process info
        result = subprocess.run(
            ['ss', '-tlnp', f'sport = :{port}'],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            line = lines[1]
            if 'users:' in line:
                match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', line)
                if match:
                    return {
                        'name': match.group(1),
                        'pid': int(match.group(2))
                    }

        # Try lsof as fallback
        result = subprocess.run(
            ['lsof', '-i', f':{port}', '-P', '-n', '-sTCP:LISTEN'],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 2:
                return {
                    'name': parts[0],
                    'pid': int(parts[1])
                }

        return None
    except Exception:
        return None


def format_process_info(process_info):
    """Format process info for display"""
    if not process_info:
        return ""
    return f" [{process_info['name']} pid={process_info['pid']}]"


def find_all_port_configs():
    """Find all ports.json files in workspace"""
    config = get_config()
    configs = []
    seen_paths = set()

    for base_dir in config.project_dirs:
        if not base_dir.exists():
            continue

        # Check immediate subdirectories
        for project_dir in base_dir.iterdir():
            if project_dir.is_dir():
                ports_file = project_dir / "ports.json"
                if ports_file.exists() and str(ports_file) not in seen_paths:
                    seen_paths.add(str(ports_file))
                    try:
                        with open(ports_file) as f:
                            cfg = json.load(f)
                            cfg['_path'] = str(ports_file)
                            configs.append(cfg)
                    except (json.JSONDecodeError, IOError):
                        pass

    return configs


def get_all_allocated_ports(config):
    """Get all allocated ports from a config"""
    ports = []
    project_name = config.get('project', 'unknown')

    for name, port in config.get('allocated', {}).items():
        ports.append({
            'port': port,
            'name': name,
            'project': project_name,
        })

    return ports


def cmd_show(args):
    """Show port allocations"""
    # Show current project if in a project directory
    project_config = load_project_config()

    if project_config:
        project_name = project_config.get('project')
        base_port = project_config.get('basePort')

        print(f"\n  Current Project: {project_name}")
        print(f"  Base Port: {base_port}")
        print(f"  Range: {base_port}-{base_port + project_config.get('range', 10) - 1}")
        print()

        print("  Allocated Ports:")
        for name, port in project_config.get('allocated', {}).items():
            in_use = is_port_in_use(port)
            process_info = get_port_process(port) if in_use else None
            status = "" if in_use else ""
            proc_str = format_process_info(process_info)
            print(f"    {status} {name}: {port}{proc_str}")

    # Show all ports across all projects
    print()
    print("  " + "=" * 60)
    print("  All Ports (All Projects)")
    print("  " + "=" * 60)

    all_configs = find_all_port_configs()
    all_ports = []

    for cfg in all_configs:
        all_ports.extend(get_all_allocated_ports(cfg))

    all_ports.sort(key=lambda x: x['port'])

    if all_ports:
        for entry in all_ports:
            in_use = is_port_in_use(entry['port'])
            process_info = get_port_process(entry['port']) if in_use else None
            status = "" if in_use else ""
            proc_str = format_process_info(process_info)
            print(f"    {status} {entry['port']:5d}  {entry['project']:25s}  {entry['name']}{proc_str}")
    else:
        print("    No ports allocated yet")

    print()


def cmd_check(args):
    """Check for port conflicts in current project"""
    config = load_project_config()

    if not config:
        print("No ports.json found in current directory.")
        print("Run 'init.py' to initialize a project.")
        return

    base_port = config.get('basePort')
    range_size = config.get('range', 10)

    print(f"\n  Checking ports {base_port}-{base_port + range_size - 1}...")
    print()

    conflicts = 0
    for i in range(range_size):
        port = base_port + i
        allocated_name = None
        for name, p in config.get('allocated', {}).items():
            if p == port:
                allocated_name = name
                break

        in_use = is_port_in_use(port)
        process_info = get_port_process(port) if in_use else None
        name_str = f" ({allocated_name})" if allocated_name else ""
        proc_str = format_process_info(process_info)

        if in_use:
            status = " IN USE"
            conflicts += 1
            print(f"    {status} {port}{name_str}{proc_str}")
        else:
            status = ""
            print(f"    {status} {port}{name_str}")

    print()
    if conflicts:
        print(f"  {conflicts} port(s) in use")
    else:
        print("  All ports available")
    print()


def cmd_available(args):
    """Check if a specific port is available"""
    port = args.port

    if is_port_in_use(port):
        process_info = get_port_process(port)
        proc_str = format_process_info(process_info)
        print(f"  Port {port} is in use{proc_str}")
        sys.exit(1)
    else:
        print(f"  Port {port} is available")
        sys.exit(0)


def cmd_allocate(args):
    """Allocate a new port in current project"""
    config = load_project_config()

    if not config:
        print("No ports.json found in current directory.")
        print("Run 'init.py' to initialize a project.")
        return

    base_port = config.get('basePort')
    range_size = config.get('range', 10)
    port = base_port + args.offset

    if args.offset >= range_size:
        print(f"Error: Offset {args.offset} is outside range (0-{range_size - 1})")
        return

    # Check if already allocated
    for name, p in config.get('allocated', {}).items():
        if p == port:
            print(f"Port {port} already allocated to '{name}'")
            return

    config['allocated'][args.name] = port
    save_project_config(config)
    print(f"Allocated port {port} to '{args.name}'")


def main():
    parser = argparse.ArgumentParser(
        description="Port management utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # show
    subparsers.add_parser('show', help='Show port allocations')

    # check
    subparsers.add_parser('check', help='Check for port conflicts')

    # available
    avail_parser = subparsers.add_parser('available', help='Check if a port is available')
    avail_parser.add_argument('port', type=int, help='Port number to check')

    # allocate
    alloc_parser = subparsers.add_parser('allocate', help='Allocate a new port')
    alloc_parser.add_argument('name', help='Name for the port')
    alloc_parser.add_argument('offset', type=int, help='Offset from base port')

    args = parser.parse_args()

    if args.command == 'show':
        cmd_show(args)
    elif args.command == 'check':
        cmd_check(args)
    elif args.command == 'available':
        cmd_available(args)
    elif args.command == 'allocate':
        cmd_allocate(args)
    elif args.command is None:
        cmd_show(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
