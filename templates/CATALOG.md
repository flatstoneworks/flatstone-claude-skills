# Development Catalog

> Living registry of all projects and skills. Single source of truth for project data and port allocations.
> Use `/catalog` to view projects, `/ports` to manage ports, `/init` to register new projects.

---

## WORK
*Work projects*

*(No projects registered yet)*

---

## PERSONAL
*Personal projects*

*(No projects registered yet)*

---

## EXPERIMENTS
*Experimental projects*

*(No projects registered yet)*

---

## TOOLS
*Tools and utilities (no ports)*

*(No projects registered yet)*

---

## Quick Reference

### Port Allocation Summary

| Category | Project | Ports |
|----------|---------|-------|

### Status Legend
- **Active** - Production ready, in use
- **WIP** - Work in progress
- **Archived** - No longer maintained

---

## Entry Format Reference

Each project entry follows this format:

```markdown
### ProjectName
| Property | Value |
|----------|-------|
| Type | Application |
| Path | `/path/to/project` |
| Ports | 3000-3009 |
| Allocated | frontend:3000, backend:3001, websocket:3003 |
| Stack | React, FastAPI, etc. |
| GitHub | https://github.com/user/repo |
| Status | Active |

Project description here.
```

**Allocated format:** `name:port, name:port, ...`
- This is the source of truth for port allocations
- Use `/ports allocate <name> <offset>` to add new allocations
