---
schema: "repo-plan/v1"
id: "RB-T-P002"
title: "Build the Linux reference runtime_lab Mix application"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P003"
  - "RB-T-P001"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-02"
x_linear_id: "ROB-683"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-683/p0-02-build-the-linux-reference-runtime-lab-mix-application"
x_labels:
  - "ready-for-agent"
---
# RB-T-P002: Build the Linux reference runtime_lab Mix application

## Goal

Create the exact high-level workload that every later ERTS and GUI experiment must run.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P001.

## Deliverables

* Create a dependency-minimal Mix application at `beam/runtime_lab`. Avoid Hex dependencies containing native code.
* Implement an OTP supervision tree with a durable-state process, an intentionally crashable worker, generation/restart counters, bounded metric sampling, and restart-intensity escalation.
* Expose deterministic commands for process churn, timers, binaries, ETS activity, garbage collection, crash-once, and crash-storm workloads.
* Route structured runtime identity and lifecycle events to standard output for reference tracing.

## Acceptance criteria

- [ ] The app reports exact Elixir, OTP, ERTS flavor, scheduler, and build identity.
- [ ] A worker crash produces a new generation while durable demo state survives.
- [ ] A crash storm exceeds the configured restart intensity and escalates predictably.
- [ ] Tests cover normal transitions, crash recovery, durable-state ownership, and restart-intensity behavior.
- [ ] The app runs with no network requirement and no application NIF.

## Verification

* `cd beam/runtime_lab && mix test`
* `cd beam/runtime_lab && mix run --no-halt`

## Evidence

* Run unit and supervision tests repeatedly on ordinary Linux.
* Save a reference boot log and workload transcript.
* Record the exact `mix release` inputs used later.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

* This issue is downstream of RB-T-P003. The toolchain issue proves only a minimal smoke project; this issue owns the complete `runtime_lab` reference application.
* “Durable” in this POC means **restart-persistent in-memory state across the intentionally crashing worker only**. It is not persistent across a BEAM/application/system restart because writable storage is out of scope.
* Tests must explicitly distinguish worker restart, supervisor/application restart, BEAM process restart, and complete image reboot; the expected state after each must be specified.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Good reference workload. Ensure no native Hex dependency, include deterministic crash/stress/shutdown cases, and emit workload version/seed.
