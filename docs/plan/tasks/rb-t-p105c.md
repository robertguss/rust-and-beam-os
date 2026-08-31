---
schema: "repo-plan/v1"
id: "RB-T-P105C"
title: "Implement single-core map, protect, unmap, ASID, and teardown semantics"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P105"
depends_on:
  - "RB-T-P105B"
  - "RB-T-P114"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-05c"
x_linear_id: "ROB-807"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-807/p1-05c-implement-single-core-map-protect-unmap-asid-and-teardown"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P105C: Implement single-core map, protect, unmap, ASID, and teardown semantics

## Goal

Complete single-core mapping mutation and ASID reuse with exact rollback, W^X, and TLB behavior.

## Context

[RB-E-P105](<rb-e-p105.md>)

## Deliverables

* Map/protect/unmap with split/merge and transactional rollback
* Single-core ASID allocation, generation, exhaustion, and forced small-space wrap tests
* Route translation changes through the RB-T-P114 publication/invalidation API
* Serialize teardown and mutation with address-space lifetime rules

## Acceptance criteria

* No W+X window or stale translation survives any successful operation
* Failure at every allocation boundary restores the prior mapping set
* ASID reuse and unmap/remap canaries fault or translate exactly as modeled

## Verification

`just test-vm-single-core` and `just test-asid-reuse`

## Evidence

`just test-vm-single-core` and `just test-asid-reuse`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
