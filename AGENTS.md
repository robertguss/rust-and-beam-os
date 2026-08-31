# Agent entry point

Plan work: Before selecting, implementing, reviewing, or closing a task, read `docs/plan/README.md`, then the assigned task file and the context it points to. The repository plan is canonical; `linear_url` fields are provenance only.

Authorization: Read `docs/plan/state.json` before starting work. Implement only tasks whose milestone is authorized and whose status is `ready-for-agent` or `in-progress`. Human gate decisions alone may authorize another milestone.

Plan integrity: After changing task metadata, dependencies, status, or authorization, run `python3 scripts/plan_tool.py validate --root docs/plan` and rebuild `docs/plan/index.json`.
