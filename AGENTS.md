# Agent entry point

Plan work: Before selecting, implementing, reviewing, or closing work, read `docs/plan/README.md` and `docs/plan/execution-policy.md`, then run `python3 scripts/repo_plan.py check --root docs/plan`.

Task selection: Run `python3 scripts/repo_plan.py ready --root docs/plan --json`. Implement only a returned task or an already-owned `in_progress` task. Human gate decisions alone authorize gated milestones.

Plan integrity: Create records with `scripts/repo_plan.py new`. After changing canonical plan content, run `python3 scripts/repo_plan.py build --root docs/plan`, then rerun `check`; commit canonical records and regenerated views together.
