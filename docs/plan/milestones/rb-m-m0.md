---
schema: "repo-plan/v1"
id: "RB-M-M0"
title: "De-risk Artifacts & Contracts"
type: "milestone"
order: 0
authorized_by: null
x_legacy_id: "M0"
---
## Outcome

Resolve the riskiest external assumptions before investing in the kernel: exact runtime artifacts, Mix-release pairing, cross-host display/input, and the Rust↔Elixir protocol.

## Scope

* Pin Rust, QEMU, musl, OTP, Elixir, and C toolchains with hashes and build receipts.
* Build and trace the reference `runtime_lab` release on Linux.
* Cross-build a static, non-JIT AArch64-musl upstream `beam.smp`.
* Pair a genuine Mix release with the target ERTS and start it without an interactive shell.
* Prove virtio display and pointer input under Linux/TCG and macOS/HVF.
* Prove the bounded ETF protocol over pipes using ordinary Linux processes.
* Freeze ADRs for target, ERTS profile, display transport, UI toolkit/license, and release assembly.

## Exit criteria

* Every spike passes from a clean reproducible build.
* The target ERTS runs the reference Erlang/Elixir workload on AArch64 Linux.
* A real Mix release boots with the paired target ERTS.
* Display and input work on both required host profiles.
* Protocol fixtures, malformed-input behavior, backpressure, and disconnect behavior pass.
* `beam-host.yaml` revision 0 and all Phase 0 evidence are committed.
* RB-G-GATE0 records Authorize M1, Pivot, Narrow, or Stop; M1 remains blocked without explicit human **Authorize M1**.

## Stop conditions

Stop or pivot if upstream ERTS requires semantic runtime patches, Mix pairing fails, out-of-scope runtime dependencies are unavoidable, or the selected QEMU device path cannot work under both HVF and TCG.

## Implementation-readiness status — 2026-08-30

**Executable with repairs; this is the only authorized milestone.** Gate 0 is an evidence gate, not a documentation checkbox. It may authorize M1 only after the exact artifact/release closure, source-plus-trace host contract, versioned platform, device/UI/license probes, runner feasibility, and prior-art risks pass with durable evidence and explicit human approval.
