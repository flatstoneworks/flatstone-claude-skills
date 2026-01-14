#!/usr/bin/env python3
"""
Development Catalog Utility

Manage the project/skill registry in CATALOG.md.

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


def parse_entries(content):
    """Parse catalog content into structured entries"""
    entries = []
    current_category = None
    current_entry = None
    category_names = get_category_names()

    # Add special stop sections
    stop_sections = ["Quick Reference"]

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
                'stack': None,
                'github': None,
                'status': None,
                'description': None,
                'line_start': i,
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
