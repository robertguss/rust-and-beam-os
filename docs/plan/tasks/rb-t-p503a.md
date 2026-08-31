---
schema: "repo-plan/v1"
id: "RB-T-P503A"
title: "Implement renderer process and capability bootstrap"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P503"
depends_on:
  - "RB-T-P500"
  - "RB-T-P401"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-03a"
x_linear_id: "ROB-817"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-817/p5-03a-implement-renderer-process-and-capability-bootstrap"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P503A: Implement renderer process and capability bootstrap

## Goal

Start the isolated native renderer with only the declared display, input, IPC, time, and logging capabilities.

## Context

[RB-E-P503](<rb-e-p503.md>)

## Deliverables

* Freeze process manifest, memory/stack limits, handle rights, and startup validation
* Deny ERTS memory, release tree, Linux personality, raw device, and undeclared handles
* Define panic, exit, cleanup, and restart/non-restart policy
* Prove idle blocking and bounded local heartbeat

## Acceptance criteria

* Capability-denial tests cover every absent right
* Fault/panic terminates only the renderer and returns all resources
* Startup fails closed on missing, duplicate, stale, or overprivileged handles

## Verification

`just test-renderer-bootstrap` and `just audit-renderer-capabilities`

## Evidence

`just test-renderer-bootstrap` and `just audit-renderer-capabilities`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
