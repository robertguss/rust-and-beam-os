---
schema: "repo-plan/v1"
id: "RB-T-P501B"
title: "Implement GPU 2D resources, backing, and scanout"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P501"
depends_on:
  - "RB-T-P501A"
  - "RB-T-P500"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-01b"
x_linear_id: "ROB-815"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-815/p5-01b-implement-gpu-2d-resources-backing-and-scanout"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P501B: Implement GPU 2D resources, backing, and scanout

## Goal

Create bounded 2D resources and scanout backing owned by the kernel and tied to RB-T-P500 surface generations.

## Context

[RB-E-P501](<rb-e-p501.md>)

## Deliverables

* Create/attach/detach/unref resources with pinned page ownership
* Configure deterministic scanout and pixel format
* Validate dimensions, stride, byte counts, descriptor chains, and DMA ranges
* Quiesce device use before reclaiming backing

## Acceptance criteria

* Renderer never receives raw queue, MMIO, or DMA authority
* Resource lifecycle survives crash, reset, duplicate completion, and exhaustion
* All pages and handles reconcile to baseline

## Verification

`just test-gpu-resources` and `just audit-gpu-dma-lifetimes`

## Evidence

`just test-gpu-resources` and `just audit-gpu-dma-lifetimes`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
