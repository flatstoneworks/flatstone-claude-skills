# Flatstone Claude Skills

A collection of productivity skills for [Claude Code](https://claude.ai/code) that help manage projects, ports, and maintain a development catalog.

## Features

### Project Management
- **`/init`** - Initialize new projects with port allocation and catalog registration
- **`/catalog`** - View and manage your project registry
- **`/ports`** - Port management utilities

### Session Management
- **`/bye`** - Save session learnings to memory and exit gracefully

### Research
- **`/name-check`** - Check product names for trademark conflicts and availability

## Why?

When working with Claude Code on multiple projects, it's helpful to:

1. **Track all your projects** in one place
2. **Avoid port conflicts** between projects
3. **Maintain consistency** in project setup
4. **Preserve learnings** between sessions
5. **Validate names** before committing to them

These skills automate the tedious parts of project management so you can focus on building.

## Architecture

**CATALOG.md is the single source of truth** for all project and port data.

```
CATALOG.md
    └── Contains all project entries with:
        ├── Project metadata (name, type, path, stack)
        ├── Port ranges (e.g., 3000-3009)
        └── Allocated ports (e.g., frontend:3000, backend:3001)

/init ──────► Writes to CATALOG.md
/catalog ───► Reads from CATALOG.md
/ports ─────► Reads/writes CATALOG.md
```

### Allocated Port Format

Each project entry in CATALOG.md can have an `Allocated` field:

```markdown
| Allocated | frontend:3000, backend:3001, websocket:3003 |
```

This format is:
- Human-readable in the markdown file
- Parsed by `/ports` to show status and detect conflicts
- Updated by `/ports allocate` when adding new port assignments

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/flatstoneworks/flatstone-claude-skills.git
cd flatstone-claude-skills

# Run setup
./install.sh
```

### Manual Install

1. Clone this repository
2. Copy the `scripts/` and `commands/` directories to your workspace
3. Run `python3 scripts/setup.py` to configure
4. Add the CLAUDE.md snippet to your project's CLAUDE.md
5. Copy commands to `.claude/commands/` for slash command support

## Configuration

Configuration is stored in `~/.config/claude-skills/config.json`:

```json
{
  "workspace": "/path/to/your/workspace",
  "hostname": "localhost",
  "categories": {
    "WORK": {"base": 3000, "description": "Work projects"},
    "PERSONAL": {"base": 4000, "description": "Personal projects"},
    "EXPERIMENTS": {"base": 5000, "description": "Experimental projects"},
    "TOOLS": {"base": null, "description": "Tools and utilities (no ports)"}
  },
  "project_dirs": ["/path/to/your/workspace"]
}
```

### Environment Variables

Override config with environment variables:

- `CLAUDE_SKILLS_WORKSPACE` - Base workspace directory
- `CLAUDE_SKILLS_CATALOG` - Path to CATALOG.md
- `CLAUDE_SKILLS_CONFIG` - Path to config file

## Skills Reference

### `/init` - Project Initialization

**MANDATORY** when starting any new project.

```bash
# Interactive mode
/init

# Quick mode with options
/init --category WORK --port 3050 --stack react-fastapi

# View all options
/init --help
```

**What it does:**
1. Registers the project in `CATALOG.md` with port allocations
2. Suggests the next available port in your category
3. Sets up default allocations (frontend, backend)

---

### `/catalog` - Catalog Management

View and manage your project registry.

```bash
/catalog                    # Show full catalog
/catalog WORK               # Show specific category
/catalog add                # Add new entry interactively
/catalog update MyProject   # Update existing entry
/catalog list               # List all entries
```

---

### `/ports` - Port Management

Manage port allocations across projects. Reads directly from `CATALOG.md`.

```bash
/ports                      # Show all port allocations
/ports show MyProject       # Show specific project's ports
/ports check                # Check for conflicts in current project
/ports available 3000       # Check if port is available
/ports allocate MyProject api 2  # Allocate port at offset 2
/ports find 3000            # Find which project uses a port
```

---

### `/bye` - Graceful Session Exit

Save session learnings before ending.

```bash
/bye
```

**What it does:**
1. Reviews session accomplishments
2. Updates CLAUDE.md with new learnings
3. Updates CATALOG.md if new projects were created
4. Summarizes what was saved
5. Exits the session

---

### `/name-check` - Name Availability Check

Check product names for trademark conflicts.

```bash
/name-check PieBox, PieHub, PieCore
/name-check --domain software --names "AppName1, AppName2"
```

**What it does:**
1. Searches for trademark conflicts
2. Checks for existing products/startups
3. Returns RED/YELLOW/GREEN status for each name
4. Recommends which names are safe to use

## CLAUDE.md Integration

Add this to your CLAUDE.md to enable slash commands:

```markdown
## Claude Skills Commands

### Project Initialization (MANDATORY)

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
| `/ports show <project>` | `python3 scripts/ports.py show <project>` | Show project ports |
| `/ports check` | `python3 scripts/ports.py check` | Check conflicts |
| `/ports available <port>` | `python3 scripts/ports.py available <port>` | Check availability |
| `/ports allocate <project> <name> <offset>` | `python3 scripts/ports.py allocate ...` | Allocate port |
| `/ports find <port>` | `python3 scripts/ports.py find <port>` | Find port owner |

### Session Management

| Command | Description |
|---------|-------------|
| `/bye` | Save learnings and exit gracefully |

### Research

| Command | Description |
|---------|-------------|
| `/name-check <names>` | Check names for trademark conflicts |
```

## Project Structure

```
flatstone-claude-skills/
├── README.md
├── LICENSE
├── install.sh
├── scripts/
│   ├── config.py          # Configuration management
│   ├── setup.py           # Initial setup wizard
│   ├── init.py            # Project initialization
│   ├── catalog.py         # Catalog management
│   └── ports.py           # Port management
├── commands/
│   ├── bye.md             # Session exit command
│   └── ports.md           # Port management command
├── skills/
│   └── name-check.md      # Name availability checker
└── templates/
    ├── CATALOG.md         # Catalog template
    └── CLAUDE_SNIPPET.md  # CLAUDE.md snippet
```

## Customization

### Custom Categories

Edit `~/.config/claude-skills/config.json` to add your own categories:

```json
{
  "categories": {
    "CLIENTS": {"base": 6000, "description": "Client projects"},
    "INTERNAL": {"base": 7000, "description": "Internal tools"},
    "EXPERIMENTS": {"base": 8000, "description": "Experiments"}
  }
}
```

### Custom Hostname

If you're running on a server with a custom hostname:

```json
{
  "hostname": "myserver.local"
}
```

### Tech Stack Presets

The init script supports these presets:
- `react-fastapi` - React 18 + FastAPI (default)
- `react` - React 18 standalone
- `nextjs` - Next.js
- `fastapi` - FastAPI standalone
- `express` - Express.js
- `python` - Python
- `node` - Node.js

Or enter any custom stack string.

## Requirements

- Python 3.8+
- Claude Code CLI

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by [Flatstone Works](https://github.com/flatstoneworks)
