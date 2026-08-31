---
schema: "repo-plan/v1"
id: "RB-E-P501"
title: "TRACKING: Complete VirtIO GPU transport, resources, and present qualification"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P501B"
  - "RB-T-P501A"
  - "RB-T-P501C"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-01"
x_linear_id: "ROB-751"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-751/p5-01-tracking-complete-virtio-gpu-transport-resources-and-present"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P501: TRACKING: Complete VirtIO GPU transport, resources, and present qualification

## Goal

Turn the Phase 0 display probe into a capability-scoped kernel display service without moving driver ownership into userspace.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-G-GATE4, RB-T-P012, RB-T-P111.

## Deliverables

* Integrate the selected MMIO or PCI virtio GPU transport from ADR evidence using DTB/ECAM discovery and the pinned `virtio-drivers` profile.
* Own feature negotiation, queues, DMA buffers, resource creation, scanout, present/flush, interrupts, reset, and teardown in the kernel device layer.
* Expose a narrow native display handle for framebuffer/dirty-region presentation rather than raw virtio queues or unrestricted MMIO.
* Instrument modes, presents, dirty regions, queue depth, interrupts, errors, resets, and frame completion.

## Acceptance criteria

- [ ] The kernel selects a deterministic display mode and presents a test frame on TCG and HVF.
- [ ] Only the renderer's declared handle can access the display API.
- [ ] All DMA memory has explicit ownership/lifetime and cannot alias arbitrary user/kernel pages.
- [ ] Device reset/error/queue exhaustion produces a bounded renderer-visible error and does not corrupt the kernel.
- [ ] The implementation remains behind the platform/device interface selected in Phase 0.

## Verification

* `just test-gpu-tcg`
* `just test-gpu-hvf`
* `just audit-gpu-dma`

## Evidence

* Run TCG/HVF smoke, reset, exhaustion, invalid-buffer, and process-exit tests.
* Compare output with the Phase 0 probe landmarks.
* Audit DMA/unsafe code and save device traces.

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

**Action:** SPLIT/TRACK

Split transport/status/features/reset, 2D resource/scanout, and transfer/flush/fence/error. Block on RB-T-P500.
### Normative readiness correction — 2026-08-30

Freeze and test the complete VirtIO device-status, reset, feature-negotiation, FEATURES_OK, VERSION_1, queue, descriptor, barrier, DMA, interrupt, error, timeout, and teardown semantics for the pinned crate/device/transport. Compilation is not conformance evidence. A missing required feature or incorrect reset/error path blocks the device decision.
