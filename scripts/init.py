#!/usr/bin/env python3
"""
Project Initialization Utility

Initialize a new project with port allocation and catalog registration.
This is MANDATORY when starting any new project.

Usage:
    # Interactive initialization (run from project directory)
    python3 init.py

    # Quick init with category and base port
    python3 init.py --category WORK --port 3050

    # Specify project name (defaults to current directory name)
    python3 init.py --name MyProject
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Import config - handle both installed and development scenarios
try:
    from config import get_config, get_catalog_file, get_categories, get_hostname
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config, get_catalog_file, get_categories, get_hostname

# Entry types
ENTRY_TYPES = ["Application", "Skill", "Library", "Tool"]

# Standard tech stacks
TECH_STACKS = {
    "react-fastapi": "React 18, TypeScript, Vite, TanStack Query, Tailwind CSS, FastAPI, Python",
    "react": "React 18, TypeScript, Vite, Tailwind CSS",
    "nextjs": "Next.js, React, TypeScript, Tailwind CSS",
    "fastapi": "FastAPI, Python, Pydantic",
    "express": "Express.js, Node.js, TypeScript",
    "python": "Python",
    "node": "Node.js, TypeScript",
    "custom": None,
}


def get_next_available_port(category):
    """Find the next available port range for a category by scanning CATALOG.md"""
    categories = get_categories()

    if category not in categories or categories[category].get("base") is None:
        return None

    base = categories[category]["base"]
    used_ports = set()

    # Parse CATALOG.md to find used ports
    catalog_file = get_catalog_file()
    if catalog_file.exists():
        content = catalog_file.read_text()
        # Find all port ranges like "3000-3009" or single ports like "3080"
        port_matches = re.findall(r'\b(\d{4,5})(?:-\d{4,5})?\b', content)
        for port_str in port_matches:
            port = int(port_str)
            # Round down to nearest 10 to get the base
            port_base = (port // 10) * 10
            if base <= port_base < base + 1000:  # Within category range
                used_ports.add(port_base)

    # Find next available slot
    for offset in range(0, 1000, 10):
        candidate = base + offset
        if candidate not in used_ports:
            return candidate

    # If all slots taken, go beyond
    return base + 1000


def create_ports_json(project_dir, project_name, base_port):
    """Create ports.json in the project directory"""
    ports_file = project_dir / "ports.json"

    config = {
        "project": project_name,
        "basePort": base_port,
        "range": 10,
        "allocated": {
            "frontend": base_port,
            "backend": base_port + 1
        }
    }

    with open(ports_file, 'w') as f:
        json.dump(config, f, indent=2)

    return ports_file


def add_to_catalog(name, category, entry_type, path, ports, stack, github, description):
    """Add a new entry to CATALOG.md"""
    catalog_file = get_catalog_file()
    content = catalog_file.read_text()

    # Build the entry markdown
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

    entry_md += "\n| Status | WIP |"

    if description:
        entry_md += f"\n\n{description}"

    entry_md += "\n\n---\n"

    # Find the category section and insert
    pattern = rf'^## {category}\n\*[^*]+\*\n'
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + entry_md + content[insert_pos:]
        catalog_file.write_text(new_content)
        return True
    else:
        print(f"  Could not find {category} section in CATALOG.md")
        return False


def update_quick_reference(name, category, ports):
    """Update the Quick Reference table in CATALOG.md"""
    catalog_file = get_catalog_file()
    content = catalog_file.read_text()

    # Find the Quick Reference table
    table_pattern = r'(\| Category \| Project \| Ports \|\n\|[^\n]+\n)((?:\|[^\n]+\n)*)'
    match = re.search(table_pattern, content)

    if match:
        header = match.group(1)
        rows = match.group(2)

        # Add new row
        new_row = f"| {category} | {name} | {ports} |\n"

        # Insert row
        new_rows = rows + new_row

        new_content = content[:match.start()] + header + new_rows + content[match.end():]
        catalog_file.write_text(new_content)


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new project with port allocation and catalog registration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    categories = get_categories()
    category_names = list(categories.keys())

    parser.add_argument('--name', '-n', help='Project name (defaults to current directory name)')
    parser.add_argument('--category', '-c', choices=category_names, help='Project category')
    parser.add_argument('--port', '-p', type=int, help='Base port number')
    parser.add_argument('--type', '-t', choices=ENTRY_TYPES, default='Application', help='Entry type')
    parser.add_argument('--stack', '-s', help='Tech stack (or preset: react-fastapi, react, nextjs, fastapi, express, python, node)')
    parser.add_argument('--github', '-g', help='GitHub URL')
    parser.add_argument('--description', '-d', help='Project description')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')

    args = parser.parse_args()

    # Get project directory and name
    project_dir = Path.cwd()
    project_name = args.name or project_dir.name
    hostname = get_hostname()

    print()
    print("  PROJECT INITIALIZATION")
    print("  " + "=" * 50)
    print(f"  Directory: {project_dir}")
    print(f"  Project: {project_name}")
    print()

    # Check if already initialized
    ports_file = project_dir / "ports.json"
    if ports_file.exists():
        print(f"  This project already has ports.json!")
        with open(ports_file) as f:
            existing = json.load(f)
        print(f"  Base port: {existing.get('basePort')}")
        print()
        response = input("  Reinitialize? [y/N]: ").strip().lower()
        if response != 'y':
            print("  Cancelled.")
            return
        print()

    # Get category
    if args.category:
        category = args.category
    else:
        print("  CATEGORIES:")
        for i, (cat, info) in enumerate(categories.items(), 1):
            port_info = f"(base: {info.get('base')})" if info.get('base') else "(no ports)"
            print(f"    {i}. {cat} - {info.get('description', '')} {port_info}")
        print()

        try:
            choice = input(f"  Select category [1-{len(categories)}]: ").strip()
            if not choice:
                print("  Category is required.")
                return
            idx = int(choice) - 1
            category = category_names[idx]
        except (ValueError, IndexError):
            print("  Invalid selection.")
            return

    print(f"  Category: {category}")

    # Get base port
    cat_info = categories.get(category, {})
    if cat_info.get("base") is None:
        base_port = None
        ports_str = None
        print("  Ports: None (tool/utility)")
    elif args.port:
        base_port = args.port
        ports_str = f"{base_port}-{base_port + 9}"
        print(f"  Base port: {base_port}")
    else:
        suggested = get_next_available_port(category)
        print()
        try:
            port_input = input(f"  Base port [{suggested}]: ").strip()
            base_port = int(port_input) if port_input else suggested
            ports_str = f"{base_port}-{base_port + 9}"
        except ValueError:
            print("  Invalid port number.")
            return

    # Get entry type
    entry_type = args.type
    if not args.type and not args.yes:
        print()
        print(f"  Entry types: {', '.join(ENTRY_TYPES)}")
        type_input = input(f"  Type [{entry_type}]: ").strip()
        if type_input and type_input in ENTRY_TYPES:
            entry_type = type_input

    # Get tech stack
    if args.stack:
        if args.stack in TECH_STACKS and TECH_STACKS[args.stack]:
            stack = TECH_STACKS[args.stack]
        else:
            stack = args.stack
    elif not args.yes:
        print()
        print("  Tech stack presets: react-fastapi, react, nextjs, fastapi, express, python, node")
        stack_input = input("  Stack [react-fastapi]: ").strip() or "react-fastapi"
        if stack_input in TECH_STACKS and TECH_STACKS[stack_input]:
            stack = TECH_STACKS[stack_input]
        else:
            stack = stack_input
    else:
        stack = TECH_STACKS["react-fastapi"]

    # Get GitHub URL
    github = args.github
    if not github and not args.yes:
        print()
        github = input("  GitHub URL (optional): ").strip() or None

    # Get description
    description = args.description
    if not description and not args.yes:
        print()
        description = input("  Description (optional): ").strip() or None

    # Summary
    print()
    print("  " + "-" * 50)
    print("  SUMMARY")
    print("  " + "-" * 50)
    print(f"  Project: {project_name}")
    print(f"  Category: {category}")
    print(f"  Type: {entry_type}")
    if base_port:
        print(f"  Ports: {ports_str} (Frontend: {base_port}, Backend: {base_port + 1})")
    print(f"  Stack: {stack}")
    if github:
        print(f"  GitHub: {github}")
    if description:
        print(f"  Description: {description}")
    print()

    # Confirm
    if not args.yes:
        confirm = input("  Initialize project? [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("  Cancelled.")
            return

    print()

    # Create ports.json
    if base_port:
        ports_file = create_ports_json(project_dir, project_name, base_port)
        print(f"  Created: {ports_file}")

    # Add to catalog
    success = add_to_catalog(
        name=project_name,
        category=category,
        entry_type=entry_type,
        path=str(project_dir),
        ports=ports_str,
        stack=stack,
        github=github,
        description=description
    )

    if success:
        catalog_file = get_catalog_file()
        print(f"  Added to: {catalog_file}")

        # Update quick reference
        if ports_str:
            update_quick_reference(project_name, category, ports_str)
            print("  Updated Quick Reference table")

    print()
    print("  " + "=" * 50)
    print("  PROJECT INITIALIZED!")
    print("  " + "=" * 50)
    if base_port:
        print(f"  Frontend: http://{hostname}:{base_port}")
        print(f"  Backend:  http://{hostname}:{base_port + 1}")
    print()
    print("  Next steps:")
    print("    1. Create your project structure")
    print("    2. Run 'catalog.py' to verify registration")
    print("    3. Start building!")
    print()


if __name__ == "__main__":
    main()
