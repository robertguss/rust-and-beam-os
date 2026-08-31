# Spec: repo-plan/v1

## Objective

Define a Git-native planning format that is complete and readable in an ordinary
source checkout. Humans and agents edit canonical Markdown records. A
standard-library-only reference CLI creates exact templates, validates the plan,
computes ready work, and rebuilds disposable indexes and graph views.

The format must not require a database, network service, hosted issue tracker, or
AI-authored boilerplate. Git history is the record history.

## Capability map

| Module | Responsibility | Depends on |
|---|---|---|
| `format` | Canonical project, milestone, task, gate, and decision contracts | — |
| `generate` | Deterministic initialization and record creation from versioned templates | `format` |
| `validate` | Schema, content, graph, readiness, link, evidence, and freshness checks | `format` |
| `adopt` | Deterministically migrate this repository's existing plan | `generate`, `validate` |

Build order: `format` → `generate` → `validate` → `adopt`.

## Authority model

Canonical inputs are:

- `project.yaml`;
- `milestones/*.md`;
- `tasks/*.md`;
- `gates/*.md`;
- `decisions/*.md`.

`generated/index.json`, `generated/graph.json`, and `generated/ready.json` are
deterministic projections. They may be committed for zero-tool discovery, but
they are never writable authorities. A local database may be added later only
as a disposable, ignored cache.

Every canonical record has exactly one file. Reverse edges and computed states
are projections:

- `parent` defines decomposition and never execution order;
- `depends_on` defines the blocking DAG;
- `related` is informational and may contain cycles;
- `milestone.authorized_by` names the human gate controlling that milestone;
- `blocks`, `ready`, `blocked`, and `current_gate` are derived and never stored.

## Project structure

```text
plan/
  README.md
  project.yaml
  milestones/
  tasks/
  gates/
  decisions/
  generated/
    index.json
    graph.json
    ready.json
```

The reference implementation lives in:

```text
scripts/repo_plan.py
templates/repo-plan/
tests/test_repo_plan.py
```

## Constrained YAML

Frontmatter and `project.yaml` use a portable subset of YAML:

- top-level scalar keys;
- top-level scalar lists;
- quoted strings, integers, booleans, `null`, and `[]`;
- no mappings inside values, anchors, aliases, tags, or multiline scalars.

The CLI emits fields in the order defined by this specification and ends files
with one newline. The same command and arguments must produce byte-identical
output.

## Project contract

`project.yaml` contains:

```yaml
schema: "repo-plan/v1"
name: "Example project"
prefix: "EX"
```

`prefix` is uppercase ASCII, begins with a letter, and contains two to eight
letters or digits. Record IDs are immutable and match
`<PREFIX>-<TYPE>-<TOKEN>`, where type is `T`, `E`, `G`, `M`, or `D` and token is
four to twelve uppercase letters or digits. Callers supply IDs explicitly so
record creation remains deterministic and distributed allocation has no shared
counter.

## Record contracts

### Task and epic

```yaml
---
schema: "repo-plan/v1"
id: "EX-T-7M3K2Q"
title: "Reproduce the reference runtime"
type: "task"
state: "open"
priority: "P1"
milestone: "EX-M-M0"
parent: null
depends_on: []
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
---
```

`type` is `task` or `epic`. Epics organize children and are not selectable.
Task bodies require these second-level headings in this order:

1. `Goal`
2. `Context`
3. `Deliverables`
4. `Acceptance criteria`
5. `Verification`
6. `Evidence`
7. `Out of scope`

### Milestone

```yaml
---
schema: "repo-plan/v1"
id: "EX-M-M0"
title: "Foundation"
type: "milestone"
order: 0
authorized_by: null
---
```

Milestone bodies require `Outcome` and `Exit criteria`. `authorized_by: null`
means initially authorized. Any other value must name a gate.

### Gate

```yaml
---
schema: "repo-plan/v1"
id: "EX-G-7Q2M9K"
title: "Authorize milestone M1"
type: "gate"
state: "open"
priority: "P0"
milestone: "EX-M-M0"
parent: null
depends_on: []
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
---
```

Gate bodies require `Decision`, `Required evidence`, `Acceptance criteria`,
`Decision record`, and `Out of scope`.

### Decision

```yaml
---
schema: "repo-plan/v1"
id: "EX-D-5W8N2R"
title: "Authorize milestone M1"
type: "decision"
gate: "EX-G-7Q2M9K"
outcome: "approved"
---
```

Decision bodies require `Decision`, `Evidence`, `Residual risks`, `Approver`,
and `Authorizing commit`. A completed gate must have exactly one decision that
references it.

Unknown frontmatter keys are rejected unless they start with `x_`. Extensions
are preserved but do not alter readiness.

## State and readiness

Task and gate state is one of `open`, `in_progress`, `done`, or `cancelled`.
Priority is `P0` through `P4`, where `P0` is highest.

A task is ready when all of these are true:

1. `type` is `task`;
2. `state` is `open`;
3. `actor` is `agent`;
4. `defer_until` is null or no later than the supplied evaluation date;
5. every `depends_on` record is `done`;
6. its milestone is authorized.

A milestone is authorized when `authorized_by` is null or the named gate is
`done`. Gate completion remains a human action. The CLI never completes a gate.

Ready work is ordered lexicographically by:

1. priority number ascending;
2. milestone order ascending;
3. count of incomplete downstream tasks descending;
4. stable ID ascending.

The ready projection records the factors so the ordering is explainable.

## Validation

`check` fails with actionable file-scoped errors when any invariant fails:

- missing required file, field, or body section;
- unknown non-extension field or invalid scalar type;
- malformed, duplicate, or prefix-mismatched ID;
- filename that does not contain the lowercase record ID;
- reference to a missing record or wrong record type;
- self-edge or cycle in `depends_on`;
- cycle in `parent` or a parent that is not an epic;
- a `done` record with unfinished dependencies;
- a `done` task without evidence;
- a `done` gate without exactly one valid decision;
- an epic marked `done` while a non-cancelled child is unfinished;
- invalid owner/state combination;
- broken repository-local Markdown link;
- generated projections that differ from a clean rebuild.

Informational `related` edges may cycle. Claims are advisory across Git clones:
`owner` is required only for `in_progress`, and must be null otherwise.

## Commands

```sh
# Create a complete empty plan with its initial milestone and projections.
python3 scripts/repo_plan.py init --root plan --name "Example" --prefix EX \
  --milestone-id EX-M-M0 --milestone-title "Foundation"

# Create canonical records from exact templates.
python3 scripts/repo_plan.py new milestone --root plan --id EX-M-M1 \
  --title "Implementation" --order 1 --authorized-by EX-G-7Q2M9K
python3 scripts/repo_plan.py new task --root plan --id EX-T-7M3K2Q \
  --title "Reproduce runtime" --milestone EX-M-M0 --priority P1
python3 scripts/repo_plan.py new gate --root plan --id EX-G-7Q2M9K \
  --title "Authorize M1" --milestone EX-M-M0
python3 scripts/repo_plan.py new decision --root plan --id EX-D-5W8N2R \
  --title "Authorize M1" --gate EX-G-7Q2M9K --outcome approved

# Rebuild or verify derived artifacts.
python3 scripts/repo_plan.py build --root plan --date 2026-08-31
python3 scripts/repo_plan.py check --root plan --date 2026-08-31
python3 scripts/repo_plan.py ready --root plan --date 2026-08-31 --json
```

`new` refuses to overwrite a file. `init` refuses a non-empty destination.
`build` is the only command that writes generated projections. `check` and
`ready` are read-only. Dates are explicit inputs; the CLI never embeds the wall
clock in canonical or generated files.

## Testing strategy

Use Python `unittest` with temporary real files and subprocess-level CLI tests.
Every behavior begins with a failing test. Tests cover:

- byte-identical initialization and record generation;
- refusal to overwrite;
- standard YAML interoperability for emitted frontmatter;
- every validation invariant listed above;
- ready ordering and explanations;
- exact generated-file freshness checks;
- successful end-to-end operation in a fresh temporary directory;
- deterministic migration of the existing legacy plan.

Run focused tests during each slice and the complete suite before every commit:

```sh
python3 -m unittest tests/test_repo_plan.py
python3 -m unittest discover -s tests
```

## Boundaries

- Always: keep canonical records human-readable, deterministic, and complete;
  make reverse relationships derived; validate before committing plan changes.
- Ask first: add dependencies, introduce a database or service, change ID or
  readiness semantics, or make a breaking schema revision.
- Never: require network access, silently overwrite canonical records, infer a
  gate decision, or let generated output become a writable authority.

## Success criteria

- A clean clone with Python 3 can initialize and use a plan offline.
- Every canonical file is generated from a versioned template or validated
  against the same contract.
- Equal inputs produce byte-identical canonical and generated files.
- `check` detects missing content, invalid graph state, broken links, and stale
  projections with a non-zero exit status.
- `ready` is deterministic and explains why each returned task is selectable.
- The current Rust + BEAM plan passes `repo-plan/v1` validation after migration.
- The complete test suite and end-to-end CLI verification pass.

## Deferred extensions

- Cross-clone atomic leases or a shared coordinator;
- a disposable SQLite query cache;
- interactive terminal UI;
- hosted integrations and bidirectional issue-tracker synchronization;
- schema migration beyond the legacy format in this repository.
