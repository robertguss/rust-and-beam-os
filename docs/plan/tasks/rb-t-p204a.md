---
schema: "repo-plan/v1"
id: "RB-T-P204A"
title: "Implement the VMA model, brk, and anonymous mappings"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P204"
depends_on:
  - "RB-T-P201"
  - "RB-T-P202"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-04a"
x_linear_id: "ROB-811"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-811/p2-04a-implement-the-vma-model-brk-and-anonymous-mappings"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P204A: Implement the VMA model, brk, and anonymous mappings

## Goal

Implement bounded reservation and demand-zero commitment for the admitted brk and anonymous mmap contract.

## Context

[RB-E-P204](<rb-e-p204.md>)

## Deliverables

* Freeze VMA identity, ordering, overlap, merge, guard, limit, and accounting rules
* Separate virtual reservation from physical commitment
* Implement demand-zero faults and deterministic ENOMEM/rollback
* Admit only observed flags and combinations

## Acceptance criteria

* Model and guest VMA sets agree after randomized operations
* Reservation does not silently commit the full ERTS range
* Fault, limit, overlap, and allocation failures preserve exact accounting

## Verification

`just test-vma-model` and `just stress-anon-mapping`

## Evidence

`just test-vma-model` and `just stress-anon-mapping`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
