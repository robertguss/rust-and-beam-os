---
schema: "repo-plan/v1"
id: "RB-T-P503B"
title: "Implement the mapped-surface and present-completion client"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P503"
depends_on:
  - "RB-T-P503A"
  - "RB-T-P501C"
  - "RB-T-P500"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-03b"
x_linear_id: "ROB-818"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-818/p5-03b-implement-the-mapped-surface-and-present-completion-client"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P503B: Implement the mapped-surface and present-completion client

## Goal

Consume RB-T-P500 from userspace without exposing device authority or allowing writes to queued buffers.

## Context

[RB-E-P503](<rb-e-p503.md>)

## Deliverables

* Map only the currently owned writable+NX surface
* Implement generation-safe acquire, draw, present, completion, release, and reset handling
* Validate dirty rectangles and frame sequences client-side and rely on kernel validation
* Handle stale, duplicate, failed, and disconnected completions

## Acceptance criteria

* Client never writes a queued/displayed buffer
* Surface replacement/reset cannot expose stale pages or handles
* Stress returns mappings and handles to exact baseline

## Verification

`just test-renderer-surface-client`

## Evidence

`just test-renderer-surface-client`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
