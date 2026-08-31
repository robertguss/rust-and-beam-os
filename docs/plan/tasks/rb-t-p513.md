---
schema: "repo-plan/v1"
id: "RB-T-P513"
title: "Run the interactive Apple Silicon HVF acceptance demonstration"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P512"
  - "RB-T-P511"
  - "RB-T-P510"
  - "RB-T-P508"
  - "RB-T-P509"
  - "RB-T-P507"
  - "RB-E-P501"
  - "RB-T-P504"
  - "RB-T-P505"
  - "RB-T-P502"
  - "RB-E-P503"
  - "RB-T-P506"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-13"
x_linear_id: "ROB-759"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-759/p5-13-run-the-interactive-apple-silicon-hvf-acceptance-demonstration"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P513: Run the interactive Apple Silicon HVF acceptance demonstration

## Goal

Evaluate the complete human-visible POC on the actual intended local host using the final guest image.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-E-P501, RB-T-P502, RB-E-P503, RB-T-P504, RB-T-P505, RB-T-P506, RB-T-P507, RB-T-P508, RB-T-P509, RB-T-P510, RB-T-P511, RB-T-P512.

## Deliverables

* Boot the final M5 image on Apple Silicon with the pinned QEMU/HVF runner profile and interactive display/input.
* Execute counter actions, stress action, 100 supervised Crash Feature cycles, BEAM disconnect/reconnect, and all visible state transitions.
* Collect event-to-visible latency, frame cadence/freezes, message accounting, process memory, queue depth, resource cleanup, screenshots, and subjective interaction notes.
* Record host hardware/macOS/QEMU configuration separately from guest build identity.

## Acceptance criteria

- [ ] Normal event-to-visible latency is below 50 ms p95 and 100 ms p99.
- [ ] The native heartbeat sustains at least 30 fps with no pause over 100 ms during 100 worker crashes.
- [ ] Pointer presses have complete sequence accounting and are never silently lost.
- [ ] Disconnect/reconnect is stable and visible.
- [ ] Combined renderer plus BEAM committed memory remains within 256 MiB or a measured exception is explicitly dispositioned.
- [ ] The demonstration uses no host-side renderer, BEAM process, or protocol bridge.

## Verification

* `just run-gui-hvf`
* `just qualify-gui-hvf`
* `just evidence-check --phase 5`

## Evidence

* Run the full scripted and human-interactive checklist on Apple Silicon.
* Repeat the measured run enough to disclose variance.
* Publish the acceptance bundle, screenshots, metrics, and observed rough edges.

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

Calibrate provisional thresholds to frozen Mac/QEMU/resolution/instrumentation; report guest completion proxy and human-visible observations separately.
### Normative readiness correction — 2026-08-30

Report guest event-to-present-completion and human-visible observations separately. Any event-to-visible threshold requires an explicit host observer, clock correlation, and error bound; calibrate provisional thresholds to the frozen Mac, QEMU, resolution, and instrumentation profile.
