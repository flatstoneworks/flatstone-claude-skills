#!/usr/bin/env python3
"""
Development Catalog Utility

Manage the project/skill registry in CATALOG.md.
CATALOG.md is the single source of truth for all project data including port allocations.

Usage:
    # Show full catalog summary
    python3 catalog.py show

    # Show specific category
    python3 catalog.py show WORK

    # Add a new project (interactive)
    python3 catalog.py add

    # Update an existing entry
    python3 catalog.py update MyProject
"""

import argparse
import re
import sys
from pathlib import Path

# Import config - handle both installed and development scenarios
try:
    from config import get_config, get_catalog_file, get_categories
except ImportError:
    # Add script directory to path for development
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_catalog_file, get_categories

# Entry types
ENTRY_TYPES = ["Application", "Skill", "Library", "Tool"]

# Status options
STATUS_OPTIONS = ["Active", "WIP", "Archived"]


def load_catalog():
    """Load and parse CATALOG.md"""
    catalog_file = get_catalog_file()
    if not catalog_file.exists():
        return None
    return catalog_file.read_text()


def save_catalog(content):
    """Save content to CATALOG.md"""
    catalog_file = get_catalog_file()
    catalog_file.write_text(content)
    print(f"Saved to {catalog_file}")


def get_category_names():
    """Get list of category names from config."""
    return list(get_categories().keys())


def parse_allocated(allocated_str):
    """Parse the Allocated field into a dict.

    Format: 'frontend:3000, backend:3001, websocket:3003'
    Returns: {'frontend': 3000, 'backend': 3001, 'websocket': 3003}
    """
    if not allocated_str:
        return {}

    result = {}
    parts = allocated_str.split(',')
    for part in parts:
        part = part.strip()
        if ':' in part:
            name, port_str = part.split(':', 1)
            try:
                result[name.strip()] = int(port_str.strip())
            except ValueError:
                pass
    return result


def format_allocated(allocated_dict):
    """Format allocated dict back to string.

    Input: {'frontend': 3000, 'backend': 3001}
    Output: 'frontend:3000, backend:3001'
    """
    if not allocated_dict:
        return ""
    parts = [f"{name}:{port}" for name, port in sorted(allocated_dict.items(), key=lambda x: x[1])]
    return ", ".join(parts)


def parse_port_range(ports_str):
    """Parse port range string into (base_port, range_size).

    '3000-3009' -> (3000, 10)
    '3000' -> (3000, 10)
    """
    if not ports_str:
        return None, None

    # Remove any extra info like "(Frontend: 3000, Backend: 3001)"
    ports_str = re.sub(r'\s*\([^)]+\)', '', ports_str).strip()

    if '-' in ports_str:
        parts = ports_str.split('-')
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
            return start, end - start + 1
        except (ValueError, IndexError):
            return None, None
    else:
        try:
            return int(ports_str.strip()), 10
        except ValueError:
            return None, None


def parse_entries(content):
    """Parse catalog content into structured entries.

    Returns list of dicts with keys:
    - name, category, type, path, ports, allocated, stack, github, status, description
    - base_port, port_range (parsed from ports)
    - allocated_dict (parsed from allocated)
    """
    entries = []
    current_category = None
    current_entry = None
    category_names = get_category_names()

    # Add special stop sections
    stop_sections = ["Quick Reference", "Entry Format Reference"]

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect category headers (## CATEGORY)
        if line.startswith('## ') and not line.startswith('### '):
            section_name = line[3:].strip()

            # Check for stop sections
            if section_name in stop_sections:
                break

            # Check if it's a known category
            if section_name.upper() in [c.upper() for c in category_names]:
                current_category = section_name.upper()

        # Detect entry headers (### Name)
        elif line.startswith('### ') and current_category:
            if current_entry:
                entries.append(current_entry)

            name = line[4:].strip()
            current_entry = {
                'name': name,
                'category': current_category,
                'type': None,
                'path': None,
                'ports': None,
                'allocated': None,
                'stack': None,
                'github': None,
                'status': None,
                'description': None,
                'line_start': i,
                'base_port': None,
                'port_range': None,
                'allocated_dict': {},
            }

        # Parse table properties
        elif current_entry and line.startswith('| '):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) == 2:
                key, value = parts[0].lower(), parts[1]
                if key == 'type':
                    current_entry['type'] = value
                elif key == 'path':
                    current_entry['path'] = value.strip('`')
                elif key == 'ports':
                    current_entry['ports'] = value
                    base, range_size = parse_port_range(value)
                    current_entry['base_port'] = base
                    current_entry['port_range'] = range_size
                elif key == 'allocated':
                    current_entry['allocated'] = value
                    current_entry['allocated_dict'] = parse_allocated(value)
                elif key == 'stack':
                    current_entry['stack'] = value
                elif key == 'github':
                    current_entry['github'] = value
                elif key == 'status':
                    current_entry['status'] = value
                elif key == 'command':
                    current_entry['command'] = value

        i += 1

    # Don't forget the last entry
    if current_entry:
        entries.append(current_entry)

    return entries


def get_all_entries():
    """Get all parsed entries from CATALOG.md.

    This is the main API for other modules to access catalog data.
    """
    content = load_catalog()
    if not content:
        return []
    return parse_entries(content)


def get_entry_by_name(name):
    """Get a specific entry by name (case-insensitive)."""
    entries = get_all_entries()
    for entry in entries:
        if entry['name'].lower() == name.lower():
            return entry
    return None


def get_all_allocated_ports():
    """Get all allocated ports across all projects.

    Returns list of dicts: {'port': int, 'name': str, 'project': str, 'category': str}
    """
    entries = get_all_entries()
    ports = []

    for entry in entries:
        project_name = entry['name']
        category = entry['category']

        for alloc_name, port in entry.get('allocated_dict', {}).items():
            ports.append({
                'port': port,
                'name': alloc_name,
                'project': project_name,
                'category': category,
            })

    return sorted(ports, key=lambda x: x['port'])


def update_entry_allocated(entry_name, allocated_dict):
    """Update the Allocated field for an entry.

    Args:
        entry_name: Name of the entry to update
        allocated_dict: New allocated dict {'frontend': 3000, ...}

    Returns True on success, False on failure.
    """
    content = load_catalog()
    if not content:
        return False

    entries = parse_entries(content)
    entry = None
    for e in entries:
        if e['name'].lower() == entry_name.lower():
            entry = e
            break

    if not entry:
        return False

    allocated_str = format_allocated(allocated_dict)

    # Find and update the Allocated line
    lines = content.split('\n')

    # Look for existing Allocated line after the entry header
    in_entry = False
    allocated_line_idx = None
    ports_line_idx = None
    table_end_idx = None

    for i, line in enumerate(lines):
        if line.startswith('### ') and entry['name'] in line:
            in_entry = True
            continue

        if in_entry:
            if line.startswith('### ') or line.startswith('## '):
                # Next entry/section
                break
            if line.startswith('| Allocated |'):
                allocated_line_idx = i
            if line.startswith('| Ports |'):
                ports_line_idx = i
            if line.startswith('|') and 'Property' not in line and '----' not in line:
                table_end_idx = i

    if allocated_line_idx is not None:
        # Update existing line
        lines[allocated_line_idx] = f"| Allocated | {allocated_str} |"
    elif ports_line_idx is not None:
        # Insert after Ports line
        lines.insert(ports_line_idx + 1, f"| Allocated | {allocated_str} |")
    else:
        # Couldn't find right place
        return False

    new_content = '\n'.join(lines)
    catalog_file = get_catalog_file()
    catalog_file.write_text(new_content)
    return True


def format_entry_summary(entry):
    """Format a single entry for display"""
    name = entry['name']
    entry_type = entry.get('type') or '?'
    status = entry.get('status') or '?'
    ports = entry.get('ports') or '-'

    # Truncate long values
    if len(name) > 20:
        name = name[:17] + "..."
    if len(ports) > 15:
        ports = ports[:12] + "..."

    # Status emoji
    status_emoji = {
        'Active': '',
        'WIP': '',
        'Archived': ''
    }.get(status, '')

    return f"  {status_emoji} {name:20s} {entry_type:12s} {ports:15s} {status}"


def cmd_show(args):
    """Show catalog summary"""
    content = load_catalog()
    if not content:
        catalog_file = get_catalog_file()
        print(f"CATALOG.md not found at {catalog_file}")
        print("Run the setup script to initialize your workspace.")
        return

    entries = parse_entries(content)
    category_names = get_category_names()

    if args.category:
        # Filter by category
        category = args.category.upper()
        if category not in [c.upper() for c in category_names]:
            print(f"Unknown category: {category}")
            print(f"Valid categories: {', '.join(category_names)}")
            return

        entries = [e for e in entries if e['category'].upper() == category]
        print(f"\n  {category}")
        print("  " + "=" * 60)
    else:
        print("\n  DEVELOPMENT CATALOG")
        print("  " + "=" * 60)

    # Group by category
    by_category = {}
    for entry in entries:
        cat = entry['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(entry)

    # Display
    for category in category_names:
        cat_upper = category.upper()
        if cat_upper not in [c.upper() for c in by_category.keys()]:
            continue

        # Find matching category (case-insensitive)
        matching_cat = next((c for c in by_category.keys() if c.upper() == cat_upper), None)
        if not matching_cat:
            continue

        if not args.category:
            print(f"\n  {category}")
            print("  " + "-" * 50)

        print(f"  {'Name':20s} {'Type':12s} {'Ports':15s} Status")
        print("  " + "-" * 50)

        for entry in by_category[matching_cat]:
            print(format_entry_summary(entry))

    # Summary stats
    total = len(entries)
    active = len([e for e in entries if e.get('status') == 'Active'])
    wip = len([e for e in entries if e.get('status') == 'WIP'])

    print()
    print("  " + "-" * 50)
    print(f"  Total: {total} | Active: {active} | WIP: {wip}")
    print()


def cmd_add(args):
    """Add a new entry interactively"""
    categories = get_categories()
    category_names = list(categories.keys())

    print("\n  ADD NEW ENTRY")
    print("  " + "=" * 40)

    try:
        # Get category
        print(f"\n  Categories: {', '.join(category_names)}")
        category = input("  Category: ").strip().upper()
        if category not in [c.upper() for c in category_names]:
            print(f"  Invalid category. Must be one of: {', '.join(category_names)}")
            return

        # Get name
        name = input("  Name: ").strip()
        if not name:
            print("  Name is required.")
            return

        # Get type
        print(f"\n  Types: {', '.join(ENTRY_TYPES)}")
        entry_type = input("  Type [Application]: ").strip() or "Application"

        # Get path (optional)
        path = input("  Path (optional): ").strip()

        # Get ports (optional)
        ports = input("  Ports (e.g., 3000-3009): ").strip()

        # Get allocated (optional, auto-generate if ports provided)
        if ports:
            base_port, _ = parse_port_range(ports)
            if base_port:
                default_allocated = f"frontend:{base_port}, backend:{base_port + 1}"
                allocated = input(f"  Allocated [{default_allocated}]: ").strip() or default_allocated
            else:
                allocated = input("  Allocated (e.g., frontend:3000, backend:3001): ").strip()
        else:
            allocated = ""

        # Get stack (optional)
        stack = input("  Stack (comma-separated): ").strip()

        # Get GitHub (optional)
        github = input("  GitHub URL (optional): ").strip()

        # Get status
        print(f"\n  Status: {', '.join(STATUS_OPTIONS)}")
        status = input("  Status [WIP]: ").strip() or "WIP"

        # Get description
        description = input("  Description: ").strip()

        # Generate markdown
        entry_md = f"""
### {name}
| Property | Value |
|----------|-------|
| Type | {entry_type} |"""

        if path:
            entry_md += f"\n| Path | `{path}` |"
        if ports:
            entry_md += f"\n| Ports | {ports} |"
        if allocated:
            entry_md += f"\n| Allocated | {allocated} |"
        if stack:
            entry_md += f"\n| Stack | {stack} |"
        if github:
            entry_md += f"\n| GitHub | {github} |"

        entry_md += f"\n| Status | {status} |"

        if description:
            entry_md += f"\n\n{description}"

        entry_md += "\n\n---\n"

        print("\n  Generated entry:")
        print("  " + "-" * 40)
        for line in entry_md.split('\n'):
            print(f"  {line}")

        confirm = input("\n  Add this entry? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("  Cancelled.")
            return

        # Insert into catalog
        content = load_catalog()

        # Find the category section and insert after its header
        pattern = rf'^## {category}\n\*[^*]+\*\n'
        match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

        if match:
            insert_pos = match.end()
            new_content = content[:insert_pos] + entry_md + content[insert_pos:]
            save_catalog(new_content)
            print(f"\n  Added '{name}' to {category}!")
        else:
            print(f"  Could not find {category} section in catalog.")

    except KeyboardInterrupt:
        print("\n  Cancelled.")


def cmd_update(args):
    """Update an existing entry"""
    content = load_catalog()
    if not content:
        print("CATALOG.md not found!")
        return

    entries = parse_entries(content)

    # Find the entry
    name = args.name
    entry = None
    for e in entries:
        if e['name'].lower() == name.lower():
            entry = e
            break

    if not entry:
        print(f"Entry '{name}' not found.")
        print("\nAvailable entries:")
        for e in entries:
            print(f"  - {e['name']} ({e['category']})")
        return

    catalog_file = get_catalog_file()
    print(f"\n  UPDATE: {entry['name']}")
    print("  " + "=" * 40)
    print(f"  Category: {entry['category']}")
    print(f"  Type: {entry.get('type', '-')}")
    print(f"  Status: {entry.get('status', '-')}")
    print(f"  Ports: {entry.get('ports', '-')}")
    print(f"  Allocated: {entry.get('allocated', '-')}")
    print()
    print("  To update, edit CATALOG.md directly at line", entry['line_start'] + 1)
    print(f"  File: {catalog_file}")


def cmd_list(args):
    """List all entries"""
    content = load_catalog()
    if not content:
        print("CATALOG.md not found!")
        return

    entries = parse_entries(content)

    print("\n  ALL ENTRIES")
    print("  " + "=" * 40)

    for entry in entries:
        status_emoji = {
            'Active': '',
            'WIP': '',
            'Archived': ''
        }.get(entry.get('status', ''), '')

        print(f"  {status_emoji} {entry['category']:12s} / {entry['name']}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Development Catalog Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # show
    show_parser = subparsers.add_parser('show', help='Show catalog summary')
    show_parser.add_argument('category', nargs='?', help='Filter by category')

    # add
    subparsers.add_parser('add', help='Add a new entry (interactive)')

    # update
    update_parser = subparsers.add_parser('update', help='Update an existing entry')
    update_parser.add_argument('name', help='Name of the entry to update')

    # list
    subparsers.add_parser('list', help='List all entries')

    args = parser.parse_args()

    if args.command == 'show':
        cmd_show(args)
    elif args.command == 'add':
        cmd_add(args)
    elif args.command == 'update':
        cmd_update(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command is None:
        # Default to show
        args.category = None
        cmd_show(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
