---
schema: "repo-plan/v1"
id: "RB-T-P308"
title: "Qualify 100 boots and 10,000 Erlang-process lifecycle"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P300"
  - "RB-T-P306"
  - "RB-T-P307"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-08"
x_linear_id: "ROB-730"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-730/p3-08-qualify-100-boots-and-10000-erlang-process-lifecycle"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P308: Qualify 100 boots and 10,000 Erlang-process lifecycle

## Goal

Prove repeatable boot and lightweight-process behavior at a meaningful but bounded POC scale.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P306, RB-T-P307.

## Deliverables

* Automate 100 complete ERTS boot/workload/halt cycles using the final SMP profile and immutable image.
* Create 10,000 Erlang processes in controlled batches, exchange checked messages, monitor completion, and terminate them within the configured userland budget.
* Track boot milestones, duration, native tasks, BEAM processes, run queues, pages, VMAs, descriptors, waiters, timers, and unknown calls.
* Preserve the first failing iteration and seed without automatic success-by-retry.

## Acceptance criteria

- [ ] All 100 boots pass with zero hang, kernel panic, ERTS abort, unknown syscall, or cleanup discrepancy.
- [ ] All 10,000 Erlang processes exchange expected messages and terminate.
- [ ] Peak committed memory remains within the declared 192 MiB BEAM budget or produces an explicit measured gate exception.
- [ ] Post-halt kernel accounting returns to the defined baseline each run.

## Verification

* `just qualify-erts-boots`
* `just qualify-erts-processes`

## Evidence

* Run the complete headless qualification on the pinned Linux/TCG runner.
* Replay an injected failing iteration.
* Publish distribution and high-water metrics, not only averages.

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

The official campaign executes only the committed RB-T-P300 boot/process manifest.

* Use fresh full-system launches—never snapshots or retained guest state—with exact artifact/image/platform/contract hashes, production entropy, final two-scheduler profile, approved runner preflight, and no automatic retries.
* A boot passes only after all expected milestones, runtime identity, workload nonce/result, orderly ERTS halt, OS process exit, descriptor/wait/timer/signal cleanup, address-space destruction, TLB acknowledgements, and post-halt exact-resource baseline. Serial output alone is insufficient.
* Record every one of the 100 iterations, including first failure, wall/guest duration, milestone timing, operation counts, native thread topology, peak and final memory/resource counters, trace-loss status, and runner validity. Publish all distributions and outliers, not a filtered average.
* The 10,000-process requirement must meet the preregistered concurrent population and meaningful per-process work/message/checksum/link-or-monitor/timer/cleanup profile. Ten thousand sequential no-op spawns do not satisfy it.
* Verify each process ID/token is created, performs its assigned work, sends/receives exact checked payloads, reaches the intended terminal reason, is observed by the coordinator, and no stale mailbox/timer/ETS/monitor/link/binary state remains at quiescence.
* Memory acceptance uses the RB-T-P300 categories. The 192 MiB BEAM budget is an explicit cap for the named scope, not an aggregate guest/QEMU figure; a proposed exception is a failed criterion until Gate 3 approves a new budget and re-runs the campaign.
* Inject and preserve at least one boot-hang and process-accounting failure before the clean run to prove the harness cannot convert timeout, missing result, skipped iteration, or partial serial log into a pass.
* The campaign is invalid if runner/image/manifest drift, deterministic entropy, trace loss, missing metrics, counter reset, host interruption, or insufficient operation count occurs.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Separate boot reliability and process lifecycle ledgers; preserve first failure, cleanup exactness, and runner classification.
