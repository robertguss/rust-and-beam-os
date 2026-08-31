---
schema: "repo-plan/v1"
id: "RB-T-P106A"
title: "Implement generic timer and GIC IRQ delivery"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P106"
depends_on:
  - "RB-T-P103"
  - "RB-T-P100"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-06a"
x_linear_id: "ROB-805"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-805/p1-06a-implement-generic-timer-and-gic-irq-delivery"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P106A: Implement generic timer and GIC IRQ delivery

## Goal

Deliver bounded single-CPU timer interrupts under the RB-T-P100 context and locking contract.

## Context

[RB-E-P106](<rb-e-p106.md>)

## Deliverables

* Program and acknowledge the generic timer and frozen GIC path
* Define IRQ entry, nesting, masking, rearm, missed-tick, and overflow behavior
* Emit bounded non-recursive traces and watchdog evidence
* No scheduler policy in this child

## Acceptance criteria

* Injected timer IRQs are acknowledged exactly once without early interrupt enable
* Long delays and back-to-back expiries have documented bounded behavior
* Forbidden IRQ-context operations fail deterministically

## Verification

`just test-timer-irq` and `just inject-irq-boundaries`

## Evidence

`just test-timer-irq` and `just inject-irq-boundaries`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
