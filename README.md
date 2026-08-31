# Rust + BEAM Mobile OS POC

This repository contains the self-contained implementation plan for an evidence-gated AArch64 Rust operating-system experiment hosting upstream Erlang/OTP, Elixir, and an isolated Rust renderer.

Implementation has not started. Read the current authorization state before choosing work:

- [Agent plan entry point](docs/plan/README.md)
- [Authorization state](docs/plan/state.json)
- [Architecture and validation plan](docs/plan/architecture.md)
- [Implementation-readiness review](docs/plan/readiness-review.md)

Validate the plan with:

```sh
python3 scripts/plan_tool.py validate --root docs/plan
```
