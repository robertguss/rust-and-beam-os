---
schema: "repo-plan/v1"
id: "RB-T-P108A"
title: "Parse, validate, allocate, and stage a static AArch64 ELF"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P108"
depends_on:
  - "RB-T-P105C"
  - "RB-T-P107"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-08a"
x_linear_id: "ROB-810"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-810/p1-08a-parse-validate-allocate-and-stage-a-static-aarch64-elf"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P108A: Parse, validate, allocate, and stage a static AArch64 ELF

## Goal

Validate the exact admitted ELF shapes and stage segments in writable, non-executable memory without entering EL0.

## Context

[RB-E-P108](<rb-e-p108.md>)

## Deliverables

* Validate ELF class/type, headers, ranges, alignment, overlap, TLS, relocation, interpreter, and dependency policy
* Allocate isolated segments transactionally and copy bytes into writable+NX staging pages
* Construct typed initial-stack and auxv inputs without publishing executable mappings
* Fuzz every structure boundary and allocation rollback point

## Acceptance criteria

* Only frozen artifact shapes are admitted
* Malformed inputs and allocation failures leave no mapping or frame leak
* No staged page is executable or W+X

## Verification

`just test-elf-staging` and `just fuzz-elf-loader`

## Evidence

`just test-elf-staging` and `just fuzz-elf-loader`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
