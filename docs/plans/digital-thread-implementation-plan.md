# Health Studio — Digital Thread Implementation Plan

## Vision

Health Studio tracks health data. The digital thread turns it into a **connected narrative** — where a journal reflection about tweaking your squat form links to your back squat PR history and your "Squat 405" goal, and visiting that goal shows every journal entry, result, and metric that references it. Every entity becomes a node in a personal health knowledge graph.

This plan builds toward that vision in six phases, each delivering standalone value, each scoped to fit in a single LLM session.

---

## Table of Contents

- [Technology Decisions](#technology-decisions)
- [Data Model Additions](#data-model-additions)
- [Phase 1 — Entity Mentions & Backlinks ✅](#phase-1--entity-mentions--backlinks-)
- [Phase 2 — Global Search ✅](#phase-2--global-search-)
- [Phase 3 — Tags](#phase-3--tags)
- [Phase 4 — Unified Timeline](#phase-4--unified-timeline)
- [Phase 5 — Smart Suggestions & Contextual Previews](#phase-5--smart-suggestions--contextual-previews)
- [Phase 6 — Graph Visualization](#phase-6--graph-visualization)
- [Appendix A — Local Embedding Model Evaluation](#appendix-a--local-embedding-model-evaluation)
- [Appendix B — Entity Reference Syntax](#appendix-b--entity-reference-syntax)

---

## Technology Decisions

### Entity Mention Syntax

Use a double-bracket wiki-link syntax in journal Markdown:

```
[[goal:Squat 405]]
[[metric:Body Weight]]
[[exercise:Back Squat]]
```

Format: `[[entity_type:display_name]]`. The parser resolves display names to IDs at save time. If the name is ambiguous (unlikely in a single-user app), the first match wins and the user can correct via the autocomplete UI. The raw syntax is preserved in `content` — resolution is stored in the `entity_mentions` join table.

This syntax was chosen because:
- It's a well-known wiki convention (Obsidian, Notion, Logseq)
- It's unambiguous to parse (no collision with standard Markdown)
- It degrades gracefully — readers without rendering still see `[[goal:Squat 405]]` in plain text
- The entity type prefix prevents cross-type name collisions

### Search Strategy: SQLite FTS5 (No Vector DB in Phase 2)

SQLite ships with FTS5 (Full-Text Search, version 5), a production-grade full-text search engine. It supports:
- Tokenized full-text indexing with BM25 ranking
- Prefix queries (`squat*`)
- Boolean operators (`shoulder AND rehab`)
- Column weighting (title matches ranked higher than body matches)
- Snippet extraction with hit highlighting

For a single-user app with thousands (not millions) of documents, FTS5 delivers sub-millisecond search with zero infrastructure. No additional service, no RAM overhead, no API key.

**FTS5 tables created:**
- `search_index` — a single FTS5 virtual table indexing all entity types (regular content mode, not external content). Columns: `entity_type`, `entity_id`, `title`, `body`, `extra`. Kept in sync via application-level hooks (insert/update/delete calls in the service layer).

This avoids the complexity of per-table FTS tables and gives us cross-entity search from a single query.

### Future Option: Local Embedding Model for Semantic Search

FTS5 handles keyword search well but can't find conceptually related content (searching "leg day" won't find a journal entry about "squat programming"). A local embedding model could enable this.

**Recommended approach (Phase 6+ or optional add-on):**
- **Model:** `all-MiniLM-L6-v2` (22M parameters, ~80MB, runs on CPU in <50ms per embedding)
- **Runtime:** `sentence-transformers` Python library, loaded once at backend startup
- **Storage:** Embeddings stored as BLOBs in a `search_embeddings` table (384-dimensional float32 vectors = 1.5KB per entity)
- **Similarity search:** Cosine similarity computed in Python. For <10,000 entities, a brute-force scan over numpy arrays is faster than any index. For larger datasets, `sqlite-vss` (SQLite vector search extension) could be used.
- **Docker impact:** Adds ~300MB to the backend image (PyTorch CPU + model weights). Acceptable for laptop deployment but should be optional — disabled by default, enabled via `ENABLE_SEMANTIC_SEARCH=true` environment variable.

This is **deferred intentionally**. FTS5 covers the primary use case. Semantic search is a "delight" feature that can be layered on later without schema changes — the `search_embeddings` table is independent of `search_index`.

See [Appendix A](#appendix-a--local-embedding-model-evaluation) for model benchmarks and sizing.

### Frontend Autocomplete

The journal `[[` autocomplete will use a lightweight approach:
- On editor mount, fetch all entity names from a single new endpoint: `GET /api/entities/names` → `{ goals: [{id, name}], metrics: [{id, name}], exercises: [{id, name}] }`
- Cache in component state (total payload: a few KB for any realistic dataset)
- Filter client-side as the user types after `[[`
- Render as a floating dropdown anchored to the cursor position in the editor

This avoids a dedicated autocomplete API endpoint and keeps the interaction latency at zero.

### Hover Previews: Frontend-Only

Contextual hover cards (Phase 5) are rendered entirely on the frontend using data already available from the backlinks response and a small, typed preview endpoint. No server-side rendering or pre-computation needed.

---

## Data Model Additions

### `entity_mentions` (Phase 1)

Stores resolved references from journal entries to other entities.

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| journal_id | TEXT (FK) | → `journal_entries.id`, ON DELETE CASCADE |
| entity_type | TEXT | `goal`, `metric_type`, `exercise_type` |
| entity_id | TEXT | UUID of the referenced entity |
| display_text | TEXT | The display name as written (e.g., "Back Squat") |
| created_at | DATETIME | |

**Indexes:**
- `ix_entity_mentions_journal_id` on `journal_id` (list mentions for a journal)
- `ix_entity_mentions_entity` on `(entity_type, entity_id)` (backlinks query)

**Constraints:**
- Unique on `(journal_id, entity_type, entity_id)` — a journal can reference the same entity only once in the mentions table, even if the syntax appears multiple times in the text.

### `search_index` (Phase 2)

FTS5 virtual table for cross-entity full-text search.

```sql
CREATE VIRTUAL TABLE search_index USING fts5(
    entity_type,
    entity_id UNINDEXED,
    title,
    body,
    extra,
    tokenize='porter unicode61'
);
```

> **Note:** The original plan specified `content=''` (external content mode) but the implementation uses regular content-storing mode. External content mode caused SELECT queries to return NULL for all content columns, making snippet extraction impossible. Regular mode stores a copy of the text in the FTS5 shadow tables, which is acceptable for this dataset size.

- `entity_type`: `journal`, `goal`, `metric_type`, `exercise_type` (searchable, enables type filtering)
- `entity_id`: not indexed, just carried through for result linking
- `title`: entity name / journal title (weighted 10x in ranking)
- `body`: journal content, goal description + plan, metric/exercise notes
- `extra`: supplementary searchable text (metric unit, exercise category, goal status)
- `tokenize='porter unicode61'`: Porter stemming + Unicode support ("running" matches "run")

### `entity_tags` (Phase 3)

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT (UUID) | Primary key |
| entity_type | TEXT | `journal`, `goal`, `metric_type`, `exercise_type` |
| entity_id | TEXT | UUID of the tagged entity |
| tag | TEXT | Lowercase, trimmed (e.g., "strength", "recovery") |
| created_at | DATETIME | |

**Indexes:**
- `ix_entity_tags_tag` on `tag` (find all entities with a tag)
- `ix_entity_tags_entity` on `(entity_type, entity_id)` (list tags for an entity)

**Constraints:**
- Unique on `(entity_type, entity_id, tag)` — no duplicate tags per entity.

---

## Phase 1 — Entity Mentions & Backlinks ✅

**Status:** Implemented (branch `triche/dt-phase1`)

**Goal:** Journal entries can reference goals, metric types, and exercise types using `[[type:name]]` syntax. Referenced entities show a "Referenced in" section listing journal entries that mention them. This is the foundational linking mechanism for the entire digital thread.

**Scope:** Backend model + migration, mention parsing + sync, backlinks API, journal editor autocomplete, mention rendering in journal view, backlinks component on goal/metric/result pages.

---

### Backend (Implemented)

**Model: `entity_mentions`**
- `backend/app/models/mention.py`
- Fields: `id`, `journal_id` (FK to journal_entries with CASCADE), `entity_type`, `entity_id`, `display_text`, `created_at`
- UniqueConstraint on `(journal_id, entity_type, entity_id)`
- Indexes on `journal_id` and `(entity_type, entity_id)`

**Alembic migration:**
- `backend/alembic/versions/7e8d28a29697_add_entity_mentions_table.py`

**Mention parsing: `backend/app/services/mentions.py`**

- `parse_mentions(content)` — Extracts `(entity_type, display_text)` tuples from journal content using case-insensitive regex. Supports aliases: `goal`/`goals`, `metric`/`metrics`/`metric_type`, `exercise`/`exercises`/`exercise_type`/`result`/`results`. All aliases map to canonical types (`goal`, `metric_type`, `exercise_type`).
- `resolve_mentions(db, mentions)` — Resolves display names to entity IDs via case-insensitive name lookup. Unresolved mentions are silently skipped.
- `sync_mentions(db, journal_id, content)` — Parses, resolves, and upserts the `entity_mentions` table. Deletes stale mentions, inserts new ones, leaves existing.
- `get_journal_mentions(db, journal_id)` — Returns all mentions for a journal entry.
- `get_backlinks(db, entity_type, entity_id)` — Returns journal entries referencing an entity, with ~200-char snippets centered on the mention.
- `_extract_snippet(content, entity_type, display_text)` — Regex-based snippet extraction that finds any alias form of the mention in the content.
- `get_entity_names(db)` — Returns all entity names grouped by type for autocomplete.

**Service layer changes:**
- `services/journal.py`: Calls `sync_mentions()` after `create_journal` (with `db.flush()` to get the ID) and `update_journal` (when content changes). Cascade delete handles cleanup.
- `services/export_import.py`: After JSON import, re-derives mentions by running `sync_mentions` on all imported journals (self-healing approach — no `entity_mentions` in the export payload).

**Endpoints (in `backend/app/routers/mentions.py`):**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/entities/names` | All entity names grouped by type (for autocomplete) |
| GET | `/api/journals/{id}/mentions` | Resolved mentions for a journal entry |
| GET | `/api/goals/{id}/backlinks` | Journal entries referencing a goal |
| GET | `/api/metric-types/{id}/backlinks` | Journal entries referencing a metric type |
| GET | `/api/exercise-types/{id}/backlinks` | Journal entries referencing an exercise type |

**Schemas (`backend/app/schemas/mention.py`):**
- `MentionResponse`: entity_type, entity_id, display_text
- `BacklinkResponse`: journal_id, title, entry_date, snippet
- `EntityNameItem`, `EntityNamesResponse`

---

### Frontend (Implemented)

**Mention autocomplete (`MentionAutocomplete.tsx`):**
- Detects `[[` from React `value` prop changes (not native DOM events) for reliable MDEditor integration
- Shows a floating dropdown positioned at the cursor using the Range API on MDEditor's visible `<pre><code>` element
- Dropdown grouped by entity type with headers: Goals, Metrics, Exercises
- Filters as user types after `[[`; keyboard navigation (↑/↓/Enter/Tab/Escape)
- Selecting an item inserts `[[type:Name]]` into the editor content
- Entity names fetched on mount via `GET /api/entities/names`, cached in state
- Keyboard events captured in capture phase on the container to intercept before MDEditor

**Mention rendering (`MentionRenderer.tsx`):**
- Case-insensitive regex matching all aliases (`goal`, `goals`, `metric`, `metrics`, `exercise`, `exercises`, `result`, `results`, `metric_type`, `exercise_type`)
- `ALIAS_MAP` normalizes any alias to a canonical config key
- Renders mentions as styled pill links with emoji icons (🎯 goals, 📊 metrics, 🏋️ exercises)
- Integrated into journal list via custom `react-markdown` components for `<p>` and `<li>` elements

**MarkdownEditor integration (`MarkdownEditor.tsx`):**
- Wraps MDEditor in a container div with `ref` passed to MentionAutocomplete
- `handleInsert` callback replaces value with `before + mention + after`

**Backlinks component (`Backlinks.tsx`):**
- Reusable component taking `entityType` and `entityId` props
- Fetches backlinks from the appropriate endpoint based on entity type
- Renders "Referenced in Journals" section with linked journal titles, dates, and snippets
- Empty state: "No journal entries reference this yet"
- Integrated into: `Goals.tsx`, `Metrics.tsx`, `Results.tsx`

**New files:**
- `frontend/src/types/mention.ts` — `Mention`, `Backlink`, `EntityNameItem`, `EntityNames` interfaces
- `frontend/src/api/mentions.ts` — `getEntityNames()`, `getJournalMentions()`, `getBacklinks()` with `BACKLINK_PATHS` mapping

---

### Tests (Implemented)

**Backend — `backend/tests/test_mentions.py` (30 tests across 6 classes):**
- `TestParseMentions` — basic mentions, exercise mentions, empty content, deduplication, multiple types, invalid types ignored, alias parsing (`Results`, `Goals`, `Metrics`), case-insensitive types
- `TestResolveMentions` — resolve goal/metric_type/exercise_type by name, not-found skipped, case-insensitive matching
- `TestSyncMentions` — sync on create, sync on update (mentions replaced), cascade on delete
- `TestBacklinks` — goal/metric/exercise backlinks, empty backlinks, snippet extraction, entry_date included
- `TestEntityNames` — returns all types, empty when no entities
- `TestMentionsEndpoint` — journal mentions, no mentions, 404 for missing journal, alias `[[Results:...]]` end-to-end sync with backlinks

**Frontend — `frontend/tests/Mentions.test.tsx` (9 tests):**
- Backlinks: shows referencing journals, empty state, journal links, correct API params, section heading
- renderMentions: `[[Results:Name]]`, `[[Goals:Name]]`, `[[Metrics:Name]]` render as links, mixed-case aliases

---

### Export/Import Impact (Implemented)

- Export does **not** include `entity_mentions` — they are derived data
- On JSON import, after all entities are committed, `sync_mentions` runs on every imported journal to re-derive mentions (self-healing if entity IDs differ between exports)

---

## Phase 2 — Global Search ✅

**Status:** Implemented (branch `main`)

**Goal:** Search across all entity types from a single search bar. Find any journal entry, goal, metric type, or exercise type by keyword. This is the fastest way to pull on a thread — search "shoulder" and see your shoulder press PRs, journal entries about rehab, and your overhead press goal.

**Scope:** FTS5 index creation + sync, search API endpoint, frontend search UI (command palette), CLI search command.

---

### Backend (Implemented)

**Alembic migration:**
- `backend/alembic/versions/a1b2c3d4e5f6_add_search_index_fts5.py`
- Raw SQL (Alembic doesn't manage virtual tables natively)
- Creates `search_index` FTS5 virtual table with regular content mode (NOT `content=''` external content — changed during implementation because external content mode caused SELECT to return NULLs, breaking snippet extraction)

**Search service: `backend/app/services/search.py`**

- `_has_fts5(db)` — checks if the `search_index` table exists (graceful degradation if migration hasn't run)
- `_get_rowid(db, entity_type, entity_id)` — finds existing row by entity_type + entity_id
- `index_entity(db, entity_type, entity_id, title, body, extra)` — delete-then-insert upsert into FTS5 index
- `remove_from_index(db, entity_type, entity_id)` — delete by rowid
- `rebuild_index(db)` — clears entire index, then re-indexes all journals, goals, metric types, and exercise types
- `search(db, query, entity_types, limit, offset)` — FTS5 MATCH with BM25 ranking (title=10x, body=1x, extra=0.5x), snippet extraction with `<mark>` tags, optional type filtering
- `search_count(db, query, entity_types)` — count matching results for pagination
- File uses `# ruff: noqa: S608` — the table name is a module-level constant, not user input

**Index sync hooks — in every service's create/update/delete:**

| Entity | title | body | extra |
|--------|-------|------|-------|
| journal | entry title | content (Markdown) | entry_date |
| goal | goal title | description + "\n" + plan | status, target_type, deadline |
| metric_type | name | "" | unit |
| exercise_type | name | "" | category, result_unit |

Service layer changes (in `services/journal.py`, `services/goal.py`, `services/metric.py`, `services/result.py`):
- After `create_*` → `db.flush()` then call `index_entity()` before `db.commit()`
- After `update_*` → call `index_entity()` before `db.commit()`
- Before `delete_*` → call `remove_from_index()` before `db.delete()`

**Rebuild on import:**
- `services/export_import.py`: After `import_json` completes all entity inserts and mention syncs, calls `rebuild_index(db)` before final commit.

**Endpoint (in `backend/app/routers/search.py`):**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search` | Full-text search (`q`, `types`, `limit`, `offset`) |

Response:
```json
{
  "query": "shoulder",
  "results": [
    {
      "entity_type": "journal",
      "entity_id": "abc-123",
      "title": "Shoulder rehab session",
      "snippet": "...worked on <mark>shoulder</mark> mobility drills and...",
      "rank": -4.52
    }
  ],
  "total": 1
}
```

**Schemas (`backend/app/schemas/search.py`):**
- `SearchResult`: entity_type, entity_id, title, snippet, rank
- `SearchResponse`: query, results (list[SearchResult]), total

---

### Frontend (Implemented)

**Command palette search (`SearchPalette.tsx`):**
- Triggered by `Cmd+K` (Mac) / `Ctrl+K` (Windows/Linux) via keydown listener in `App.tsx`, or by clicking search button in sidebar
- Modal overlay with backdrop, text input at the top
- Debounced search (300ms) calls `GET /api/search?q=...`
- Results listed with entity-type icons:
  - 📓 Journal entries → `/journals/{id}`
  - 🎯 Goals → `/goals`
  - 📊 Metric types → `/metrics`
  - 🏋️ Exercise types → `/results`
- Keyboard navigable: ↑/↓ to move, Enter to select, Escape to close
- Snippets rendered with `dangerouslySetInnerHTML` (contains FTS5 `<mark>` tags)
- Empty state: "No results found" / placeholder: "Start typing to search across all your health data"

**Sidebar addition (`Sidebar.tsx`):**
- Search button with magnifying glass SVG icon and `⌘K` keyboard shortcut hint
- `SidebarProps` extended with `onSearchOpen?: () => void`

**App integration (`App.tsx`):**
- `searchOpen` state, `handleSearchKeydown` callback for Cmd+K/Ctrl+K toggle
- `<SearchPalette open={searchOpen} onClose={...} />` rendered at root layout level

**New files:**
- `frontend/src/types/search.ts` — `SearchResult`, `SearchResponse` interfaces
- `frontend/src/api/search.ts` — `search(query, types?, limit?, offset?)` using URLSearchParams

---

### CLI (Implemented)

New command: `hs search <query> [--type/-t journal|goal|metric|exercise] [--limit/-l 20]`

- File: `cli/health_studio_cli/commands/search.py`
- Registered via `app.add_typer(search_app, name="search")` in `cli/health_studio_cli/main.py`
- Type aliases: `metric` → `metric_type`, `exercise` → `exercise_type`
- Renders results as a Rich table: Type | Title | Snippet
- Color-coded by entity type: cyan=Journal, yellow=Goal, green=Metric, magenta=Exercise

---

### Tests (Implemented)

**Backend — `backend/tests/test_search.py` (31 tests across 8 classes):**
- `TestIndexEntity` (2) — index and find entity, index replaces on update
- `TestRemoveFromIndex` (1) — remove entity from index
- `TestRebuildIndex` (2) — indexes all entity types, clears stale entries
- `TestSearch` (12) — by title, by content, goal, exercise, metric, stemming ("running" → "run"), prefix ("squat*"), ranking (title > body), type filter, pagination, empty query, no results
- `TestSearchIndexSyncOnCreate` (4) — journal, goal, metric_type, exercise_type appear in search after API create
- `TestSearchIndexSyncOnUpdate` (2) — journal, goal updated content found in search via API
- `TestSearchIndexSyncOnDelete` (2) — journal, goal removed from search after API delete
- `TestSearchEndpoint` (5) — returns results, type filter, empty query, pagination, requires auth
- `TestSearchRebuildOnImport` (1) — import JSON triggers full index rebuild

**Frontend — `frontend/tests/Search.test.tsx` (7 tests):**
- Renders when open, does not render when closed
- Calls onClose on Escape
- Shows results grouped by type
- Shows no results message
- Shows placeholder text before searching
- Navigates to correct page when selecting a journal result

**Test infrastructure:**
- `backend/tests/conftest.py`: `_create_fts5_tables(engine)` and `_drop_fts5_tables(engine)` added to `_setup_db` fixture (SQLAlchemy `create_all` doesn't handle FTS5 virtual tables)

---

### Export/Import Impact (Implemented)

- Export does **not** include the FTS5 index — it is derived data
- On JSON import, after all entities are committed and mentions synced, `rebuild_index(db)` re-indexes everything

---

## Phase 3 — Tags

**Goal:** Tag any entity (journals, goals, metric types, exercise types) with freeform labels. Filter any list by tag. Tags become lightweight connective tissue — group related things across entity types without explicit mention links.

**Scope:** Tags model + migration, tag CRUD API, tag filtering on all list endpoints, tag UI on all entity pages, tag filter in sidebar/search.

---

### Backend

**Model: `entity_tags`**
- New file: `backend/app/models/tag.py`
- Fields: `id`, `entity_type`, `entity_id`, `tag` (lowercase, trimmed), `created_at`
- Unique constraint on `(entity_type, entity_id, tag)`
- Register in `models/__init__.py`

**Alembic migration:**
- `alembic revision --autogenerate -m "add entity_tags table"`

**Tag service: `backend/app/services/tags.py`**

```python
def add_tag(db, entity_type: str, entity_id: str, tag: str) -> EntityTag:
    """Add a tag to an entity. Normalizes to lowercase/trimmed. No-op if already exists."""
    ...

def remove_tag(db, entity_type: str, entity_id: str, tag: str) -> None:
    """Remove a tag from an entity."""
    ...

def get_tags(db, entity_type: str, entity_id: str) -> list[str]:
    """Get all tags for an entity."""
    ...

def list_all_tags(db) -> list[dict]:
    """Get all unique tags with usage counts, sorted by count desc."""
    # Returns: [{"tag": "strength", "count": 12}, ...]
    ...

def get_entities_by_tag(db, tag: str, entity_type: str | None = None) -> list[dict]:
    """Get all entities with a given tag, optionally filtered by type."""
    ...

def sync_tags(db, entity_type: str, entity_id: str, tags: list[str]) -> None:
    """Set the exact tag list for an entity — adds new, removes missing."""
    ...
```

**Schema changes:**

Add optional `tags` field to existing create/update/response schemas:
- `JournalCreate` / `JournalUpdate` / `JournalResponse` → `tags: list[str] | None`
- `GoalCreate` / `GoalUpdate` / `GoalResponse` → `tags: list[str] | None`
- `MetricTypeCreate` / `MetricTypeUpdate` / `MetricTypeResponse` → `tags: list[str] | None`
- `ExerciseTypeCreate` / `ExerciseTypeUpdate` / `ExerciseTypeResponse` → `tags: list[str] | None`

**Service layer changes:**
- On create/update of any entity, if `tags` is provided, call `sync_tags()`
- On get/list of any entity, include tags in the response (join or subquery)
- On delete of any entity, cascade deletes entity_tags

**List endpoint filtering:**
- Add `?tag=strength` query parameter to all list endpoints: `/api/journals`, `/api/goals`, `/api/metric-types`, `/api/exercise-types`
- Filter via subquery: entities that have a matching row in `entity_tags`

**New endpoints:**

`GET /api/tags` → all unique tags with counts
```json
[
  {"tag": "strength", "count": 12},
  {"tag": "recovery", "count": 8},
  {"tag": "nutrition", "count": 5}
]
```

`GET /api/tags/{tag}` → all entities with this tag
```json
{
  "tag": "strength",
  "entities": [
    {"entity_type": "goal", "entity_id": "abc", "title": "Squat 405"},
    {"entity_type": "journal", "entity_id": "def", "title": "Leg day reflections"},
    {"entity_type": "exercise_type", "entity_id": "ghi", "title": "Back Squat"}
  ]
}
```

**Router:** New file `backend/app/routers/tags.py`, mounted under `/api`.

**Search index impact:**
- When tags change, re-index the entity with tags as part of the `extra` field so tags are searchable via global search.

**Export/Import impact:**
- `export_json` includes `entity_tags` in the payload
- `import_json` imports `entity_tags` rows
- Alternatively, embed tags in each entity's export object and derive entity_tags on import (cleaner JSON structure)

---

### Frontend

**Tag input component: `TagInput.tsx`**
- Appears on journal edit, goal create/edit, metric type create, exercise type create
- Displays current tags as removable pills/chips
- Text input with autocomplete from existing tags (`GET /api/tags`)
- Pressing Enter or comma adds the typed tag
- Clicking × on a pill removes it
- Tags are normalized to lowercase on input

**Tag display component: `TagList.tsx`**
- Renders tags as clickable pills on list views and detail views
- Clicking a tag navigates to a filtered view (e.g., `/journals?tag=strength`)

**Tag filter in list pages:**
- Add a tag filter dropdown/pill bar above the list on Journals, Goals, Metrics, Results pages
- Selecting a tag filters the list via `?tag=...` query parameter
- Active tag filter shown as a dismissible pill
- Can also be activated by clicking a tag on any entity

**Tags page (optional but recommended):**
- New page: `/tags` — browse all tags, see counts, click to see all entities with that tag
- Or: integrate into the search palette as a "Browse by tag" section

**Sidebar addition:**
- Add "Tags" navigation item below the existing items

---

### CLI

- `hs tags list` — all tags with counts
- `hs tags show <tag>` — all entities with a tag
- Support `--tag` filter on existing list commands: `hs journal list --tag recovery`
- Support `--tags strength,recovery` on create/update commands

---

### Tests

**Backend (pytest):**
- `test_tags.py`:
  - `test_add_tag` — tag is created and associated
  - `test_add_tag_normalized` — "  Strength  " becomes "strength"
  - `test_add_tag_idempotent` — adding same tag twice is a no-op
  - `test_remove_tag` — tag is removed
  - `test_get_tags` — returns all tags for an entity
  - `test_sync_tags` — sets exact tag list, adding/removing as needed
  - `test_list_all_tags` — returns unique tags with counts
  - `test_get_entities_by_tag` — returns all entities with a tag
  - `test_get_entities_by_tag_filtered` — type filter works
  - `test_journal_create_with_tags` — journal creation includes tags
  - `test_journal_update_tags` — updating journal tags syncs correctly
  - `test_journal_list_filter_by_tag` — tag query parameter filters list
  - `test_goal_list_filter_by_tag` — same for goals
  - `test_tag_search_integration` — tags appear in search results
  - `test_tag_cascade_delete` — deleting entity removes its tags

**Frontend (vitest):**
- `Tags.test.tsx`:
  - TagInput renders existing tags as pills
  - TagInput adds tag on Enter
  - TagInput removes tag on click
  - TagInput autocompletes from existing tags
  - TagList renders clickable tag pills
  - Tag filter on journal list works
  - Tags page shows all tags with counts

---

## Phase 4 — Unified Timeline

**Goal:** A single chronological feed that interleaves all entity types — journal entries, metric entries, result entries, and goal milestones. This is the "home feed" of your health narrative. Replaces or supplements the existing dashboard with a richer, scrollable view of your health journey.

**Scope:** Timeline API endpoint, frontend timeline page, entity type filtering, infinite scroll, CLI timeline command.

---

### Backend

**New endpoint:**

`GET /api/timeline?page=1&per_page=20&types=journal,metric,result,goal&tag=strength&date_from=2026-01-01&date_to=2026-04-01`

This is a **union query** across multiple tables, ordered by date descending. Each item is normalized to a common shape:

```json
{
  "items": [
    {
      "type": "journal",
      "id": "abc-123",
      "title": "Leg day reflections",
      "summary": "First 200 chars of content...",
      "date": "2026-04-01",
      "tags": ["strength", "legs"],
      "metadata": {}
    },
    {
      "type": "result",
      "id": "def-456",
      "title": "Back Squat",
      "summary": "315 lbs",
      "date": "2026-04-01",
      "tags": ["strength"],
      "metadata": {"value": 315, "display_value": "315 lbs", "is_pr": true, "is_rx": true, "exercise_type_id": "..."}
    },
    {
      "type": "metric",
      "id": "ghi-789",
      "title": "Body Weight",
      "summary": "205 lbs",
      "date": "2026-03-31",
      "tags": [],
      "metadata": {"value": 205, "unit": "lbs", "metric_type_id": "..."}
    },
    {
      "type": "goal",
      "id": "jkl-012",
      "title": "Squat 405",
      "summary": "Created • 77% progress",
      "date": "2026-03-15",
      "tags": ["strength"],
      "metadata": {"status": "active", "progress": 77.0, "event": "created"}
    }
  ],
  "total": 142,
  "page": 1,
  "per_page": 20
}
```

**Implementation approach:**

The timeline service builds a union query:

```python
def get_timeline(db, page, per_page, types, tag, date_from, date_to) -> dict:
    """
    Union across entity tables, each projecting the same columns.
    Sort by date DESC, paginate.

    For goals: include creation date. Goal status changes could be tracked
    separately if we add an audit log in the future.
    """
    ...
```

Because SQLAlchemy union queries with different models can be awkward, a pragmatic approach:
1. Query each included type separately with limit = per_page (fetch slightly more than needed)
2. Merge and sort in Python
3. Slice to page

This is fast for realistic data sizes (thousands of entries, not millions). If performance becomes an issue, a materialized view or denormalized timeline table could be added later.

**Service:** `backend/app/services/timeline.py`
**Router:** `backend/app/routers/timeline.py`
**Schemas:** `backend/app/schemas/timeline.py`

---

### Frontend

**New page: `/timeline`**

- Infinite scroll (or "Load more" button) rather than traditional pagination
- Each timeline item is a card styled by entity type:
  - **Journal:** Title, date, first 2 lines of content (rendered Markdown with mention pills via Phase 1's `renderMentions()`), tags, mention chips
  - **Result:** Exercise name, value (with PR badge if applicable), date, notes excerpt, tags
  - **Metric:** Metric name, value + unit, date, mini sparkline (last 7 values), tags
  - **Goal:** Title, progress bar, status badge, date, tags
- Filter bar at the top:
  - Entity type toggles (all on by default): Journal / Metric / Result / Goal
  - Tag filter dropdown
  - Date range picker
- Clicking any card navigates to the entity's detail page
- Cards show mention links and tags as clickable elements

**Sidebar addition:**
- Add "Timeline" navigation item, positioned first (above Dashboard) or second

**Component: `TimelineCard.tsx`**
- Polymorphic card component that renders different layouts based on `type`
- Reuses existing styling patterns from Dashboard cards

**Component: `TimelineFilters.tsx`**
- Entity type toggle buttons
- Tag filter (reuses `TagInput.tsx` in filter mode)
- Date range inputs

---

### CLI

New command: `hs timeline [--type journal,result] [--tag strength] [--limit 20]`

- Renders a chronological list using Rich
- Color-coded by entity type
- Shows: date, type icon, title, summary

---

### Tests

**Backend (pytest):**
- `test_timeline.py`:
  - `test_timeline_mixed_types` — returns interleaved journal + metric + result entries
  - `test_timeline_type_filter` — `types=journal` excludes metrics and results
  - `test_timeline_tag_filter` — only tagged entities appear
  - `test_timeline_date_range` — date boundaries work
  - `test_timeline_pagination` — page/per_page work correctly
  - `test_timeline_ordering` — items ordered by date descending
  - `test_timeline_empty` — no data returns empty list
  - `test_timeline_goal_events` — goals appear with creation date

**Frontend (vitest):**
- `Timeline.test.tsx`:
  - Renders mixed entity cards
  - Type filter toggles work
  - Tag filter works
  - Cards navigate to correct detail pages
  - Infinite scroll / load more works
  - Empty state displayed when no data

---

## Phase 5 — Smart Suggestions & Contextual Previews

**Goal:** Reduce friction in building connections. When writing a journal entry, Health Studio suggests entities to link based on what you're typing. When hovering over links and backlinks, see a preview card without navigating away.

**Scope:** Entity name matching in journal editor, suggestion UI, hover preview cards, preview data endpoint.

---

### Backend

**New endpoint:**

`GET /api/entities/preview?type=goal&id=abc-123`

Returns a lightweight preview payload tailored to the entity type:

```json
// Goal preview
{
  "entity_type": "goal",
  "entity_id": "abc-123",
  "title": "Squat 405",
  "status": "active",
  "progress": 77.0,
  "target_value": 405,
  "current_value": 315,
  "deadline": "2026-12-31"
}

// Metric type preview
{
  "entity_type": "metric_type",
  "entity_id": "def-456",
  "title": "Body Weight",
  "unit": "lbs",
  "latest_value": 205,
  "latest_date": "2026-04-01",
  "trend": [{"date": "2026-03-25", "value": 207}, ...] // last 7 data points
}

// Exercise type preview
{
  "entity_type": "exercise_type",
  "entity_id": "ghi-789",
  "title": "Back Squat",
  "category": "Barbell",
  "result_unit": "lbs",
  "pr_value": 315,
  "pr_date": "2026-03-20",
  "recent_results": [{"date": "2026-03-20", "value": 315}, ...] // last 5
}
```

**Router:** Add to `backend/app/routers/entities.py`

---

### Frontend

**Smart suggestions: `MentionSuggestions.tsx`**

Runs alongside the journal editor (below or beside it). As the user types:
1. Debounce the content (500ms after last keystroke)
2. Tokenize the current paragraph into significant words (ignore stop words)
3. Match against the cached entity names list (already fetched by `MentionAutocomplete` from Phase 1 via `GET /api/entities/names`)
4. Display matching entities that aren't already mentioned as suggestion chips: "Link to Back Squat?" / "Link to Squat 405?"
5. Clicking a suggestion inserts `[[type:Name]]` at the cursor position (reuse cursor detection infrastructure from Phase 1's `MentionAutocomplete.tsx` which uses the Range API on MDEditor's `<pre><code>` element)

**Matching algorithm (client-side):**
- Case-insensitive substring match of entity names against the journal text
- Multi-word entity names require all words to appear (not necessarily contiguous): "back squat" matches "did some back squats today"
- Exclude entities already mentioned (already have `[[...]]` syntax in content)
- Rank by: exact name match > all-words-present > partial match

This is purely client-side — no additional API calls beyond the initial entity names fetch.

**Hover preview cards: `EntityPreview.tsx`**

- Triggered on mouseenter over mention pill links (rendered by Phase 1's `MentionRenderer.tsx` in journal view) and backlink items (rendered by Phase 1's `Backlinks.tsx` on entity pages)
- Positioned as a floating card near the hover target (portal-rendered, collision-aware)
- Fetches `GET /api/entities/preview?type=...&id=...` on first hover, then caches
- Renders type-specific content:
  - **Goal:** Title, progress bar (colored by status), target vs. current, deadline
  - **Metric type:** Name, latest value + date, 7-point mini sparkline (SVG or tiny Plotly)
  - **Exercise type:** Name, category, PR value + date, last 5 results mini chart
- Dismisses on mouseleave (with small delay to allow mouse movement to the card itself)
- Loading state: skeleton placeholder while fetching

**Implementation notes:**
- Use `@floating-ui/react` (or simple absolute positioning) for card placement
- Sparklines in previews: use an inline SVG polyline (no Plotly overhead) for the small charts
- Cache previews in a React context or module-level Map to avoid re-fetching

---

### Tests

**Backend (pytest):**
- `test_entity_preview.py`:
  - `test_preview_goal` — returns goal with progress data
  - `test_preview_metric_type` — returns metric with latest value and trend
  - `test_preview_exercise_type` — returns exercise with PR and recent results
  - `test_preview_not_found` — 404 for unknown entity
  - `test_preview_invalid_type` — 400 for unsupported entity type

**Frontend (vitest):**
- `MentionSuggestions.test.tsx`:
  - Suggests entity when name appears in text
  - Does not suggest already-mentioned entities
  - Clicking suggestion inserts mention syntax
  - No suggestions when no matches
- `EntityPreview.test.tsx`:
  - Shows goal preview on hover
  - Shows metric preview with sparkline
  - Shows exercise preview with PR
  - Caches preview data (no re-fetch on second hover)
  - Shows loading state while fetching

---

## Phase 6 — Graph Visualization

**Goal:** Visualize the connections between all your health data as an interactive force-directed graph. See clusters emerge — your strength cluster, your recovery cluster, your nutrition cluster. This is the capstone of the digital thread: literally seeing the web of your health journey.

**Scope:** Graph data API endpoint, frontend graph page, interactive navigation, optional local embedding model for similarity edges.

---

### Backend

**New endpoint:**

`GET /api/graph?min_connections=0&include_orphans=false`

Returns a nodes-and-edges structure:

```json
{
  "nodes": [
    {"id": "journal:abc-123", "type": "journal", "label": "Leg day reflections", "date": "2026-04-01", "tags": ["strength"]},
    {"id": "goal:def-456", "type": "goal", "label": "Squat 405", "status": "active", "progress": 77, "tags": ["strength"]},
    {"id": "exercise_type:ghi-789", "type": "exercise_type", "label": "Back Squat", "tags": ["strength"]},
    {"id": "metric_type:jkl-012", "type": "metric_type", "label": "Body Weight", "tags": []}
  ],
  "edges": [
    {"source": "journal:abc-123", "target": "goal:def-456", "type": "mentions"},
    {"source": "journal:abc-123", "target": "exercise_type:ghi-789", "type": "mentions"},
    {"source": "goal:def-456", "target": "exercise_type:ghi-789", "type": "tracks"},
    {"source": "journal:abc-123", "target": "goal:def-456", "type": "shared_tag", "tag": "strength"}
  ]
}
```

**Edge types:**
- `mentions` — from mentions table (journal → entity)
- `tracks` — from goal target (goal → metric_type or exercise_type)
- `shared_tag` — entities that share a tag (only connect within the same tag, not across all shared tags)

**Service:** `backend/app/services/graph.py`

```python
def build_graph(db, min_connections=0, include_orphans=False) -> dict:
    """
    Build the full graph of entity connections.

    1. Fetch all entities as nodes
    2. Fetch all mention edges from entity_mentions (Phase 1 table)
    3. Fetch all goal-target edges from goals
    4. Compute shared-tag edges from entity_tags
    5. Optionally filter orphan nodes (no edges)
    6. Optionally filter by minimum connection count
    """
    ...
```

**Router:** `backend/app/routers/graph.py`

---

### Frontend

**New page: `/graph`**

**Library choice: `react-force-graph-2d`**
- Lightweight wrapper around `d3-force` (~40KB gzipped)
- Canvas-based (performant up to thousands of nodes)
- Built-in zoom, pan, node drag
- Supports custom node rendering, click handlers, hover tooltips
- Alternative: `@react-sigma/core` (WebGL-based, better for very large graphs) — but overkill for this use case

**Layout:**
- Full-width canvas filling the main content area
- Floating control panel (top-right):
  - Entity type toggle filters (show/hide by type)
  - Tag filter
  - Edge type toggles
  - "Include orphans" checkbox
  - Zoom controls
  - "Center" button (reset view)
- Floating node detail panel (right side or bottom, appears on node click):
  - Entity preview (reuse `EntityPreview.tsx` from Phase 5)
  - "Go to detail →" link
  - List of connections (clickable, highlights edge in graph)

**Node styling:**
- Color by entity type (using the project palette):
  - Journal: blue-400
  - Goal: amber-400
  - Metric type: emerald-400
  - Exercise type: rose-400
- Size by connection count (more connected = larger node)
- Shape: circles for all (keep it clean)
- Label: entity title (truncated to 20 chars), shown on hover or when zoomed in
- Opacity: dimmed for filtered-out types, full for active

**Edge styling:**
- `mentions`: solid line
- `tracks`: dashed line
- `shared_tag`: dotted line, lighter color
- Width: 1px (mentions), 2px (tracks)
- Color: gray-400 (darkens on hover/selection)

**Interactions:**
- **Click node:** Select node, show detail panel, highlight connected nodes and edges
- **Double-click node:** Navigate to entity detail page
- **Hover node:** Show tooltip with entity name and type
- **Drag node:** Reposition, simulation re-settles
- **Search within graph:** Filter nodes by text (highlights matching, dims others)

**New dependency:**
- `react-force-graph-2d` (npm package)

---

### Optional: Semantic Similarity Edges

If `ENABLE_SEMANTIC_SEARCH=true` is configured (see [Appendix A](#appendix-a--local-embedding-model-evaluation)):

**Additional edge type: `similar`**
- Computed by cosine similarity between entity embeddings
- Only add edges above a similarity threshold (e.g., 0.7)
- These reveal connections that aren't explicit (no mention, no shared tag) but are conceptually related
- Example: a journal entry about "progressive overload" connects to a goal about "increase bench press" even if neither explicitly mentions the other

**Endpoint extension:**
- `GET /api/graph?include_similar=true&similarity_threshold=0.7`
- Similarity edges are computed on-demand (or cached)

**Docker impact:**
- The embedding model adds ~300MB to the image
- Model loads at backend startup if enabled (~2s on CPU)
- Embedding computation is fast: <50ms per entity

This is entirely opt-in. The graph works without it — you just don't get the implicit similarity edges.

---

### CLI

- `hs graph stats` — show connection counts, most connected entities, orphan count
- No visual graph in the CLI (that's inherently a GUI feature)

---

### Tests

**Backend (pytest):**
- `test_graph.py`:
  - `test_graph_mention_edges` — mention links appear as edges
  - `test_graph_goal_target_edges` — goal-target links appear as edges
  - `test_graph_shared_tag_edges` — shared tags create edges
  - `test_graph_node_types` — all entity types represented
  - `test_graph_filter_orphans` — orphan nodes excluded when requested
  - `test_graph_min_connections` — min_connections filter works
  - `test_graph_empty` — empty database returns empty graph

**Frontend (vitest):**
- `Graph.test.tsx`:
  - Graph page renders without errors
  - Node count matches expected entities
  - Clicking node shows detail panel
  - Type filter toggles work
  - Note: Interactive graph testing is limited in JSDOM; focus on data loading and filter logic rather than canvas rendering

---

## Appendix A — Local Embedding Model Evaluation

### Recommended: `all-MiniLM-L6-v2`

| Property | Value |
|----------|-------|
| Parameters | 22.7M |
| Dimensions | 384 |
| Model size | ~80MB |
| Inference time (CPU) | ~30ms per sentence |
| Memory usage | ~200MB resident |
| Quality (STS benchmark) | 0.789 (Spearman correlation) |

**Why this model:**
- Small enough to run on any laptop CPU without GPU
- Quality is sufficient for short-text similarity (entity names, journal paragraphs)
- Well-supported by `sentence-transformers` library
- Apache 2.0 license

### Docker Image Impact

| Component | Size |
|-----------|------|
| Base image (python:3.12-slim) | ~150MB |
| Current app + dependencies | ~100MB |
| PyTorch CPU-only | ~180MB |
| sentence-transformers | ~20MB |
| Model weights | ~80MB |
| **Total with embeddings** | **~530MB** |
| **Total without** | **~250MB** |

### Architecture

```
ENABLE_SEMANTIC_SEARCH=true  (default: false)

Backend startup:
  if enabled:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    # Downloads model on first run (~80MB), cached in /app/models/

New table: search_embeddings
  entity_type TEXT
  entity_id TEXT
  embedding BLOB  (384 × float32 = 1,536 bytes)
  UNIQUE(entity_type, entity_id)

Sync hooks (same as FTS5 hooks):
  On entity create/update: compute embedding, upsert into search_embeddings
  On entity delete: remove from search_embeddings

Similarity query:
  Load all embeddings into numpy array (lazy, cached)
  Compute cosine similarity against query embedding
  Return top-K results above threshold
```

### Alternative: `gte-small` (Alibaba DAMO)

Slightly better quality (0.821 STS) at similar size (33M params, ~120MB). Worth evaluating if `all-MiniLM-L6-v2` quality is insufficient.

### What NOT to Use

- **OpenAI embeddings / Cohere / etc.** — Requires API key, cloud dependency, cost. Against project constraints.
- **Large models (e5-large, BGE-large)** — 300M+ params, >1GB, slow on CPU. Overkill for this dataset size.
- **ONNX runtime** — Possible optimization but adds complexity. Not needed at this scale.

---

## Appendix B — Entity Reference Syntax

### Full Syntax Specification

```
mention       = "[[" type_prefix ":" display_name "]]"
type_prefix   = "goal" | "goals"
              | "metric" | "metrics" | "metric_type"
              | "exercise" | "exercises" | "exercise_type"
              | "result" | "results"
display_name  = <any text except "]">
```

Type prefixes are **case-insensitive**: `[[Goal:...]]`, `[[METRIC:...]]`, and `[[results:...]]` all work.

### Type Prefix Mapping

| Syntax prefix(es) | Database `entity_type` | Target table |
|-------------------|----------------------|---------------|
| `goal`, `goals` | `goal` | `goals` |
| `metric`, `metrics`, `metric_type` | `metric_type` | `metric_types` |
| `exercise`, `exercises`, `exercise_type`, `result`, `results` | `exercise_type` | `exercise_types` |

### Resolution Rules

1. Match `display_name` against the `name` (or `title` for goals) column, case-insensitive
2. If exactly one match: resolve to that entity's ID
3. If multiple matches: resolve to the first match (by creation date ascending)
4. If no match: mention is stored as unresolved — the `[[...]]` syntax is preserved in content, but no row is added to `entity_mentions`. This means the text is harmless if you reference something that doesn't exist yet.
5. On subsequent saves: previously unresolved mentions are re-checked. If the entity now exists, a mention row is created.

### Examples

```markdown
Today I hit a new PR on [[exercise:Back Squat]] — 315 lbs! Getting closer to
my [[goal:Squat 405]] goal. My [[metric:Body Weight]] has been stable
around 205 which is perfect for this training block.
```

Renders as:
> Today I hit a new PR on **Back Squat** ↗ — 315 lbs! Getting closer to
> my **Squat 405** ↗ goal. My **Body Weight** ↗ has been stable
> around 205 which is perfect for this training block.

(Where ↗ represents a styled link to the entity's page)
