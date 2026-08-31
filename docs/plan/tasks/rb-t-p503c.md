---
schema: "repo-plan/v1"
id: "RB-T-P503C"
title: "Implement the renderer event, render, and IPC loop with backpressure"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P503"
depends_on:
  - "RB-T-P407"
  - "RB-T-P502"
  - "RB-T-P503B"
  - "RB-T-P408"
  - "RB-T-P503A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-03c"
x_linear_id: "ROB-819"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-819/p5-03c-implement-the-renderer-event-render-and-ipc-loop-with"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P503C: Implement the renderer event, render, and IPC loop with backpressure

## Goal

Integrate pointer input, bounded Rust↔BEAM IPC, model updates, heartbeat, drawing, and presentation on one deterministic renderer thread.

## Context

[RB-E-P503](<rb-e-p503.md>)

## Deliverables

* Freeze event priorities, queue byte/object bounds, coalescing, and fairness
* Keep feature application state separate from native telemetry/heartbeat
* Validate a complete next model before atomic swap
* Preserve last-valid view and session generation across disconnect/reconnect

## Acceptance criteria

* No state-changing action is silently dropped and every accepted action reaches one terminal outcome
* Native heartbeat remains responsive under BEAM crash and IPC saturation
* Idle loop blocks; overload remains bounded and observable

## Verification

`just test-renderer-loop` and `just stress-renderer-backpressure`

## Evidence

`just test-renderer-loop` and `just stress-renderer-backpressure`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
