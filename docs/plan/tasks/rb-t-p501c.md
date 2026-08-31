---
schema: "repo-plan/v1"
id: "RB-T-P501C"
title: "Implement transfer, flush, fence, error, and present qualification"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: "RB-E-P501"
depends_on:
  - "RB-T-P500"
  - "RB-T-P501B"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-01c"
x_linear_id: "ROB-816"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-816/p5-01c-implement-transfer-flush-fence-error-and-present-qualification"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P501C: Implement transfer, flush, fence, error, and present qualification

## Goal

Turn RB-T-P500 queued surfaces into bounded transfer/flush completions with exact failure and recovery behavior.

## Context

[RB-E-P501](<rb-e-p501.md>)

## Deliverables

* Submit dirty-region transfer and resource flush with frame sequence and generation
* Define completion/fence proxy, queue bounds, ordering, timeout, reset, and stale completion
* Expose present-completion telemetry without claiming host-visible pixel time
* Qualify both TCG and HVF profiles

## Acceptance criteria

* Each accepted frame has exactly one completed, failed, or reset outcome
* Queued pages are never reused before safe completion
* Delayed, duplicate, missing, reordered, and malformed completions are detected

## Verification

`just test-gpu-present` and `just qualify-gpu-present-profiles`

## Evidence

`just test-gpu-present` and `just qualify-gpu-present-profiles`

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context
### Completion rule

Done means this bounded child behavior is implemented, its negative and concurrency tests pass, and the parent tracking issue can consume its durable evidence.
