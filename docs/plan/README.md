# Repository implementation plan

This directory is the canonical plan for local and cloud development. Linear identifiers and URLs are retained only as migration provenance; agents must be able to complete assigned work using repository content alone.

## Agent workflow

1. Read [`state.json`](state.json). Completion criterion: the assigned task's milestone is listed in `authorized_milestones`.
2. Locate the assigned ID in [`index.json`](index.json), then read its task or gate file. Completion criterion: its goal, acceptance criteria, dependencies, evidence, and out-of-scope boundary are understood.
3. Read the current [`milestone`](milestones/) and each direct `blocked_by` task. Read [`architecture.md`](architecture.md) for boundary or design work. Read [`readiness-review.md`](readiness-review.md) for gate, scope, or remediation decisions.
4. Follow [`execution-policy.md`](execution-policy.md). Implement one bounded task, produce its required evidence, and update its status without broadening scope.
5. Validate plan changes with `python3 scripts/plan_tool.py validate --root docs/plan`. Rebuild the compact index after metadata changes.

## Source hierarchy

1. `state.json` controls milestone authorization.
2. `tasks/*.md` and `gates/*.md` are canonical task contracts.
3. `architecture.md`, `project.md`, and `milestones/*.md` define shared context.
4. `readiness-review.md` supplies audit rationale and remediation history.
5. `index.json` is a generated discovery index; task files remain authoritative.

The one-time `import-snapshot` command overwrites generated project, milestone, task, and gate files. Do not use it as a routine sync after repository-native work begins.
