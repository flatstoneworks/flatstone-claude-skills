---
description: Save session learnings to memory and exit gracefully
allowed-tools: Read, Write, Bash
argument-hint: ""
---

# Graceful Session Exit

Before ending this session, review and preserve important learnings.

## Steps

1. **Review the session** - Look back at what was accomplished:
   - New files created or modified
   - Problems solved and how
   - User preferences discovered
   - Project patterns or conventions learned
   - Useful commands or workflows identified

2. **Update CLAUDE.md if needed** - If significant project knowledge was gained:
   - Add new conventions or patterns to the appropriate CLAUDE.md
   - Document any new scripts, commands, or workflows
   - Update known port ranges if new projects were configured
   - Add any project-specific gotchas or debugging tips

3. **Update CATALOG.md if needed** - If new projects or skills were created:
   - Add new entries with `/catalog add`
   - Update status of existing projects (WIP → Active)

4. **Summarize for the user** - Briefly tell the user:
   - What was saved to memory/CLAUDE.md
   - Any pending tasks or next steps to remember

5. **Exit** - End the session

## Memory Candidates

Things worth remembering:
- New project structures or file locations
- User preferences (coding style, tools, workflows)
- Bug fixes that might recur
- API keys or service configurations (locations only, not values!)
- Debugging techniques that worked
- Project-specific gotchas
- New dependencies or tools installed

## What NOT to Save

- Sensitive data (passwords, API keys, tokens)
- Temporary debugging code
- One-off commands that won't be reused
- Information already documented elsewhere

## Output Format

```
Session Summary
===============

## Accomplished
- [List what was done]

## Saved to CLAUDE.md
- [List what was added/updated]

## Pending / Next Steps
- [Any incomplete work or follow-ups]

See you next time!
```

Then exit the session.
