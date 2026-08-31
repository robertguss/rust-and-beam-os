---
schema: "repo-plan/v1"
id: "RB-T-P501A"
title: "Implement VirtIO GPU transport, status, features, and reset"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P501"
depends_on:
  - "RB-G-GATE4"
  - "RB-T-P500"
  - "RB-T-P012"
  - "RB-T-P111"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-01a"
x_linear_id: "ROB-813"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-813/p5-01a-implement-virtio-gpu-transport-status-features-and-reset"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P501A: Implement VirtIO GPU transport, status, features, and reset

## Goal

Implement the frozen GPU transport and complete VirtIO initialization/reset state machine before creating display resources.

## Context

[RB-E-P501](<rb-e-p501.md>)

## Deliverables

* Freeze MMIO/PCI transport, VERSION_1, feature negotiation, FEATURES_OK, status, reset, and timeout
* Validate queue size, alignment, descriptors, barriers, interrupt acknowledgement, and device generation
* Audit pinned crate behavior and patch, replace, or narrow missing semantics
* Inject malformed, stalled, and reset device responses

## Acceptance criteria

* TCG and HVF semantic profiles complete the same admitted state machine
* Missing features and incorrect reset fail closed
* No stale completion or DMA access crosses device generation

## Verification

`just test-gpu-transport` and `just audit-virtio-gpu-init`

## Evidence

`just test-gpu-transport` and `just audit-virtio-gpu-init`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
