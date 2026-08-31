---
schema: "repo-plan/v1"
id: "RB-T-P108B"
title: "Publish executable segments and enter the isolated EL0 process"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: "RB-E-P108"
depends_on:
  - "RB-T-P108A"
  - "RB-T-P114"
  - "RB-T-P113"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-08b"
x_linear_id: "ROB-809"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-809/p1-08b-publish-executable-segments-and-enter-the-isolated-el0-process"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P108B: Publish executable segments and enter the isolated EL0 process

## Goal

Publish staged code through RB-T-P114, initialize the full hard-float EL0 context, and prove isolated entry, syscall, fault, and exit.

## Context

[RB-E-P108](<rb-e-p108.md>)

## Deliverables

* Use RB-T-P114 D-cache/I-cache/TLB/barrier publication only
* Build deterministic registers, SPSR, stack, TLS, FP state, and entry point
* Enter EL0 through exception return and handle syscall, fault, return, and exit
* Reject stale generations, invalid entry, W+X, and unsupported context

## Acceptance criteria

* A normal hard-float Rust process executes only after RB-T-P113 and RB-T-P114 pass
* Faults terminate only the process and cleanup reconciles exactly
* Stale-code, state-leak, and invalid-entry negative canaries fail

## Verification

`just test-el0-entry` and `just test-executable-publication`

## Evidence

`just test-el0-entry` and `just test-executable-publication`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
