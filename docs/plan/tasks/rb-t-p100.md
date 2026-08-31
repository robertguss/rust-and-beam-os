---
schema: "repo-plan/v1"
id: "RB-T-P100"
title: "Freeze single-CPU IRQ, preemption, locking, and exception-stack invariants"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P103"
  - "RB-T-P102"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-00"
x_linear_id: "ROB-801"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-801/p1-00-freeze-single-cpu-irq-preemption-locking-and-exception-stack"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P100: Freeze single-CPU IRQ, preemption, locking, and exception-stack invariants

## Goal

Define and prove the kernel execution-context rules that every M1 interrupt, scheduler, allocator, VM, wait-queue, tracing, process-exit, and user-copy path depends on.

## Context

Blocked by RB-T-P102 and RB-T-P103.
Blocks RB-E-P106, RB-T-P109, RB-T-P112, and RB-G-GATE1.

## Deliverables

* Define exception/IRQ entry stacks, guard pages, nesting limit, saved context, and current-task/per-CPU access.
* Define IRQ-disable and preemption-disable nesting, ownership, restoration, and assertions.
* Define lock classes: IRQ-safe spin lock, task-only spin/mutex where applicable, and waitable objects.
* Define lock ordering and prohibit sleeping, user copy, or blocking allocation while holding non-sleepable locks.
* Define whether allocation/logging is permitted in IRQ or panic context and provide bounded emergency paths where needed.
* Define scheduler-entry/reentrancy rules and the task-state transition linearization points.
* Define the single-CPU sleep/wakeup publication invariant and compiler-ordering requirements.
* Instrument violations with structured, non-recursive failure records.
* Add a machine-readable lock/context inventory linked to callers.

## Acceptance criteria

* Nested IRQ/preemption-disable state restores exactly and never enables interrupts early.
* Timer IRQ at every injected critical boundary cannot corrupt allocator, VM, handle, wait, or task state.
* Sleep-in-IRQ, sleep-while-spinlocked, lock inversion, recursive scheduler entry, and blocking allocation in forbidden context fail deterministically.
* Exception and IRQ stacks cannot overlap user/kernel task stacks and guard faults are classified.
* Every M1 lock/context use appears in the inventory and names its order and context rule.
* Negative canaries prove the harness detects early-enable, lost wake, lock inversion, and stack-overrun defects.

## Verification

* Model tests for context/lock nesting and wait/wake state.
* Guest fault/preemption injection at every annotated boundary.
* Lock-order and forbidden-context assertions.
* Stack guard and nested-exception tests.
* Structured trace replay.

## Evidence

* Model tests for context/lock nesting and wait/wake state.
* Guest fault/preemption injection at every annotated boundary.
* Lock-order and forbidden-context assertions.
* Stack guard and nested-exception tests.
* Structured trace replay.

## Out of scope

SMP ordering, cross-CPU locks/IPIs, NUMA, production real-time guarantees, or lock-free optimization.

## Additional context
### Why this is a blocker

Phase 1 already introduces timer IRQs, preemption, blocking, faults, and shared kernel state. P2’s SMP memory model cannot retroactively make M1’s single-core reentrancy safe. Without a frozen IRQ/preemption/locking contract, implementation agents can independently choose incompatible rules that appear to work until a timer interrupt lands in the wrong critical section.
### Completion rule

Done means every M1 execution context and synchronization primitive has one explicit invariant, linearization point, forbidden-operation rule, negative test, and diagnostic path.
