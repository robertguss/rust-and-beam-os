---
schema: "repo-plan/v1"
id: "RB-T-P105A"
title: "Implement page-table primitives and a reference translation model"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P105"
depends_on:
  - "RB-T-P104"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-05a"
x_linear_id: "ROB-806"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-806/p1-05a-implement-page-table-primitives-and-a-reference-translation"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P105A: Implement page-table primitives and a reference translation model

## Goal

Provide bounded AArch64 page-table construction, traversal, permission, and translation primitives with a model oracle.

## Context

[RB-E-P105](<rb-e-p105.md>)

## Deliverables

* Typed descriptors and level/index calculations with overflow and alignment rejection
* Reference model for map, translate, protect, and unmap outcomes
* Explicit ownership of page-table frames and deterministic allocation failure
* No executable publication or ASID lifecycle in this child

## Acceptance criteria

* Model and guest translations agree across randomized mappings
* Malformed, overlapping, misaligned, and out-of-range operations fail without partial mutation
* Every allocated table frame is reclaimed exactly once

## Verification

`just test-page-table-model` and `just test-page-table-primitives`

## Evidence

`just test-page-table-model` and `just test-page-table-primitives`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
