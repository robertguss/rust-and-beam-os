---
schema: "repo-plan/v1"
id: "RB-T-P205B"
title: "Make scheduling, blocking, wakeups, and task migration SMP-correct"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P205"
depends_on:
  - "RB-T-P113"
  - "RB-T-P200"
  - "RB-T-P205A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-05b"
x_linear_id: "ROB-785"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-785/p2-05b-make-scheduling-blocking-wakeups-and-task-migration-smp-correct"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P205B: Make scheduling, blocking, wakeups, and task migration SMP-correct

## Goal

Extend the single-CPU scheduler into a four-vCPU scheduler with no lost task, duplicate execution, lost wakeup, unsafe migration, or unbounded priority inversion.

## Context

Blocked by: RB-T-P205A, RB-T-P200.

## Deliverables

* Choose and document the minimal run-queue topology, ownership, task-state machine, enqueue/dequeue linearization points, migration rule, and idle/wakeup protocol.
* Implement cross-CPU wakeups through SGIs/IPIs using RB-T-P200 ordering; a wake racing with block, timeout, exit, cancellation, or migration must be resolved exactly once.
* Define lock ordering, interrupt-context restrictions, preemption-disable semantics, scheduler reentrancy rules, and bounded critical-section expectations.
* Preserve integer, control, TLS, FP/AdvSIMD, address-space, and accounting state across migration; run RB-T-P113's deferred migration tests.
* Define CPU affinity/count behavior required by the host contract, without general Linux policy.
* Implement task conservation/debug assertions and sequence-stamped traces capable of reconstructing ownership transitions.
* Keep a deterministic one-vCPU mode and an optional deterministic scheduling/fault-injection mode for replay.

## Acceptance criteria

- [ ] At every trace point, each live task is in exactly one legal state and is owned by at most one CPU/queue/wait object.
- [ ] No wake is lost and no task is enqueued twice across the complete block/wake/timeout/exit/migration interleaving matrix.
- [ ] Migrated tasks retain address space, TLS, integer, FP/AdvSIMD, and signal-placeholder state with no cross-task leak.
- [ ] Idle CPUs are woken when runnable work is published and do not spin indefinitely under an empty system.
- [ ] Lock-order assertions and deliberately inverted negative tests detect deadlock/priority-inversion hazards.
- [ ] Randomized stress preserves task conservation, bounded queue lengths, forward progress, and reproducible seeds.

## Verification

* `just test-smp-scheduler-model`
* `just stress-scheduler-smp`
* `just test-cross-cpu-wakeups`
* `just test-fpsimd-migration`

## Evidence

* Model-based task-state testing; randomized four-CPU scheduling; forced preemption at each transition; IPI loss/duplication injection; timeout/exit/migration races; FP migration stress; and single-CPU regression.
* Trace replay that reconstructs every task's state sequence and flags illegal ownership.

## Out of scope

* NUMA, production load balancing, real-time guarantees, CPU hotplug, work stealing optimization beyond what evidence requires, or ERTS-specific scheduler changes.

## Additional context
### Completion rule

Done means the scheduler's task-state and wakeup invariants survive exhaustive modeled boundaries and long seeded stress on four vCPUs.
### Learning checkpoint

State the task ownership machine and the exact publication/notification sequence that prevents a wake from being lost as a task transitions to sleep.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. It owns RB-T-P113’s deferred migration tests and exact task-conservation evidence.
