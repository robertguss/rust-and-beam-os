# Rust + BEAM Mobile OS POC

This repository contains an evidence-gated AArch64 Rust operating-system
experiment hosting upstream Erlang/OTP, Elixir, and an isolated Rust renderer.

Phase 0 evidence work has started. Kernel implementation remains blocked until
Gate 0 is explicitly approved. The repository plan is the source of truth:

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

Bootstrap a Linux checkout and run all current checks with:

```sh
./scripts/bootstrap.sh
```

The script installs the candidate Rust toolchain and `just` version recorded in
[`toolchain/bootstrap-tools.json`](toolchain/bootstrap-tools.json), then runs
`just check`. See [`docs/development.md`](docs/development.md) for
prerequisites, individual commands, and the distinction between candidate
bootstrap tools and Gate-0-frozen toolchains.
