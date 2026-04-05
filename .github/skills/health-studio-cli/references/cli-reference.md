# CLI Command Reference

Complete reference for every `hs` command, including arguments, options, output format, and example usage.

---

## Global

```bash
hs              # Show banner and version
hs --version    # Show version
hs --help       # Show all command groups
```

---

## `hs config` — Configuration

### `hs config init`
Interactive setup. Prompts for base URL and API key. Writes to `~/.health-studio/config.toml`.

### `hs config show`
Displays current configuration. API key is masked (first 8 chars visible).

**Example output:**
```
Base URL: http://localhost:8000
API Key:  abc12345****
```

### `hs config set <key> <value>`
Update a single config value.

**Keys:** `server.base_url`, `auth.api_key`

```bash
hs config set server.base_url http://localhost:8000
hs config set auth.api_key my-new-key
```

---

## `hs dashboard` — Overview

Single command, no subcommands. Shows a compact summary of all domains:
- Recent journal entries (title, date)
- Active goals with progress percentage
- Latest metrics (with time format conversion for minutes)
- Recent personal records with 🏆 badge

```bash
hs dashboard
```

**Use this first** to get a broad overview before drilling into specifics.

---

## `hs goals` — Goal Tracking

### `hs goals list [--status STATUS]`
List all goals. Optionally filter by status.

**Options:**
- `--status` — Filter: `active`, `completed`, or `abandoned`

**Output columns:** ID (truncated to 8 chars), Title, Status, Progress (%), Deadline

```bash
hs goals list
hs goals list --status active
hs goals list --status completed
```

### `hs goals show <goal_id>`
Display detailed goal information including:
- Title, status, deadline
- Target value and current progress
- Whether lower is better
- Start value
- Full description and plan (rendered as Markdown)

```bash
hs goals show abc12345-full-uuid-here
```

**Note:** Use the full UUID from `goals list` output, not the truncated 8-char version. The truncated ID shown in tables is just for display.

---

## `hs metrics` — Health Metrics

### `hs metrics types`
List all available metric types.

**Output columns:** ID, Name, Unit

```bash
hs metrics types
```

**Always run this first** to discover metric type IDs before using `log` or `trend`.

### `hs metrics log <type_id> <value> [OPTIONS]`
Record a new metric entry.

**Arguments:**
- `type_id` — UUID of the metric type
- `value` — Numeric value to record

**Options:**
- `--date YYYY-MM-DD` — Date of measurement (default: today)
- `--notes TEXT` — Optional notes

```bash
hs metrics log abc123-type-uuid 72.5
hs metrics log abc123-type-uuid 155 --date 2026-04-01 --notes "Morning weigh-in"
```

### `hs metrics trend <type_id> [--since YYYY-MM-DD]`
View trend data for a metric over time.

**Arguments:**
- `type_id` — UUID of the metric type

**Options:**
- `--since YYYY-MM-DD` — Start date for the trend window

**Output columns:** Date, Value, Notes

```bash
hs metrics trend abc123-type-uuid
hs metrics trend abc123-type-uuid --since 2026-03-01
```

**Time conversion:** Metrics with unit "minutes" that are ≥ 60 display as `Xh Ym`.

---

## `hs results` — Exercise Results & Personal Records

### `hs results types`
List all available exercise types.

**Output columns:** ID, Name, Category, Unit

```bash
hs results types
```

**Always run this first** to discover exercise IDs before using `log` or `prs`.

### `hs results log <exercise_id> <value> [OPTIONS]`
Log an exercise result. The system automatically detects if this is a new personal record.

**Arguments:**
- `exercise_id` — UUID of the exercise type
- `value` — Numeric result value

**Options:**
- `--date YYYY-MM-DD` — Date of the exercise (default: today)
- `--notes TEXT` — Optional notes

**Output:** Shows success message. If the value is a new PR, displays 🏆 badge.

```bash
hs results log def456-exercise-uuid 185.5
hs results log def456-exercise-uuid 200 --date 2026-04-04 --notes "Felt strong"
```

### `hs results prs <exercise_id>`
Show personal record history for a specific exercise.

**Output columns:** Date, Value, Notes, RX status (✓ if RX)

```bash
hs results prs def456-exercise-uuid
```

---

## `hs journal` — Journal Entries

### `hs journal list [OPTIONS]`
List journal entries.

**Options:**
- `--since YYYY-MM-DD` — Only entries from this date forward
- `--limit N` — Maximum entries to return (default: 20)

**Output columns:** ID (truncated to 8 chars), Title, Date

```bash
hs journal list
hs journal list --since 2026-04-01
hs journal list --limit 5
```

### `hs journal show <journal_id>`
Display full journal entry with Markdown rendering.

**Output:** Title, date, and full body rendered as Markdown.

```bash
hs journal show abc12345-full-uuid-here
```

### `hs journal create --title TEXT [OPTIONS]`
Create a new journal entry.

**Required:**
- `--title TEXT` — Entry title

**Options:**
- `--file PATH` — Read body content from a file
- `--editor` — Open `$EDITOR` (default: `vi`) to compose the body
- `--date YYYY-MM-DD` — Entry date (default: today)

```bash
hs journal create --title "Weekly Reflection" --editor
hs journal create --title "Morning Notes" --file /tmp/entry.md --date 2026-04-04
```

---

## `hs export` — Export Data

### `hs export json <output_path>`
Export all Health Studio data as a JSON backup file.

```bash
hs export json ~/backups/health-studio-backup.json
```

### `hs export csv <entity> <output_path>`
Export a single entity type as CSV.

**Entities:** `metric_types`, `metric_entries`, `exercise_types`, `result_entries`, `journal_entries`, `goals`

```bash
hs export csv metric_entries ~/backups/metrics.csv
hs export csv journal_entries ~/backups/journals.csv
```

### `hs export markdown <output_path>`
Export all journal entries as a single Markdown document.

```bash
hs export markdown ~/backups/journals.md
```

---

## `hs import` — Import Data

### `hs import json <input_path>`
Import a full JSON backup. Skips records whose IDs already exist in the database.

```bash
hs import json ~/backups/health-studio-backup.json
```

**Output:** Table showing count of imported records per entity type and number skipped.

### `hs import csv <entity> <input_path>`
Import CSV data for metrics or results.

**Entities:** `metric_entries`, `result_entries`

**CSV columns (metric_entries):** `metric_type_id`, `value`, `recorded_date`, `notes` (optional)
**CSV columns (result_entries):** `exercise_type_id`, `value`, `recorded_date`, `notes` (optional)

```bash
hs import csv metric_entries ~/data/weight-history.csv
hs import csv result_entries ~/data/workout-log.csv
```

---

## Connection & Authentication

- **Base URL:** Configurable, default `http://localhost:8000`
- **Auth:** Bearer token via `Authorization` header
- **Env override:** Set `HEALTH_STUDIO_API_KEY` environment variable to override config file
- **Config file:** `~/.health-studio/config.toml`
- **Timeout:** 30 seconds per request

## Error Handling

If a command fails:
- **Connection refused** — Backend is not running. Start it with `docker compose up`
- **401 Unauthorized** — API key is invalid or missing. Run `hs config init`
- **404 Not Found** — The ID provided doesn't exist. Verify with the `types` or `list` command
- **422 Validation Error** — Invalid input format (e.g., bad date format, non-numeric value)
