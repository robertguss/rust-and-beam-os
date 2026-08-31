# Repository-native planning systems: Beads and beads_rust

Research snapshot: 2026-08-31. Sources are pinned to the repository revisions
reviewed so the conclusions remain reproducible.

## Executive finding

Neither project makes ordinary, human-readable files in the checked-out source
tree the sole writable source of truth.

- Current Beads (`bd`) makes a Dolt database canonical. Its JSONL file is only
  an export, and cross-machine synchronization happens through a separate Dolt
  ref on the Git remote. A normal source checkout therefore does not, by itself,
  expose the canonical plan to an agent.
  [Sync concepts](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/core-concepts/sync-concepts.md)
- beads_rust (`br`) makes SQLite canonical for local operation and uses
  `.beads/issues.jsonl` as the Git-friendly collaboration representation.
  Successful mutations auto-export by default, but incoming JSONL changes still
  require an explicit import or three-way merge. This is closer to repository
  portability, but it retains two representations whose freshness must be
  managed.
  [README](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/README.md),
  [CLI reference](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/CLI_REFERENCE.md)

For a “clone the repo and every agent can immediately understand the current
plan” requirement, the strongest design is the inverse: checked-in text records
are canonical, while databases, indexes, queues, and graph views are disposable
projections rebuilt from those records.

## Comparison

| Concern | Beads (`bd`) | beads_rust (`br`) |
|---|---|---|
| Canonical local store | Dolt database | SQLite database |
| Git-visible representation | Optional/passive JSONL export; not the sync protocol | JSONL export intended for Git collaboration |
| Cross-machine synchronization | `bd dolt push` / `bd dolt pull` via `refs/dolt/data` | Human runs Git; then `br` imports or merges JSONL |
| Merge model | Dolt cell-level merge | Git line merge first; `br sync --merge` then performs a semantic three-way merge against `beads.base.jsonl` |
| Dependency model | Typed blocking and non-blocking edges, cycle rejection, external-condition gates | Typed blocking and non-blocking edges with blocking-cycle rejection |
| Ready-work model | Open, non-deferred work with no active blockers; priority is the default ordering | Configurable ready-status group, no blocking dependency, defer-time filtering; hybrid ordering by default |
| Claim behavior | Atomic claim in one shared database; server mode supports concurrent writers | Atomic local claim under SQLite/write locking; coordination across clones still depends on Git handoff |
| Agent loop | `ready` → atomic `claim` → work/discover → `close` → Dolt push | `ready --json` → `update --claim` → work/discover → `close` → export → Git commit/push |

Sources for the table:
[Beads README](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/README.md),
[Beads ready reference](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/cli-reference/ready.md),
[Beads dependencies](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/core-concepts/dependencies.md),
[Beads coordination](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/multi-agent/coordination.md),
[beads_rust README](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/README.md),
[beads_rust agent guide](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/AGENT_INTEGRATION.md),
[beads_rust sync safety](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/SYNC_SAFETY.md).

## What each system gets right

### Beads

The dependency graph is more expressive than a flat issue list. Only semantic
blocking edges determine readiness, while provenance and knowledge links can
remain non-blocking. Write-time cycle rejection protects the executable graph;
gates can represent human approval, a timer, a pull request, CI, or an external
bead rather than pretending every prerequisite is ordinary work.
[Dependency and gate semantics](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/core-concepts/dependencies.md)

Its default work-selection contract is also crisp: `bd ready` returns open work
without active blockers, excludes in-progress/deferred/blocked items, orders by
priority unless told otherwise, and can atomically claim the first matching
item. Priorities use the conventional numeric P0–P4 scale.
[Ready command](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/cli-reference/ready.md),
[issue priorities](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/core-concepts/issues.md)

For multiple agents sharing one store, atomic claims and an explicit merge-slot
primitive address two different races: duplicate task selection and serialized
access to conflict-prone integration work. Hash-derived IDs avoid the ordinary
distributed collision problem of independently allocating sequential IDs.
[Agent coordination](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/multi-agent/coordination.md),
[ID tradeoffs](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/reference/configuration.md)

### beads_rust

beads_rust deliberately refuses Git authority: synchronization never stages,
commits, pulls, or pushes. That makes the boundary easy to audit and lets an
operator commit task-state changes alongside code deliberately.
[README design philosophy](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/README.md),
[sync safety contract](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/SYNC_SAFETY.md)

Its synchronization design acknowledges that SQLite and JSONL may both have
changed. The normal merge uses a saved base snapshot; semantic conflicts stop
unless the operator explicitly chooses database, JSONL, or timestamp policy.
It rejects unresolved Git conflict markers and protects against exporting an
empty or stale database over useful JSONL.
[Sync safety](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/SYNC_SAFETY.md)

The agent interface is strongly machine-oriented: structured output, explicit
exit/error contracts, atomic claim, discovered-work links, and a repeatable
`ready` → `claim` → `close` → `flush` loop. Ready statuses are repository
policy rather than hard-coded beyond the default `open`, and blocking cycles
are rejected for the edge types that influence execution.
[Agent integration](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/AGENT_INTEGRATION.md),
[ready and cycle semantics](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/CLI_REFERENCE.md)

## Failure and concurrency tradeoffs

| Failure or race | Consequence |
|---|---|
| Fresh source clone with Beads data | The source branch is insufficient; the agent needs the `bd` binary and a Dolt bootstrap/pull from the separate remote ref. JSONL may be stale or absent because it is explicitly non-canonical. |
| Concurrent Beads writers in embedded mode | Embedded mode is single-writer. Server mode is the documented multi-writer option. Automatic pushes are discouraged for racing writers because concurrent Git-protocol Dolt pushes can strand or corrupt remote history. |
| Fresh clone with beads_rust JSONL | The plan is inspectable as text, but normal query/update behavior requires rebuilding or importing into SQLite. |
| SQLite and JSONL both changed | A semantic merge is required after Git integration; same-record edits can demand an explicit winner. |
| Two agents on separate Git branches claim the same item | Each local database can accept its own “atomic” claim. Atomicity does not cross disconnected stores; the collision is discovered only after synchronization. |
| Two agents edit one JSONL file | Independent issue lines often merge, but same-line edits can produce textual conflicts; unresolved markers cause `br` import to fail closed. |
| Export omitted or stale | A Git commit may not contain the latest database state. beads_rust reduces this with default auto-flush and final-flush guidance, but the invariant remains procedural. |

Sources:
[Beads storage modes and sync](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/README.md),
[Beads push concurrency warning](https://github.com/gastownhall/beads/blob/d530cddfa64b174930bddc6c5949b127a450fc13/docs/reference/configuration.md),
[beads_rust architecture](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/ARCHITECTURE.md),
[beads_rust sync failure handling](https://github.com/Dicklesworthstone/beads_rust/blob/d2393c99ddcf337bd77d4ba61ce29ea8cdbe715b/docs/SYNC_SAFETY.md).

## Design lessons for a repository-native planning specification

1. **Choose one writable authority.** Task files committed on the source branch
   should be canonical. A database, JSON index, ready queue, Mermaid graph, or
   search index should be reproducible and explicitly marked generated.
2. **Use one record per task.** A directory of small Markdown files with strict
   frontmatter preserves readable context while reducing the Git conflict
   surface compared with a single JSONL ledger.
3. **Separate graph execution from graph annotation.** Define a small set of
   blocking edges used for DAG validation and readiness; keep `related-to`,
   `discovered-from`, `duplicates`, and similar links non-blocking.
4. **Make readiness a deterministic function.** A task is selectable only when
   its status is in a declared ready set, every blocking predecessor is done,
   authorization/gates allow it, and it is not deferred. Then rank the result by
   an explicit tuple such as `(priority, milestone order, stable ID)`.
5. **Validate before merge.** Reject missing IDs, duplicate IDs, self-edges,
   blocking cycles, invalid states, and inconsistent reverse links in CI.
6. **Treat claims honestly.** A file-based plan can provide atomic claims only
   within one checkout. Across branches or disconnected agents, ownership is an
   advisory, merge-mediated lease unless a shared coordinator is introduced.
7. **Preserve recovery evidence.** Git history already supplies record history;
   status transitions should still carry concise completion evidence, and
   destructive graph rewrites should be reviewable in the normal code diff.

The useful pieces to borrow are the typed DAG, deterministic ready-work query,
P0–P4 priority convention, atomic-when-local claims, explicit gates, structured
agent output, and fail-closed validation. The piece to avoid for this use case is
a mutable database plus a second serialized representation: it improves query
speed, but weakens the central promise that the checkout itself is complete,
canonical, and directly intelligible.
