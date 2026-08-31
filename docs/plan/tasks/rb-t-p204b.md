---
schema: "repo-plan/v1"
id: "RB-T-P204B"
title: "Implement mprotect, munmap, VMA splitting, merge, and rollback"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P204"
depends_on:
  - "RB-T-P204A"
  - "RB-T-P114"
  - "RB-T-P205C"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-04b"
x_linear_id: "ROB-812"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-812/p2-04b-implement-mprotect-munmap-vma-splitting-merge-and-rollback"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P204B: Implement mprotect, munmap, VMA splitting, merge, and rollback

## Goal

Make permission changes and unmapping transactional and safe across faults, user copy, teardown, and later SMP shootdowns.

## Context

[RB-E-P204](<rb-e-p204.md>)

## Deliverables

* Implement exact split/merge and partial-range semantics
* Enforce W^X and route page-table changes through RB-T-P114
* Serialize with user-copy/address-space lifetime rules
* Block multi-CPU destruction/reuse on acknowledged RB-T-P205C shootdowns

## Acceptance criteria

* Failure at every step restores the prior VMA/page-table/accounting state
* Unmap/protect races with faults and user copy produce documented outcomes
* No page, table, ASID, or mapping is reclaimed before required acknowledgement

## Verification

`just test-vma-protect-unmap` and `just stress-vm-races`

## Evidence

`just test-vma-protect-unmap` and `just stress-vm-races`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
