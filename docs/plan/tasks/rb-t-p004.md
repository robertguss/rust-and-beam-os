---
schema: "repo-plan/v1"
id: "RB-T-P004"
title: "Trace and document the reference ERTS workload on Linux"
type: "task"
state: "in_progress"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P002"
  - "RB-T-P003"
related: []
actor: "agent"
owner: "amp:T-01a05912-a43d-754e-84fc-d56536c31a76"
defer_until: null
evidence: []
x_legacy_id: "P0-04"
x_linear_id: "ROB-686"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-686/p0-04-trace-and-document-the-reference-erts-workload-on-linux"
x_labels:
  - "ready-for-agent"
---

# RB-T-P004: Trace and document the reference ERTS workload on Linux

## Goal

Establish a source-backed preliminary map of what the pinned ERTS workload asks
from a Unix host.

## Context

[Architecture & Validation Plan](../architecture.md)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run
against the pinned project artifacts and preserve the own-kernel hypothesis.
Host-side programs are scaffolding and evidence only; they do not satisfy the
final POC.

Blocked by: RB-T-P002, RB-T-P003.

## Deliverables

- Run the exact `runtime_lab` boot, stress, crash, and shutdown workloads on
  normal Linux.
- Capture opened files, mappings, signals, native threads, descriptor
  operations, timing calls, polling behavior, process queries, and syscall
  families.
- Cross-reference observations with `erts/emulator/sys/unix`, the upstream build
  profile, and musl call sites.
- Create `abi/beam-host.yaml` revision 0 with observed callers, flags, blocking
  behavior, errors, and planned tests; mark architecture-specific items as
  provisional.

## Acceptance criteria

- [ ] Every observed host interaction is classified as required,
      optional/disabled, build-time only, or unexplained.
- [ ] Each required entry names at least one evidence source and one future
      conformance test.
- [ ] Unknown/unexplained interactions are resolved or explicitly block the
      gate.
- [ ] The trace workload and capture commands are committed and repeatable.

## Verification

- `just trace-reference-runtime`
- `just beam-host-validate`

## Evidence

- Replay the workload twice and compare normalized traces.
- Review the contract against ERTS Unix source and the chosen build flags.
- Save raw and normalized traces with toolchain/build IDs.

## Out of scope

- Do not implement a Linux or Android guest.
- Do not add networking, writable persistent storage, dynamic linking,
  third-party NIFs, or phone hardware.
- Do not weaken an acceptance test merely to make the spike pass.

## Additional context

### Completion rule

Do not mark this issue Done until every acceptance item has a linked test,
trace, build receipt, ADR, or other durable evidence. If an assumption fails,
stop and create or update the relevant decision record instead of silently
changing scope.

### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and
how the saved evidence distinguishes success from an accidental demo.

### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Add source-to-contract coverage and fault/error/cancellation/timeout/exit
scenarios; repeat traces alone are insufficient.

### Normative readiness correction — 2026-08-30

Dynamic traces are necessary but not sufficient. Build a source-to-contract
inventory for the exact frozen musl/ERTS configuration. Exercise fault-injected
allocation, copy, timeout, cancellation, signal, close, thread-start,
thread-exit, and shutdown paths. Every inventoried interaction must be traced,
proven unreachable by configuration, or recorded as an unresolved Gate 0 risk.
Two equal happy-path traces do not establish completeness.
