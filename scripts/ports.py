#!/usr/bin/env python3
"""
Port Management Utility

Manage ports for projects. Reads from CATALOG.md (single source of truth).

Usage:
    # Show all projects and allocations
    python3 ports.py show

    # Show specific project
    python3 ports.py show MyProject

    # Check for port conflicts
    python3 ports.py check

    # Check if a specific port is available
    python3 ports.py available 3000

    # Allocate a new port for a project
    python3 ports.py allocate MyProject websocket 3
"""

import argparse
import re
import socket
import subprocess
import sys
from pathlib import Path

# Import config and catalog - handle both installed and development scenarios
try:
    from config import get_config, get_catalog_file, get_categories, get_hostname
    from catalog import (
        get_all_entries, get_entry_by_name, get_all_allocated_ports,
        update_entry_allocated, parse_port_range, format_allocated
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_catalog_file, get_categories, get_hostname
    from catalog import (
        get_all_entries, get_entry_by_name, get_all_allocated_ports,
        update_entry_allocated, parse_port_range, format_allocated
    )


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


def get_current_project():
    """Try to determine the current project based on cwd."""
    cwd = Path.cwd()
    entries = get_all_entries()

    for entry in entries:
        if entry.get('path'):
            try:
                project_path = Path(entry['path'])
                if cwd == project_path or cwd.is_relative_to(project_path):
                    return entry
            except (ValueError, TypeError):
                pass

    # Also try matching by directory name
    for entry in entries:
        if entry['name'].lower() == cwd.name.lower():
            return entry

    return None


def cmd_show(args):
    """Show port allocations"""
    entries = get_all_entries()

    if args.project:
        # Show specific project
        entry = get_entry_by_name(args.project)
        if not entry:
            print(f"  Project '{args.project}' not found in catalog.")
            print("\n  Available projects:")
            for e in entries:
                if e.get('base_port'):
                    print(f"    - {e['name']}")
            return

        print(f"\n  Project: {entry['name']}")
        print(f"  Category: {entry['category']}")
        if entry.get('ports'):
            print(f"  Ports: {entry['ports']}")
        print()

        allocated = entry.get('allocated_dict', {})
        if allocated:
            print("  Allocated Ports:")
            for name, port in sorted(allocated.items(), key=lambda x: x[1]):
                in_use = is_port_in_use(port)
                process_info = get_port_process(port) if in_use else None
                status = "" if in_use else ""
                proc_str = format_process_info(process_info)
                print(f"    {status} {name}: {port}{proc_str}")
        else:
            print("  No ports allocated yet.")

        # Show available slots
        if entry.get('base_port') and entry.get('port_range'):
            base = entry['base_port']
            range_size = entry['port_range']
            used_offsets = set()
            for port in allocated.values():
                if base <= port < base + range_size:
                    used_offsets.add(port - base)

            available = [i for i in range(range_size) if i not in used_offsets]
            if available:
                print(f"\n  Available offsets: {available[:5]}{'...' if len(available) > 5 else ''}")

        print()
        return

    # Show current project if in a project directory
    current = get_current_project()
    if current and current.get('base_port'):
        print(f"\n  Current Project: {current['name']}")
        print(f"  Ports: {current.get('ports', '-')}")
        print()

        allocated = current.get('allocated_dict', {})
        if allocated:
            print("  Allocated Ports:")
            for name, port in sorted(allocated.items(), key=lambda x: x[1]):
                in_use = is_port_in_use(port)
                process_info = get_port_process(port) if in_use else None
                status = "" if in_use else ""
                proc_str = format_process_info(process_info)
                print(f"    {status} {name}: {port}{proc_str}")

    # Show all ports across all projects
    print()
    print("  " + "=" * 60)
    print("  All Ports (from CATALOG.md)")
    print("  " + "=" * 60)

    all_ports = get_all_allocated_ports()

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
    """Check for port conflicts"""
    if args.project:
        entry = get_entry_by_name(args.project)
        if not entry:
            print(f"  Project '{args.project}' not found.")
            return
    else:
        entry = get_current_project()
        if not entry:
            print("  Not in a project directory and no project specified.")
            print("  Usage: ports.py check [project_name]")
            return

    if not entry.get('base_port'):
        print(f"  Project '{entry['name']}' has no port range defined.")
        return

    base_port = entry['base_port']
    range_size = entry.get('port_range', 10)
    allocated = entry.get('allocated_dict', {})

    print(f"\n  Checking ports {base_port}-{base_port + range_size - 1} for {entry['name']}...")
    print()

    conflicts = 0
    for i in range(range_size):
        port = base_port + i
        allocated_name = None
        for name, p in allocated.items():
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

        # Check if it's allocated to a project
        all_ports = get_all_allocated_ports()
        for entry in all_ports:
            if entry['port'] == port:
                print(f"  Allocated to: {entry['project']} ({entry['name']})")
                break

        sys.exit(1)
    else:
        print(f"  Port {port} is available")
        sys.exit(0)


def cmd_allocate(args):
    """Allocate a new port for a project"""
    project_name = args.project
    port_name = args.name
    offset = args.offset

    entry = get_entry_by_name(project_name)
    if not entry:
        # Try current directory
        current = get_current_project()
        if current:
            entry = current
            project_name = entry['name']
        else:
            print(f"  Project '{project_name}' not found in catalog.")
            return

    if not entry.get('base_port'):
        print(f"  Project '{entry['name']}' has no port range defined.")
        return

    base_port = entry['base_port']
    range_size = entry.get('port_range', 10)
    allocated = entry.get('allocated_dict', {}).copy()

    if offset >= range_size:
        print(f"  Error: Offset {offset} is outside range (0-{range_size - 1})")
        return

    port = base_port + offset

    # Check if already allocated
    for name, p in allocated.items():
        if p == port:
            print(f"  Port {port} already allocated to '{name}'")
            return

    # Check if name already used
    if port_name in allocated:
        print(f"  Name '{port_name}' already allocated to port {allocated[port_name]}")
        return

    # Add new allocation
    allocated[port_name] = port

    # Update catalog
    if update_entry_allocated(entry['name'], allocated):
        print(f"  Allocated port {port} to '{port_name}' in {entry['name']}")
        print(f"  Updated CATALOG.md")
    else:
        print(f"  Failed to update catalog")


def cmd_find(args):
    """Find which project uses a port"""
    port = args.port

    all_ports = get_all_allocated_ports()
    for entry in all_ports:
        if entry['port'] == port:
            print(f"  Port {port} is allocated to:")
            print(f"    Project: {entry['project']}")
            print(f"    Name: {entry['name']}")
            print(f"    Category: {entry['category']}")

            in_use = is_port_in_use(port)
            if in_use:
                process_info = get_port_process(port)
                proc_str = format_process_info(process_info)
                print(f"    Status:  IN USE{proc_str}")
            else:
                print(f"    Status:  Not running")
            return

    print(f"  Port {port} is not allocated to any project")

    if is_port_in_use(port):
        process_info = get_port_process(port)
        proc_str = format_process_info(process_info)
        print(f"  But it IS in use{proc_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Port management utility (reads from CATALOG.md)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # show
    show_parser = subparsers.add_parser('show', help='Show port allocations')
    show_parser.add_argument('project', nargs='?', help='Show specific project')

    # check
    check_parser = subparsers.add_parser('check', help='Check for port conflicts')
    check_parser.add_argument('project', nargs='?', help='Project to check (default: current directory)')

    # available
    avail_parser = subparsers.add_parser('available', help='Check if a port is available')
    avail_parser.add_argument('port', type=int, help='Port number to check')

    # allocate
    alloc_parser = subparsers.add_parser('allocate', help='Allocate a new port')
    alloc_parser.add_argument('project', help='Project name')
    alloc_parser.add_argument('name', help='Name for the port (e.g., websocket)')
    alloc_parser.add_argument('offset', type=int, help='Offset from base port')

    # find
    find_parser = subparsers.add_parser('find', help='Find which project uses a port')
    find_parser.add_argument('port', type=int, help='Port number to find')

    args = parser.parse_args()

    if args.command == 'show':
        cmd_show(args)
    elif args.command == 'check':
        cmd_check(args)
    elif args.command == 'available':
        cmd_available(args)
    elif args.command == 'allocate':
        cmd_allocate(args)
    elif args.command == 'find':
        cmd_find(args)
    elif args.command is None:
        args.project = None
        cmd_show(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
