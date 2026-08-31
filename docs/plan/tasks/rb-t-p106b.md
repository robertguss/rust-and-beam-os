---
schema: "repo-plan/v1"
id: "RB-T-P106B"
title: "Implement the single-CPU preemptive scheduler and task-state machine"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P106"
depends_on:
  - "RB-T-P105C"
  - "RB-T-P100"
  - "RB-T-P106A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-06b"
x_linear_id: "ROB-803"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-803/p1-06b-implement-the-single-cpu-preemptive-scheduler-and-task-state"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P106B: Implement the single-CPU preemptive scheduler and task-state machine

## Goal

Implement one explicit task-state machine and timer-driven preemption with no duplicate, lost, or concurrently running task.

## Context

[RB-E-P106](<rb-e-p106.md>)

## Deliverables

* Freeze runnable/running/blocked/exiting transitions and linearization points
* Implement context switch, run queue, scheduler-entry, preemption-disable, and idle rules
* Integrate RB-T-P113 FP state without owning its proof
* Bound fairness and expose task-conservation telemetry

## Acceptance criteria

* Task conservation holds across randomized preemption and injected faults
* Recursive scheduler entry and illegal transitions fail deterministically
* Runnable tasks make progress within the frozen single-CPU bound

## Verification

`just test-scheduler-model` and `just stress-preemption-single-core`

## Evidence

`just test-scheduler-model` and `just stress-preemption-single-core`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
