# Flatstone Claude Skills

A collection of productivity skills for [Claude Code](https://claude.ai/code) that help manage projects, ports, and maintain a development catalog.

## Features

- **`/init`** - Initialize new projects with port allocation and catalog registration
- **`/catalog`** - View and manage your project registry
- **`/ports`** - Port management utilities

## Why?

When working with Claude Code on multiple projects, it's helpful to:

1. **Track all your projects** in one place
2. **Avoid port conflicts** between projects
3. **Maintain consistency** in project setup

These skills automate the tedious parts of project management so you can focus on building.

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/flatstoneworks/flatstone-claude-skills.git
cd flatstone-claude-skills

# Run setup
python3 scripts/setup.py
```

### Manual Install

1. Clone this repository
2. Copy the `scripts/` directory to your workspace
3. Run `python3 scripts/setup.py` to configure
4. Add the CLAUDE.md snippet to your project's CLAUDE.md

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

## Usage

### Initialize a New Project

```bash
# Create project directory
mkdir my-new-project
cd my-new-project

# Run init (interactive)
python3 ../scripts/init.py

# Or with options
python3 ../scripts/init.py --category WORK --port 3050 --stack react-fastapi
```

This will:
1. Create `ports.json` in your project directory
2. Add the project to `CATALOG.md`
3. Suggest the next available port in your category

### View Your Catalog

```bash
# Show all projects
python3 scripts/catalog.py

# Show specific category
python3 scripts/catalog.py show WORK

# Add a new entry manually
python3 scripts/catalog.py add
```

### Manage Ports

```bash
# Show all port allocations
python3 scripts/ports.py

# Check for conflicts in current project
python3 scripts/ports.py check

# Check if a specific port is available
python3 scripts/ports.py available 3000

# Allocate a new port
python3 scripts/ports.py allocate websocket 3
```

## CLAUDE.md Integration

Add this to your CLAUDE.md to enable slash commands:

```markdown
## Claude Skills Commands

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
```

## Project Structure

```
flatstone-claude-skills/
├── README.md
├── LICENSE
├── scripts/
│   ├── config.py      # Configuration management
│   ├── setup.py       # Initial setup wizard
│   ├── init.py        # Project initialization
│   ├── catalog.py     # Catalog management
│   └── ports.py       # Port management
├── templates/
│   └── CATALOG.md     # Catalog template
└── docs/
    └── ...            # Additional documentation
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
