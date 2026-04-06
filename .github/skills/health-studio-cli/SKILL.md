---
name: health-studio-cli
description: "Use the Health Studio CLI (`hs`) to query, analyze, and manage health data. USE WHEN: user asks about their health data, metrics, goals, journal entries, exercise results, personal records, trends, progress, dashboard, or wants insights/analysis from Health Studio. Also use when user wants to log data, create journal entries, or interact with their Health Studio instance. KEYWORDS: health data, metrics, goals, journal, exercise, results, personal records, trends, progress, dashboard, analysis, insights, weight, sleep, workout, fitness, habits."
---

# Health Studio CLI

Use the `hs` CLI tool to interact with the user's Health Studio application. The CLI connects to the running Health Studio backend API and provides rich terminal output.

## When to Use

- User asks questions about their health data (metrics, goals, results, journal)
- User wants analysis, insights, or trends from their tracked data
- User wants to log new data (metrics, exercise results, journal entries)
- User asks about progress toward goals
- User wants a summary/overview of their health status
- User asks about personal records or exercise history
- User wants to compare or correlate different health metrics

## Prerequisites

The CLI must be installed and configured. If a command fails with a connection or auth error:
1. Check config: `hs config show`
2. If not configured: `hs config init` (needs the running server URL and an API key)
3. Ensure the Health Studio backend is running (typically `docker compose up`)

## Core Workflow

### Step 1: Gather Context

Before answering a question, gather the relevant data using CLI commands. Start broad, then narrow down.

**For a general overview:**
```bash
hs dashboard
```

**For specific domains**, use the appropriate commands from the [CLI Reference](./references/cli-reference.md).

### Step 2: Query Specific Data

Based on what you learn from the overview, drill into specifics:

- List available metric types or exercise types first (to get IDs)
- Then query trends, PRs, or details using those IDs
- Combine multiple queries to build a complete picture

### Step 3: Analyze and Respond

After gathering data via the CLI:
- Synthesize the information into a clear, actionable answer
- Identify patterns, trends, and correlations across data points
- Provide specific insights grounded in the actual data
- Suggest next steps or areas of attention when relevant

## Important Notes

- **IDs are UUIDs** — commands like `hs metrics trend` and `hs results prs` require the type/exercise UUID. Always run the `types` subcommand first to discover available IDs.
- **Date filtering** — Use `--since YYYY-MM-DD` or `--date YYYY-MM-DD` to scope queries to relevant time periods.
- **Read-only by default** — Querying data is safe. Only use `log` or `create` commands when the user explicitly asks to record new data.
- **Output is Rich-formatted** — The CLI uses Rich tables and Markdown rendering in the terminal. Parse the structured output to extract values.

## Command Quick Reference

| Task | Command |
|------|---------|
| Overview | `hs dashboard` |
| List goals | `hs goals list [--status active\|completed\|abandoned]` |
| Goal details | `hs goals show <goal_id>` |
| Metric types | `hs metrics types` |
| Metric trend | `hs metrics trend <type_id> [--since YYYY-MM-DD]` |
| Log metric | `hs metrics log <type_id> <value> [--date YYYY-MM-DD] [--notes TEXT]` |
| Exercise types | `hs results types` |
| Personal records | `hs results prs <exercise_id>` |
| Log result | `hs results log <exercise_id> <value> [--date YYYY-MM-DD] [--notes TEXT]` |
| Journal entries | `hs journal list [--since YYYY-MM-DD] [--limit N]` |
| Read entry | `hs journal show <journal_id>` |
| Create entry | `hs journal create --title TEXT [--file PATH] [--editor] [--date YYYY-MM-DD]` |
| Export JSON backup | `hs export json <output_path>` |
| Export CSV | `hs export csv <entity> <output_path>` |
| Export journals Markdown | `hs export markdown <output_path>` |
| Import JSON backup | `hs import json <input_path>` |
| Import CSV | `hs import csv <entity> <input_path>` |

See [CLI Reference](./references/cli-reference.md) for full details on every command.

See [Analysis Workflows](./references/analysis-workflows.md) for common multi-step analysis patterns.
