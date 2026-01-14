#!/usr/bin/env python3
"""
Claude Code Account Switcher

Automatically use different Claude accounts based on project directory.
Manages account configurations and generates a shell function for auto-switching.

Usage:
    # List configured accounts
    python3 scripts/accounts.py list

    # Add a new account with directory pattern
    python3 scripts/accounts.py add flatstone --pattern "*/FLATSTONE/*"

    # Add account with multiple patterns
    python3 scripts/accounts.py add wikioai --pattern "*/WIKIOAI/*" --pattern "*/wikioai/*"

    # Remove an account
    python3 scripts/accounts.py remove flatstone

    # Install the shell function to ~/.bashrc
    python3 scripts/accounts.py install

    # Show the generated shell function (without installing)
    python3 scripts/accounts.py show

    # Login to a specific account
    python3 scripts/accounts.py login flatstone

    # Check which account would be used for current directory
    python3 scripts/accounts.py which
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Configuration file location
CONFIG_FILE = Path.home() / ".claude-accounts.json"

# Default configuration
DEFAULT_CONFIG = {
    "accounts": {},
    "default_config_dir": str(Path.home() / ".claude"),
    "shell_function_name": "claude"
}


def load_config():
    """Load configuration from JSON file"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {CONFIG_FILE}, using defaults")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Save configuration to JSON file"""
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    print(f"Configuration saved to {CONFIG_FILE}")


def cmd_list(args, config):
    """List all configured accounts"""
    accounts = config.get("accounts", {})

    if not accounts:
        print("No accounts configured.")
        print("\nUse 'accounts.py add <name> --pattern <pattern>' to add one.")
        return

    print("  CLAUDE CODE ACCOUNTS")
    print("  " + "=" * 50)
    print()

    for name, info in accounts.items():
        config_dir = info.get("config_dir", f"~/.claude-{name}")
        patterns = info.get("patterns", [])
        exists = Path(os.path.expanduser(config_dir)).exists()
        logged_in = (Path(os.path.expanduser(config_dir)) / "credentials.json").exists() or \
                    (Path(os.path.expanduser(config_dir)) / ".credentials.json").exists()

        status = "✓ Ready" if logged_in else ("○ Not logged in" if exists else "○ Not initialized")

        print(f"  {name}")
        print(f"    Config:   {config_dir}")
        print(f"    Patterns: {', '.join(patterns) if patterns else '(none)'}")
        print(f"    Status:   {status}")
        print()

    print(f"  Default: {config.get('default_config_dir', '~/.claude')}")
    print()


def cmd_add(args, config):
    """Add a new account configuration"""
    name = args.name.lower()
    patterns = args.pattern or []

    if not patterns:
        # Generate default patterns based on name
        patterns = [f"*/{name.upper()}/*", f"*/{name.lower()}/*"]
        print(f"No patterns specified, using defaults: {patterns}")

    config_dir = args.config_dir or f"~/.claude-{name}"

    if "accounts" not in config:
        config["accounts"] = {}

    if name in config["accounts"] and not args.force:
        print(f"Account '{name}' already exists. Use --force to overwrite.")
        return

    config["accounts"][name] = {
        "config_dir": config_dir,
        "patterns": patterns
    }

    # Create the config directory
    config_path = Path(os.path.expanduser(config_dir))
    if not config_path.exists():
        config_path.mkdir(parents=True)
        print(f"Created directory: {config_dir}")

    save_config(config)
    print(f"Added account '{name}' with patterns: {patterns}")
    print(f"\nNext step: Run 'python3 scripts/accounts.py login {name}' to authenticate")


def cmd_remove(args, config):
    """Remove an account configuration"""
    name = args.name.lower()

    if name not in config.get("accounts", {}):
        print(f"Account '{name}' not found.")
        return

    del config["accounts"][name]
    save_config(config)
    print(f"Removed account '{name}'")
    print(f"Note: Config directory was not deleted. Remove manually if needed.")


def generate_shell_function(config):
    """Generate the bash/zsh function for auto-switching"""
    accounts = config.get("accounts", {})
    default_dir = config.get("default_config_dir", "~/.claude")
    func_name = config.get("shell_function_name", "claude")

    if not accounts:
        return None

    # Build case patterns
    case_blocks = []
    for name, info in accounts.items():
        patterns = info.get("patterns", [])
        config_dir = info.get("config_dir", f"~/.claude-{name}")

        if patterns:
            pattern_str = "|".join(patterns)
            case_blocks.append(f'    {pattern_str})\n      config_dir="{config_dir}"\n      ;;')

    cases = "\n".join(case_blocks)

    function_code = f'''# Claude Code auto-account switcher
# Generated by: python3 scripts/accounts.py install
# Config file: {CONFIG_FILE}
{func_name}() {{
  local config_dir

  case "$PWD" in
{cases}
    *)
      config_dir="{default_dir}"
      ;;
  esac

  CLAUDE_CONFIG_DIR="$config_dir" command claude "$@"
}}'''

    return function_code


def cmd_show(args, config):
    """Show the generated shell function"""
    function_code = generate_shell_function(config)

    if not function_code:
        print("No accounts configured. Nothing to generate.")
        return

    print(function_code)


def cmd_install(args, config):
    """Install the shell function to shell rc file"""
    function_code = generate_shell_function(config)

    if not function_code:
        print("No accounts configured. Nothing to install.")
        return

    # Detect shell rc file
    shell = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        rc_file = Path.home() / ".zshrc"
    else:
        rc_file = Path.home() / ".bashrc"

    if args.rc_file:
        rc_file = Path(args.rc_file)

    # Check if already installed
    marker_start = "# Claude Code auto-account switcher"
    marker_end = "# End Claude Code auto-account switcher"

    rc_content = rc_file.read_text() if rc_file.exists() else ""

    # Remove old installation if exists
    if marker_start in rc_content:
        lines = rc_content.split("\n")
        new_lines = []
        skip = False
        for line in lines:
            if marker_start in line:
                skip = True
                continue
            if skip and line.strip() == "}":
                skip = False
                continue
            if not skip:
                new_lines.append(line)
        rc_content = "\n".join(new_lines).rstrip()

    # Append new function
    with open(rc_file, "w") as f:
        f.write(rc_content)
        if rc_content and not rc_content.endswith("\n"):
            f.write("\n")
        f.write("\n")
        f.write(function_code)
        f.write("\n")

    print(f"Installed shell function to {rc_file}")
    print("\nReload your shell or run:")
    print(f"  source {rc_file}")


def cmd_login(args, config):
    """Login to a specific account"""
    name = args.name.lower()

    if name not in config.get("accounts", {}):
        print(f"Account '{name}' not found.")
        print("Available accounts:", ", ".join(config.get("accounts", {}).keys()))
        return

    config_dir = config["accounts"][name].get("config_dir", f"~/.claude-{name}")
    config_path = Path(os.path.expanduser(config_dir))

    # Create directory if needed
    if not config_path.exists():
        config_path.mkdir(parents=True)
        print(f"Created directory: {config_dir}")

    print(f"Logging into account '{name}'...")
    print(f"Config directory: {config_dir}")
    print()

    # Run claude login with the config dir
    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(config_path)

    try:
        subprocess.run(["claude", "login"], env=env)
    except FileNotFoundError:
        print("Error: 'claude' command not found. Is Claude Code installed?")


def cmd_which(args, config):
    """Show which account would be used for current/specified directory"""
    import fnmatch

    check_dir = args.directory or os.getcwd()
    accounts = config.get("accounts", {})
    default_dir = config.get("default_config_dir", "~/.claude")

    for name, info in accounts.items():
        patterns = info.get("patterns", [])
        for pattern in patterns:
            if fnmatch.fnmatch(check_dir, pattern):
                config_dir = info.get("config_dir", f"~/.claude-{name}")
                print(f"Directory: {check_dir}")
                print(f"Account:   {name}")
                print(f"Config:    {config_dir}")
                print(f"Pattern:   {pattern}")
                return

    print(f"Directory: {check_dir}")
    print(f"Account:   (default)")
    print(f"Config:    {default_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Account Switcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  accounts.py list                              # List all accounts
  accounts.py add flatstone                     # Add with default patterns
  accounts.py add work --pattern "*/work/*"    # Add with custom pattern
  accounts.py install                           # Install shell function
  accounts.py login flatstone                   # Login to account
  accounts.py which                             # Check current directory
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list
    list_parser = subparsers.add_parser("list", help="List configured accounts")

    # add
    add_parser = subparsers.add_parser("add", help="Add a new account")
    add_parser.add_argument("name", help="Account name (e.g., 'flatstone', 'work')")
    add_parser.add_argument("--pattern", "-p", action="append",
                           help="Directory pattern (can specify multiple)")
    add_parser.add_argument("--config-dir", "-c",
                           help="Config directory (default: ~/.claude-<name>)")
    add_parser.add_argument("--force", "-f", action="store_true",
                           help="Overwrite existing account")

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove an account")
    remove_parser.add_argument("name", help="Account name to remove")

    # show
    show_parser = subparsers.add_parser("show", help="Show generated shell function")

    # install
    install_parser = subparsers.add_parser("install", help="Install shell function")
    install_parser.add_argument("--rc-file", help="Shell rc file to install to")

    # login
    login_parser = subparsers.add_parser("login", help="Login to an account")
    login_parser.add_argument("name", help="Account name to login to")

    # which
    which_parser = subparsers.add_parser("which", help="Check which account for directory")
    which_parser.add_argument("directory", nargs="?", help="Directory to check (default: current)")

    args = parser.parse_args()
    config = load_config()

    if args.command == "list":
        cmd_list(args, config)
    elif args.command == "add":
        cmd_add(args, config)
    elif args.command == "remove":
        cmd_remove(args, config)
    elif args.command == "show":
        cmd_show(args, config)
    elif args.command == "install":
        cmd_install(args, config)
    elif args.command == "login":
        cmd_login(args, config)
    elif args.command == "which":
        cmd_which(args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
