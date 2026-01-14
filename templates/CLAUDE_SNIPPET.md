## Claude Skills Commands

Project initialization and catalog management skills.

### Project Initialization (MANDATORY)

When starting a new project, run `/init` to allocate ports and register in the catalog.

| Command | Action | Description |
|---------|--------|-------------|
| `/init` | `python3 scripts/init.py` | Interactive project initialization |
| `/init --category WORK --port 3050` | Quick init | Skip prompts |
| `/init --help` | Show all options | View available flags |

**Workflow:**
```
1. Create project directory
2. cd into the directory
3. Run /init
4. Answer the prompts (category, port, stack, etc.)
5. Start building!
```

### Catalog Management

| Command | Action | Description |
|---------|--------|-------------|
| `/catalog` | `python3 scripts/catalog.py show` | Show full catalog |
| `/catalog <category>` | `python3 scripts/catalog.py show <category>` | Show category |
| `/catalog add` | `python3 scripts/catalog.py add` | Add new entry |
| `/catalog update <name>` | `python3 scripts/catalog.py update <name>` | Update entry |
| `/catalog list` | `python3 scripts/catalog.py list` | List all entries |

### Port Management

| Command | Action | Description |
|---------|--------|-------------|
| `/ports` | `python3 scripts/ports.py show` | Show all ports |
| `/ports check` | `python3 scripts/ports.py check` | Check conflicts |
| `/ports available <port>` | `python3 scripts/ports.py available <port>` | Check availability |
| `/ports allocate <name> <offset>` | `python3 scripts/ports.py allocate <name> <offset>` | Allocate port |
