---
schema: "repo-plan/v1"
id: "RB-T-P511"
title: "Instrument event-to-present-completion, frame cadence, freezes, and memory"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P508"
  - "RB-T-P505"
  - "RB-T-P507"
  - "RB-T-P509"
  - "RB-T-P510"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-11"
x_linear_id: "ROB-760"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-760/p5-11-instrument-event-to-present-completion-frame-cadence-freezes-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P511: Instrument event-to-present-completion, frame cadence, freezes, and memory

## Goal

Measure interactive viability and fault isolation with shared sequence/timestamp evidence.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P505, RB-T-P507, RB-T-P508, RB-T-P509, RB-T-P510.

## Deliverables

* Carry monotonic timestamps and sequence IDs from normalized input through renderer event, kernel stream, ERTS port, Elixir transition, returned model, redraw, present request, and frame completion where observable.
* Record frame intervals, longest freeze, redraw causes, event-to-visible latency, queue depths, coalescing, CPU/task activity, and committed pages by process.
* Define warm-up, sampling, runner-profile separation, percentile calculation, clock-domain assumptions, and dropped-sample policy.
* Emit JSON Lines keyed by build ID and runner profile.

## Acceptance criteria

- [ ] Metrics distinguish Linux/TCG and macOS/HVF and never compare them as equivalent baselines.
- [ ] Each measured action can be joined end-to-end by sequence ID.
- [ ] p50/p95/p99 latency and longest frame freeze are computed from documented samples.
- [ ] Instrumentation is bounded and does not materially change the measured path without disclosure.
- [ ] Renderer and BEAM memory high-water values reconcile with kernel accounting.

## Verification

* `just test-ui-metrics`
* `just measure-ui-tcg`
* `just measure-ui-hvf`

## Evidence

* Run synthetic known-delay calibration and normal/stress/crash scenarios.
* Validate metric schema and percentile calculations.
* Compare instrumented/non-instrumented frame cadence for observer effect.

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

Rename to event-to-present-completion unless host observer exists; freeze clock domains/error, sample policy, and observer-effect bound.
### Normative readiness correction — 2026-08-30

The guest metric is event-to-present-completion. A host-visible pixel claim requires host capture instrumentation, clock correlation, and a stated error bound. Freeze clock domains, sample policy, observer-effect bound, and profile-calibrated provisional thresholds.
