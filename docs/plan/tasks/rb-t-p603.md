---
schema: "repo-plan/v1"
id: "RB-T-P603"
title: "Run the 12-hour complete-system mixed stress qualification"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P602"
  - "RB-T-P601"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-03"
x_linear_id: "ROB-762"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-762/p6-03-run-the-12-hour-complete-system-mixed-stress-qualification"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P603: Run the 12-hour complete-system mixed stress qualification

## Goal

Exercise the kernel, ERTS, Elixir, IPC, renderer, input, and recovery boundary together long enough to reveal cross-layer failures.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P602.

## Deliverables

* Run a deterministic mix of UI actions, supervised crashes, process churn, timers, messages, binaries, ETS, GC, protocol load, input motion/presses, reconnect drills, and idle periods.
* Use bounded workload phases with continuous semantic assertions and independent watchdogs for heartbeat, BEAM progress, protocol progress, and kernel liveness.
* Sample memory, tasks/processes, VMAs, descriptors/handles, ports, waiters, queues, frame intervals, latency, GC, restarts, unknown calls, and faults.
* Classify all drift, stalls, dropped actions, reconnect failures, deadline misses, trace loss, and shutdown discrepancies.

## Acceptance criteria

- [ ] The 12-hour run completes with zero deadlock, panic, abort, unknown syscall, unclassified fault, silent button loss, or invariant violation.
- [ ] Memory/resources stabilize after warm-up with no monotonic leak.
- [ ] The renderer heartbeat and input remain responsive through declared crash/load phases.
- [ ] Every injected failure reaches its specified recovery/degraded state.
- [ ] The run is reproducible from image, manifest, workload schedule, and seed.

## Verification

* `just qualify-complete-12h`
* `just analyze-complete-stress`

## Evidence

* Run the frozen campaign on the declared qualification runner.
* Replay one injected fault position and one shortened deterministic segment.
* Publish time-series slopes, high-water values, and state/sequence conservation.

## Out of scope

* New kernel/runtime/UI features not required by qualification.
* JIT, second hardware target, networking, persistent writable storage, update slots, phone drivers, or production security.
* Hiding failed runs, retroactively weakening thresholds, or presenting the emulator POC as a daily-driver phone OS.

## Additional context
### Completion rule

Done requires the frozen qualification contract, exact image/build provenance, raw and summarized evidence, and honest classification of every failure or exception.
### Learning checkpoint

Explain what the evidence proves, what it does not prove, one source of measurement bias, and the strongest fact that could justify stopping or pivoting.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Use frozen warm-up/slope/confidence/resource criteria and deterministic workload schedule; classify host/runner invalidity separately.
### Normative readiness correction — 2026-08-30

Qualification uses the RB-T-P601-frozen warm-up, sample interval, observation windows, exact resource baselines, robust memory-slope estimator and confidence interval, projected-growth budget, outlier/invalid-run classification, retry policy, host-interruption policy, and first-failure preservation. Exact tasks, descriptors, handles, ports, queues, waiters, and mappings return to baseline after cleanup unless a named cache is explicitly admitted. No automatic retry converts a failed run to pass.
