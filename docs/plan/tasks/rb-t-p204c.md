---
schema: "repo-plan/v1"
id: "RB-T-P204C"
title: "Implement file-backed read-only mappings only if admitted"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P204"
depends_on:
  - "RB-T-P203"
  - "RB-T-P204A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-04c"
x_linear_id: "ROB-814"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-814/p2-04c-implement-file-backed-read-only-mappings-only-if-admitted"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P204C: Implement file-backed read-only mappings only if admitted

## Goal

Implement only the exact file-backed read-only mapping behavior proven necessary by the frozen musl/ERTS contract; otherwise record it as excluded.

## Context

[RB-E-P204](<rb-e-p204.md>)

## Deliverables

* Gate implementation on an explicit admitted contract entry
* Bind mappings to immutable release-tree objects and open-file-description lifetime
* Reject writable/shared/unsupported flags before side effects
* Define truncation, EOF, fault, close, and teardown behavior

## Acceptance criteria

* When excluded, generated contract/tests prove all such calls fail closed
* When admitted, Linux fixtures match for exact flags, EOF, errors, and lifecycle
* No writable persistence or general filesystem mapping scope is introduced

## Verification

`just test-file-mapping-contract`

## Evidence

`just test-file-mapping-contract`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
