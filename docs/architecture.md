# Implementation architecture

The canonical researched architecture and validation plan is
[`docs/plan/architecture.md`](plan/architecture.md). This file is the stable
implementation entry point for contributors and records only repository-level
decisions that are active now.

## Authorized boundary

Phase 0 may build host-side probes, target artifacts, conformance tools, and
evidence. The custom kernel remains unimplemented until a human-approved Gate 0
decision authorizes M1. Host-side probes are scaffolding, never final POC proof.

## Ownership map

| Path             | Responsibility                                                      |
| ---------------- | ------------------------------------------------------------------- |
| `kernel/`        | Future project-owned AArch64 kernel; Gate-0 blocked                 |
| `userspace/`     | Future isolated native processes and support code                   |
| `beam/`          | Reference Mix application and ERTS build/integration inputs         |
| `abi/`           | Native ABI and bounded ERTS host-contract schemas                   |
| `protocol/`      | Versioned Rust↔Elixir protocol and fixtures                         |
| `image/`         | Future immutable image manifest and license closure                 |
| `toolchain/`     | Candidate/frozen tool inputs, source lock, and build environment    |
| `xtask/`         | Build, image, run, and evidence orchestration as tasks authorize it |
| `tests/`         | Host, QEMU, musl, OTP, and protocol qualification                   |
| `docs/evidence/` | Machine-validated receipts and source/claim ledger                  |
| `docs/plan/`     | Canonical task graph and authorization state                        |

## Active dependency direction

`just` exposes readable entry points. It may invoke Cargo, `xtask`, and Python,
but the underlying command remains visible in the `justfile`. `xtask` will own
build and image mechanics, not plan authorization. The plan and evidence
validators remain small dependency-free Python programs so a fresh checkout can
validate authorization before installing the Rust toolchain.
