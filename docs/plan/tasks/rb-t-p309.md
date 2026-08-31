---
schema: "repo-plan/v1"
id: "RB-T-P309"
title: "Run the 12-hour ERTS stress and memory-stability qualification"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P300"
  - "RB-T-P016"
  - "RB-T-P305"
  - "RB-T-P307"
  - "RB-T-P308"
  - "RB-T-P306"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-09"
x_linear_id: "ROB-733"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-733/p3-09-run-the-12-hour-erts-stress-and-memory-stability-qualification"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P309: Run the 12-hour ERTS stress and memory-stability qualification

## Goal

Expose rare runtime/OS interaction failures under sustained processes, timers, messages, binaries, ETS, GC, and native-thread activity.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P305, RB-T-P306, RB-T-P307, RB-T-P308.

## Deliverables

* Create a deterministic mixed Erlang workload with bounded process churn, timers, messages, ETS, binary allocation, forced/natural GC, supervised pure-Erlang crashes, and idle periods.
* Run at least 12 hours with the final SMP profile on four vCPUs.
* Sample BEAM memory/process/run-queue/GC metrics and kernel pages/tasks/VMAs/futex/poll/descriptor counters at bounded frequency.
* Classify any plateau, drift, stall, timeout, unknown syscall, ERTS abort, kernel fault, or trace loss.

## Acceptance criteria

- [ ] The run completes without deadlock, panic, abort, unknown call, or unclassified fault.
- [ ] Memory stabilizes after warm-up; any growth is bounded, explained, and reproducible.
- [ ] Timers and message acknowledgements meet correctness assertions throughout.
- [ ] All native and Erlang processes expected to terminate are accounted for.
- [ ] The run is reproducible from exact image, configuration, and seed.

## Verification

* `just qualify-erts-12h`
* `just analyze-erts-stress`

## Evidence

* Run the full duration with independent watchdogs.
* Plot or summarize time-series slopes and high-water marks.
* Replay at least one injected stall/fault to prove capture.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Additional context
### Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.
### Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.
### Readiness-audit correction — 2026-08-30

The official 12-hour run executes only the committed RB-T-P300 stress manifest; no workload, warm-up, sampling, slope, cap, confidence, or runner choice may be revised after results are viewed.

* Use the RB-T-P016-approved full-duration runner and a separate TCG semantic/fault campaign where appropriate. Replace the original implicit TCG assumption if it cannot meet validity/capacity requirements.
* Meet both host-wall and guest-monotonic duration plus every preregistered process/message/timer/ETS/binary/GC/crash/native-thread and quiescent-checkpoint operation floor. A stalled or severely degraded runtime cannot pass by surviving 12 hours.
* Capture exact build/image/platform/contract/workload hashes, production entropy, final ERTS flags, host resources/load, QEMU validity, watchdog state, first failure, and all raw samples before analysis.
* Apply the frozen metric classifications: exact-conservation resources return to baseline at quiescent checkpoints; workload-proportional data matches expected live population; retained pools/caches remain under absolute caps and satisfy the prespecified post-warm-up plateau/slope/confidence rule.
* Report reserved VA, kernel committed pages, ERTS allocator/carrier categories, live process/ETS/binary/timer data, fragmentation/retention, immutable code/image pages, trace buffers, and host-QEMU memory separately. An unexplained aggregate plateau is not enough.
* Record natural-GC behavior and separately labeled forced-GC checkpoints. A final forced GC cannot retroactively convert prior sustained growth, progress loss, or fragmentation outside its threshold into a pass.
* Continuously enforce correctness/progress: message checksums/ack deadlines, timer create/cancel/fire invariants, expected crash containment, scheduler/reduction/run-queue floors, native-thread progress, futex/poll/timer waits, signal delivery/return, and kernel object conservation.
* Trace overflow, missing sample, clock anomaly, counter reset/wrap without handling, artifact truncation, deterministic entropy, runner drift, host interruption, QEMU failure, or insufficient operation count invalidates the run. Reruns remain separate linked results.
* Replay the prescribed injected stall/leak/fault using the same harness before the clean campaign and prove capture/analysis identifies the intended cause.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Replace qualitative stability with pre-frozen warm-up/slope/confidence/resource rules and runner capacity.
### Normative readiness correction — 2026-08-30

Qualification uses the RB-T-P601-frozen warm-up, sample interval, observation windows, exact resource baselines, robust memory-slope estimator and confidence interval, projected-growth budget, outlier/invalid-run classification, retry policy, host-interruption policy, and first-failure preservation. Exact tasks, descriptors, handles, ports, queues, waiters, and mappings return to baseline after cleanup unless a named cache is explicitly admitted. No automatic retry converts a failed run to pass.
