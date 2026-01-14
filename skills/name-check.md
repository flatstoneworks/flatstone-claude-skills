---
description: Check candidate product/project names for trademark conflicts and availability
allowed-tools: WebSearch, Task
argument-hint: "<name1>, <name2>, <name3>, ..."
---

# Name Availability Check Skill

## Purpose

Check candidate product/project names for trademark conflicts, existing products, and general availability before committing to a name.

## Usage

```
/name-check <name1>, <name2>, <name3>, ...
```

Or with context:
```
/name-check --domain software --names "PieBox, PieHub, PieCore"
```

## Process

### 1. Parse Input

Extract candidate names from user input (comma-separated or space-separated).

### 2. Parallel Search Strategy

For each candidate name, launch a sub-agent (using Task tool) to search for:

- **Direct trademark conflicts**: `"<name>" trademark registered`
- **Existing products**: `"<name>" software product application`
- **Company/startup usage**: `"<name>" company startup`
- **Domain-specific conflicts**: `"<name>" <domain> platform`
- **GitHub repos**: `"<name>" github repository`
- **NPM/PyPI packages**: `"<name>" npm package` or `"<name>" pypi`

### 3. Evaluation Criteria

**RED FLAGS (Name is taken):**
- Existing registered trademark in same/similar class
- Active product with same name in similar market
- Well-funded startup using the name
- Major company product using the name
- Popular open source project with the name

**YELLOW FLAGS (Proceed with caution):**
- Inactive/abandoned products with same name
- Products in completely different markets
- Generic dictionary words with broad usage
- Small projects with low visibility

**GREEN (Likely clear):**
- No significant search results
- Only unrelated uses (different industries)
- No trademark registrations found
- No active products or companies

### 4. Output Format

Return a structured assessment:

```markdown
## Name Check Results

| Name | Status | Conflicts Found | Notes |
|------|--------|-----------------|-------|
| PieBox | 🔴 RED | PieBox Inc. (software) | Active product, same market |
| PieHub | 🟢 GREEN | None | Clear to use |
| PieCore | 🟡 YELLOW | PieCore (defunct 2019) | Low risk, abandoned |

### Recommended Names
1. **PieHub** - No conflicts found, domain likely available
2. **PieCore** - Low risk, previous product abandoned

### Names to Avoid
1. **PieBox** - Active trademark conflict
```

### 5. Domain Availability (Optional)

If requested, also check:
- `.com` domain availability
- `.io` domain availability
- `.dev` domain availability

### 6. Iteration

If user needs N clear names and current batch doesn't have enough:
1. Generate new candidate names based on the naming pattern
2. Run additional checks
3. Repeat until N clear names found

## Sub-Agent Prompt Template

```
Search for existing products, trademarks, or companies using the name "<NAME>".

Search queries to run:
1. "<NAME>" trademark software
2. "<NAME>" product application
3. "<NAME>" company startup
4. "<NAME>" github repository
5. "<NAME>" <DOMAIN> platform

Evaluate:
- Is there an active product with this exact name?
- Is there a registered trademark?
- Is there a funded startup using this name?
- Is there a popular open source project?
- Would using this name create confusion?

Return:
- STATUS: RED (taken) / YELLOW (caution) / GREEN (clear)
- CONFLICTS: List any found with links
- RECOMMENDATION: Brief assessment
```

## Example Session

**User:** `/name-check PieStation, PieDeck, PieBox`

**Claude:**
1. Creates 3 parallel Task agents (one per name)
2. Each agent searches for conflicts
3. Collects and aggregates results
4. Returns summary table with recommendations

**User:** "I need 3 clear names, can you suggest alternatives?"

**Claude:**
1. Generates alternatives based on "Pie" theme: PieForge, PieStack, PieLab
2. Runs checks on new candidates
3. Returns updated recommendations

## Tips

- More specific/unique names are safer than generic ones
- Check common misspellings too
- Consider international conflicts for global products
- "Foo for X" style names (e.g., "Uber for Dogs") may have issues if Foo is trademarked
