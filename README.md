# Rust + BEAM Mobile OS POC

This repository contains the self-contained implementation plan for an evidence-gated AArch64 Rust operating-system experiment hosting upstream Erlang/OTP, Elixir, and an isolated Rust renderer.

Implementation has not started. The repository plan is the source of truth:

- [Agent plan entry point](docs/plan/README.md)
- [Execution policy](docs/plan/execution-policy.md)
- [Generated task index](docs/plan/generated/index.json)
- [Architecture and validation plan](docs/plan/architecture.md)
- [Implementation-readiness review](docs/plan/readiness-review.md)
- [Reusable planning specification](docs/specs/repo-plan-v1.md)

Validate the plan and list currently executable work with:

```sh
python3 scripts/repo_plan.py check --root docs/plan
python3 scripts/repo_plan.py ready --root docs/plan --json
```
