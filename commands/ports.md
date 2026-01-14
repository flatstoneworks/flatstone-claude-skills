---
description: Port management utility - view, check, and allocate ports
allowed-tools: Bash(python3:*)
argument-hint: "[show | check | init [base] | allocate <name> <offset> | available <port>]"
---

# Port Management

Manage project port allocation using the ports.json configuration.

## Commands

Based on $ARGUMENTS, execute the appropriate command:

| Arguments | Action |
|-----------|--------|
| (empty) or `show` | Show current port configuration |
| `check` | Check for port conflicts |
| `init` | Initialize ports.json interactively |
| `init <base>` | Initialize with specific base port |
| `allocate <name> <offset>` | Allocate a named port at offset |
| `available <port>` | Check if specific port is available |

## Implementation

Execute the ports.py script with python3:

- `/ports` → `python3 scripts/ports.py show`
- `/ports show` → `python3 scripts/ports.py show`
- `/ports check` → `python3 scripts/ports.py check`
- `/ports init` → `python3 scripts/ports.py init`
- `/ports init 3000` → `python3 scripts/ports.py init --base 3000`
- `/ports allocate api 2` → `python3 scripts/ports.py allocate api 2`
- `/ports available 3000` → `python3 scripts/ports.py available 3000`

## Output

Display the command output directly to the user. The script will show:

- Port status with emoji indicators (🟢 running, ⚪ stopped)
- Process information (PID, process name) for ports in use
- Conflict warnings if ports are unexpectedly occupied

## Example Output

```
  Current Project: my-app
  Base Port: 3000
  Range: 3000-3009

  Allocated Ports:
    🟢 frontend: 3000 [node pid=12345]
    🟢 backend: 3001 [python pid=12346]
    ⚪ websocket: 3003

  ============================================================
  All Ports (All Projects)
  ============================================================
    🟢  3000  my-app                     frontend
    🟢  3001  my-app                     backend
    ⚪  4000  another-project            frontend
```
