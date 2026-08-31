---
schema: "repo-plan/v1"
id: "RB-T-P105B"
title: "Freeze kernel/user virtual layout and implement address-space lifecycle"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P105"
depends_on:
  - "RB-T-P105A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-05b"
x_linear_id: "ROB-804"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-804/p1-05b-freeze-kerneluser-virtual-layout-and-implement-address-space"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P105B: Freeze kernel/user virtual layout and implement address-space lifecycle

## Goal

Define the canonical virtual layout and create, activate, reference, destroy, and account isolated address spaces.

## Context

[RB-E-P105](<rb-e-p105.md>)

## Deliverables

* Freeze kernel/user ranges, guard regions, stack policy, and reserved holes
* Define address-space generation, lifetime/read locking, ownership, and teardown
* Prevent cross-process or kernel mapping exposure
* Publish machine-readable layout and accounting

## Acceptance criteria

* Fresh and reused address spaces contain no stale user data or mappings
* Destroy waits for permitted users and reconciles all tables/frames
* Kernel mappings remain protected and identical where required

## Verification

`just test-address-space-lifecycle` and `just audit-virtual-layout`

## Evidence

`just test-address-space-lifecycle` and `just audit-virtual-layout`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
