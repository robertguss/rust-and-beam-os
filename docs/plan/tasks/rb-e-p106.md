---
schema: "repo-plan/v1"
id: "RB-E-P106"
title: "TRACKING: Complete timer IRQs, preemptive scheduling, and wakeup safety"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P106B"
  - "RB-T-P106A"
  - "RB-T-P106C"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-06"
x_linear_id: "ROB-700"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-700/p1-06-tracking-complete-timer-irqs-preemptive-scheduling-and-wakeup"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P106: TRACKING: Complete timer IRQs, preemptive scheduling, and wakeup safety

## Goal

Replace cooperative progress with observable timer-driven scheduling primitives for later native threads.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P103, RB-E-P105.

## Deliverables

* Initialize the architectural generic timer and its interrupt path using discovered platform data.
* Implement monotonic tick/deadline conversion with overflow-safe arithmetic.
* Add a minimal kernel task context, runnable queue, timer preemption, sleep queue, wakeup path, and idle task for one CPU.
* Record context-switch, timer, runnable, sleep, and wake counters in the trace ring.

## Acceptance criteria

- [ ] Two CPU-bound kernel test tasks are preempted rather than relying on voluntary yield.
- [ ] Sleep deadlines fire no earlier than requested and within the declared QEMU tolerance.
- [ ] Wake-before-timeout and timeout/wakeup races have deterministic legal outcomes.
- [ ] No lost-wakeup or run-queue corruption appears in randomized scheduling tests.

## Verification

* `just test-scheduler-host`
* `just test-scheduler-guest`

## Evidence

* Run deterministic scheduler tests with recorded seeds.
* Compare guest monotonic time with QEMU elapsed bounds.
* Save context-switch traces for normal, sleep, wake, and timeout paths.

## Out of scope

* ERTS, Elixir, musl/pthreads, GPU UI integration, networking, writable storage, and phone hardware.
* General POSIX/Linux compatibility or a production security claim.
* Broad optimization before correctness evidence.

## Additional context
### Completion rule

Do not mark Done until every acceptance item has durable evidence from the exact build. Preserve any failing seed or trace; never convert a flake into success by blind retry.
### Learning checkpoint

Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process, the invariant this slice protects, one race or memory-corruption failure mode, and how the tests expose it.
### Implementation-readiness disposition — 2026-08-30

**Action:** SPLIT/TRACK

Block on new RB-T-P100; split timer IRQ, scheduler/preemption, and wait queues. Define state/lock/wakeup invariants first.
### Normative readiness correction — 2026-08-30

RB-T-P100 defines the task-state machine, preemption-disable rules, IRQ nesting, lock classes/order, scheduler reentrancy, wait-object ownership, wake publication/linearization, timeout cancellation, and no-sleep/no-allocation contexts. This parent is tracking-only; RB-T-P106A, RB-T-P106B, and RB-T-P106C own implementation.
