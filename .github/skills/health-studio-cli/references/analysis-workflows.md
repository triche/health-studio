# Analysis Workflows

Common multi-step patterns for answering health data questions using the CLI.

---

## Workflow 1: General Health Overview

**When:** User asks "how am I doing?" or wants a summary.

```bash
# Step 1: Get the dashboard overview
hs dashboard

# Step 2: Check active goals for progress
hs goals list --status active

# Step 3: Drill into any goals that are behind or noteworthy
hs goals show <goal_id>
```

**Analysis approach:** Summarize recent activity, highlight goals at risk (approaching deadline with low progress), note any new PRs, and call out metrics trending in a positive or negative direction.

---

## Workflow 2: Metric Trend Analysis

**When:** User asks about a specific metric (weight, sleep, blood pressure, etc.) or wants to see trends.

```bash
# Step 1: Find the metric type ID
hs metrics types

# Step 2: Pull trend data (adjust time window as needed)
hs metrics trend <type_id> --since 2026-01-01

# Step 3: For context, check related goals
hs goals list --status active
```

**Analysis approach:** Look for:
- Overall direction (improving, declining, stable)
- Rate of change
- Consistency of tracking (gaps in dates)
- Whether the trend aligns with any active goals
- Notable outliers or inflection points

---

## Workflow 3: Exercise Progress & PRs

**When:** User asks about exercise performance, strength gains, or personal records.

```bash
# Step 1: List available exercises
hs results types

# Step 2: Check PR history for relevant exercises
hs results prs <exercise_id>

# Step 3: For broader context, check dashboard
hs dashboard
```

**Analysis approach:** Look for:
- Frequency and recency of PRs
- Rate of improvement between PRs
- Whether PRs are RX or scaled
- Plateaus (long gaps between PRs)
- Correlation with goals

---

## Workflow 4: Goal Progress Deep-Dive

**When:** User asks about specific goal progress, whether they'll meet a deadline, or wants goal advice.

```bash
# Step 1: List goals (filter by status if needed)
hs goals list --status active

# Step 2: Get full details on the target goal
hs goals show <goal_id>

# Step 3: If the goal tracks a metric, pull trend data
hs metrics types
hs metrics trend <metric_type_id> --since <goal_start_date>

# Step 4: If the goal tracks exercise performance
hs results types
hs results prs <exercise_id>
```

**Analysis approach:**
- Calculate progress rate (current value vs start value, time elapsed vs total time)
- Project whether the goal is on track to meet its deadline
- Factor in `lower_is_better` (e.g., weight loss goals)
- Review the goal's plan/description for qualitative context
- Suggest adjustments if progress is off-track

---

## Workflow 5: Journal Review & Reflection

**When:** User asks about past journal entries, wants a recap, or needs to find something they wrote.

```bash
# Step 1: List recent entries
hs journal list --limit 10

# Step 2: Read specific entries
hs journal show <journal_id>

# Step 3: For time-bounded search
hs journal list --since 2026-03-01 --limit 50
```

**Analysis approach:**
- Summarize themes across entries
- Highlight any patterns in mood, energy, or concerns
- Connect journal content to metric/goal data for holistic insights

---

## Workflow 6: Cross-Domain Correlation

**When:** User asks questions that span multiple data types (e.g., "does my sleep affect my workout performance?" or "how does journaling frequency relate to my goal progress?").

```bash
# Step 1: Dashboard for overview
hs dashboard

# Step 2: Pull metric trends for each relevant metric
hs metrics types
hs metrics trend <sleep_type_id> --since 2026-01-01
hs metrics trend <other_metric_id> --since 2026-01-01

# Step 3: Pull exercise data
hs results types
hs results prs <exercise_id>

# Step 4: Journal entries for qualitative context
hs journal list --since 2026-01-01
hs journal show <entry_id>  # for particularly relevant entries
```

**Analysis approach:**
- Align data by date to look for correlations
- Note any patterns (e.g., PRs tend to come after periods of good sleep)
- Be transparent about limitations (correlation ≠ causation, limited sample size)
- Suggest tracking adjustments that could provide clearer data

---

## Workflow 7: Data Entry

**When:** User wants to log new data (metrics, exercise results, or journal entries).

```bash
# Step 1: Find the correct type ID
hs metrics types        # for metrics
hs results types        # for exercises

# Step 2: Log the data
hs metrics log <type_id> <value> --date YYYY-MM-DD --notes "context"
hs results log <exercise_id> <value> --date YYYY-MM-DD --notes "context"
hs journal create --title "Title" --file /tmp/entry.md
```

**Important:** Only log data when the user explicitly asks. Confirm the values before running the command. For journal entries, write the content to a temp file first, then use `--file` to create the entry.

---

## General Analysis Principles

1. **Always ground insights in actual data** — cite specific values, dates, and trends from CLI output.
2. **Acknowledge data gaps** — if tracking is inconsistent, note it and suggest more regular logging.
3. **Be actionable** — don't just describe data; suggest what the user could do next.
4. **Respect the user's goals** — frame insights in terms of their stated goals when possible.
5. **Be honest about limitations** — short time windows, small sample sizes, and confounding factors all matter.
