---
schema: "repo-plan/v1"
id: "RB-T-P505"
title: "Implement the opinionated Runtime Lab shell, theme, fonts, and native heartbeat"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P504"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-05"
x_linear_id: "ROB-753"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-753/p5-05-implement-the-opinionated-runtime-lab-shell-theme-fonts-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P505: Implement the opinionated Runtime Lab shell, theme, fonts, and native heartbeat

## Goal

Create the coherent visual shell and an animation whose continuity independently proves renderer responsiveness.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P504.

## Deliverables

* Design and implement the Runtime Lab layout, theme tokens, typography, spacing, focus/pressed/disabled/error states, and bounded embedded font/assets.
* Add a native heartbeat/frame-cadence animation driven entirely by renderer time and redraw logic, not BEAM messages.
* Define fixed screenshot landmarks and deterministic test data mode while preserving a polished interactive mode.
* Render loading, ready, degraded, disconnected, and fatal-renderer/device states.

## Acceptance criteria

- [ ] The screen is readable and coherent at the selected QEMU display resolution.
- [ ] The heartbeat animates before BEAM connects and continues through protocol silence.
- [ ] All assets are immutable, inventoried, licensed, and within the renderer budget.
- [ ] Deterministic mode produces stable landmarks for QMP screenshot tests.
- [ ] No application feature policy is embedded in the shell.

## Verification

* `just test-runtime-lab-shell`
* `just screenshot-runtime-lab`

## Evidence

* Run host/mock layout tests and guest render smoke.
* Capture deterministic screenshots on TCG and HVF.
* Measure idle and heartbeat frame cadence.

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

Enforce single renderer-thread Slint rule, bundled font determinism, bounded layout, local heartbeat independent of BEAM and protocol queues.
