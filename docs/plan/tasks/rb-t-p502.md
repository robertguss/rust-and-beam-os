---
schema: "repo-plan/v1"
id: "RB-T-P502"
title: "Integrate virtio pointer input and normalize semantic pointer events"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-G-GATE4"
  - "RB-T-P012"
  - "RB-T-P111"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-02"
x_linear_id: "ROB-747"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-747/p5-02-integrate-virtio-pointer-input-and-normalize-semantic-pointer"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P502: Integrate virtio pointer input and normalize semantic pointer events

## Goal

Deliver bounded, device-independent pointer events to the renderer through an exclusive native capability.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-G-GATE4, RB-T-P012, RB-T-P111.

## Deliverables

* Integrate the selected virtio input device transport, queue, interrupts, reset, and teardown in the kernel device layer.
* Translate raw absolute/relative coordinates, buttons, motion, press/release, and bounds into a documented native event format.
* Define cursor bounds, scaling, button state, event timestamp, ordering, motion coalescing, overflow, and device loss.
* Expose input only through the renderer's declared read/wait handle and instrument queue/drop/coalescing counters.

## Acceptance criteria

- [ ] Scripted motion and clicks produce correct normalized coordinates/button transitions on TCG and HVF.
- [ ] Press/release events are never silently dropped; only motion is coalesced by documented policy.
- [ ] Queue overflow, device reset, malformed descriptors, and renderer exit have bounded behavior.
- [ ] BEAM has no direct input-device capability.
- [ ] Event timestamps use the shared monotonic clock.

## Verification

* `just test-input-tcg`
* `just test-input-hvf`
* `just compare-input-traces`

## Evidence

* Run identical scripted input traces on TCG and HVF.
* Test edges, corners, rapid motion, press/move/release, overflow, reset, and process exit.
* Save raw-to-normalized fixtures and counters.

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

Freeze exact QEMU input frontend/device mapping, coordinate transform, press/release conservation, coalescing, reset, and hot-loss behavior.
