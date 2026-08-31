---
schema: "repo-plan/v1"
id: "RB-T-P509"
title: "Implement the Crash Feature flow and visible supervised recovery"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P410"
  - "RB-T-P506"
  - "RB-T-P507"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-09"
x_linear_id: "ROB-752"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-752/p5-09-implement-the-crash-feature-flow-and-visible-supervised-recovery"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P509: Implement the Crash Feature flow and visible supervised recovery

## Goal

Deliver the defining demo: an Elixir worker crashes and restarts while Rust rendering visibly continues.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P410, RB-T-P506, RB-T-P507.

## Deliverables

* Wire the Crash Feature semantic action to the intentionally crashable worker path through the normal protocol.
* Show pending/restarting/ready states, prior/new worker identity, generation, restart count, and reason using semantic lifecycle messages.
* Keep the native heartbeat independent of the crashable worker, durable state, and BEAM reply cadence.
* Define failure behavior for supervisor escalation, whole-release exit, and missing recovery snapshot.

## Acceptance criteria

- [ ] One press causes one intentional worker crash and a visibly new generation/restart count.
- [ ] Durable counter/demo state survives the worker crash.
- [ ] The native heartbeat never stops because of the Elixir feature failure.
- [ ] The UI distinguishes worker recovery, supervisor escalation, and BEAM disconnect.
- [ ] No Logger-text parsing, renderer-side fake restart, or host control participates.

## Verification

* `just test-crash-feature`
* `just qualify-visible-recovery`

## Evidence

* Run 100 sequential visible crashes, crash-storm escalation, and BEAM-exit cases.
* Correlate UI frame, protocol, OTP lifecycle, and kernel traces.
* Record a QMP screenshot sequence or short evidence capture around recovery.

## Out of scope

* GPU acceleration, browser/web runtime, Android UI compatibility, networking, writable storage, audio/camera/sensors, and physical phone hardware.
* Sending drawing commands or executable UI code from Elixir.
* Moving virtio queues, DMA, or unrestricted MMIO into the renderer.

## Additional context
### Completion rule

Done requires both semantic and visual evidence from the exact guest. A screenshot alone cannot prove correctness; every state must correlate with protocol, runtime, and kernel evidence.
### Learning checkpoint

Explain device-versus-renderer ownership, the click-to-pixel path, the failure boundary this slice demonstrates, and what measurement would falsify the design.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Replace durable with supervisor-resilient in-memory state; define state reset and whole-release-exit behavior.
### Normative readiness correction — 2026-08-30

The feature state is supervisor-resilient in-memory state. Prove preservation across the worker crash and intentional reset across release, BEAM, or OS restart.
