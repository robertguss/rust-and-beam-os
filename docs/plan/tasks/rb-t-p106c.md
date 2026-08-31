---
schema: "repo-plan/v1"
id: "RB-T-P106C"
title: "Implement sleep queues, timeouts, and wakeup linearization"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P106"
depends_on:
  - "RB-T-P106B"
  - "RB-T-P106A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-06c"
x_linear_id: "ROB-808"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-808/p1-06c-implement-sleep-queues-timeouts-and-wakeup-linearization"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P106C: Implement sleep queues, timeouts, and wakeup linearization

## Goal

Provide single-CPU blocking and wakeup primitives with one terminal outcome and no lost wake.

## Context

[RB-E-P106](<rb-e-p106.md>)

## Deliverables

* Define wait-object ownership and check/register/recheck or equivalent protocol
* Implement sleep, wake, timeout cancellation, exit cleanup, and reuse generations
* Use the RB-T-P100 lock/context rules and RB-T-P106A timer source
* Preserve an absolute deadline when a wait is retried

## Acceptance criteria

* Wake-before-sleep, expiry-vs-wake, cancel-vs-fire, exit, and reuse races conserve one outcome
* No waiter remains stranded or wakes a reused task
* Wait queues return to exact baseline after every scenario

## Verification

`just test-wait-queue-model` and `just stress-wake-timeout-races`

## Evidence

`just test-wait-queue-model` and `just stress-wake-timeout-races`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
