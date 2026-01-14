#!/usr/bin/env python3
"""
Setup Utility for Claude Skills

Initialize the configuration and workspace for Claude Skills.

Usage:
    # Interactive setup
    python3 setup.py

    # Quick setup with defaults
    python3 setup.py --workspace ~/projects --yes
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Import config
try:
    from config import Config, DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import Config, DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE

# Get the templates directory (relative to this script)
SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"


def create_catalog_from_template(workspace: Path, categories: dict):
    """Create CATALOG.md from template."""
    catalog_file = workspace / "CATALOG.md"

    if catalog_file.exists():
        print(f"  CATALOG.md already exists at {catalog_file}")
        return False

    # Build catalog content
    content = """# Development Catalog

> Living registry of all projects and skills. Use `/catalog` to view, `/catalog add` to register new work.

---

"""

    for cat_name, cat_info in categories.items():
        desc = cat_info.get("description", "")
        content += f"""## {cat_name}
*{desc}*

*(No projects registered yet)*

---

"""

    content += """## Quick Reference

### Port Allocation Summary

| Category | Project | Ports |
|----------|---------|-------|

### Status Legend
- **Active** - Production ready, in use
- **WIP** - Work in progress
- **Archived** - No longer maintained
"""

    catalog_file.write_text(content)
    print(f"  Created: {catalog_file}")
    return True


def create_claude_md_snippet():
    """Return the CLAUDE.md snippet for skill commands."""
    return """
## Claude Skills Commands

Project initialization and catalog management skills.

### Project Initialization (MANDATORY)

When starting a new project, run `/init` to allocate ports and register in the catalog.

| Command | Action | Description |
|---------|--------|-------------|
| `/init` | `python3 scripts/init.py` | Interactive project initialization |
| `/init --category WORK --port 3050` | Quick init | Skip prompts |

### Catalog Management

| Command | Action | Description |
|---------|--------|-------------|
| `/catalog` | `python3 scripts/catalog.py show` | Show full catalog |
| `/catalog <category>` | `python3 scripts/catalog.py show <category>` | Show category |
| `/catalog add` | `python3 scripts/catalog.py add` | Add new entry |

### Port Management

| Command | Action | Description |
|---------|--------|-------------|
| `/ports` | `python3 scripts/ports.py show` | Show all ports |
| `/ports check` | `python3 scripts/ports.py check` | Check conflicts |
| `/ports available <port>` | `python3 scripts/ports.py available <port>` | Check availability |
"""


def main():
    parser = argparse.ArgumentParser(
        description="Setup Claude Skills configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--workspace', '-w', help='Workspace directory')
    parser.add_argument('--hostname', help='Hostname for URLs (default: localhost)')
    parser.add_argument('--yes', '-y', action='store_true', help='Accept defaults')

    args = parser.parse_args()

    print()
    print("  CLAUDE SKILLS SETUP")
    print("  " + "=" * 50)
    print()

    # Check if already configured
    if DEFAULT_CONFIG_FILE.exists():
        print(f"  Configuration already exists at {DEFAULT_CONFIG_FILE}")
        print()
        response = input("  Reconfigure? [y/N]: ").strip().lower()
        if response != 'y':
            print("  Setup cancelled.")
            return
        print()

    # Get workspace
    if args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    elif args.yes:
        workspace = Path.home() / "projects"
    else:
        default_workspace = Path.home() / "projects"
        print(f"  Where is your projects workspace?")
        workspace_input = input(f"  Workspace [{default_workspace}]: ").strip()
        workspace = Path(workspace_input).expanduser().resolve() if workspace_input else default_workspace

    # Create workspace if it doesn't exist
    if not workspace.exists():
        print(f"\n  Workspace {workspace} doesn't exist.")
        if args.yes or input("  Create it? [Y/n]: ").strip().lower() != 'n':
            workspace.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {workspace}")
        else:
            print("  Setup cancelled.")
            return

    # Get hostname
    if args.hostname:
        hostname = args.hostname
    elif args.yes:
        hostname = "localhost"
    else:
        print()
        hostname = input("  Hostname for URLs [localhost]: ").strip() or "localhost"

    # Define categories
    print()
    print("  Default categories:")
    default_categories = {
        "WORK": {"base": 3000, "description": "Work projects"},
        "PERSONAL": {"base": 4000, "description": "Personal projects"},
        "EXPERIMENTS": {"base": 5000, "description": "Experimental projects"},
        "TOOLS": {"base": None, "description": "Tools and utilities (no ports)"},
    }

    for cat, info in default_categories.items():
        port_info = f"(ports: {info['base']}-{info['base']+999})" if info['base'] else "(no ports)"
        print(f"    - {cat}: {info['description']} {port_info}")

    print()
    if not args.yes:
        customize = input("  Customize categories? [y/N]: ").strip().lower()
        if customize == 'y':
            print("\n  Category customization:")
            print("  (Press Enter to keep defaults, or enter new values)")
            print()

            new_categories = {}
            for cat, info in default_categories.items():
                keep = input(f"  Keep '{cat}'? [Y/n]: ").strip().lower()
                if keep != 'n':
                    new_categories[cat] = info

            # Add custom categories
            while True:
                new_cat = input("  Add new category (or Enter to finish): ").strip().upper()
                if not new_cat:
                    break
                desc = input(f"    Description for {new_cat}: ").strip()
                base_port = input(f"    Base port for {new_cat} (or Enter for none): ").strip()
                new_categories[new_cat] = {
                    "base": int(base_port) if base_port else None,
                    "description": desc
                }

            default_categories = new_categories

    categories = default_categories

    # Summary
    print()
    print("  " + "-" * 50)
    print("  CONFIGURATION SUMMARY")
    print("  " + "-" * 50)
    print(f"  Workspace: {workspace}")
    print(f"  Hostname: {hostname}")
    print(f"  Categories: {', '.join(categories.keys())}")
    print(f"  Config file: {DEFAULT_CONFIG_FILE}")
    print()

    if not args.yes:
        confirm = input("  Save configuration? [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("  Setup cancelled.")
            return

    # Create config
    print()
    config = Config.init_config(
        workspace=str(workspace),
        hostname=hostname,
        categories=categories
    )

    # Save config
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.save()
    print(f"  Saved: {DEFAULT_CONFIG_FILE}")

    # Create CATALOG.md
    create_catalog_from_template(workspace, categories)

    # Create scripts directory in workspace
    scripts_dir = workspace / "scripts"
    if not scripts_dir.exists():
        scripts_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {scripts_dir}")

        # Copy scripts
        for script in ["config.py", "catalog.py", "init.py", "ports.py"]:
            src = SCRIPT_DIR / script
            dst = scripts_dir / script
            if src.exists():
                shutil.copy(src, dst)
                dst.chmod(0o755)
                print(f"  Copied: {dst}")

    # Show CLAUDE.md snippet
    print()
    print("  " + "=" * 50)
    print("  SETUP COMPLETE!")
    print("  " + "=" * 50)
    print()
    print("  Add this to your CLAUDE.md:")
    print("  " + "-" * 50)
    print(create_claude_md_snippet())
    print("  " + "-" * 50)
    print()
    print("  Next steps:")
    print("    1. Add the above snippet to your CLAUDE.md")
    print("    2. Start a new project with /init")
    print("    3. View your catalog with /catalog")
    print()


if __name__ == "__main__":
    main()
