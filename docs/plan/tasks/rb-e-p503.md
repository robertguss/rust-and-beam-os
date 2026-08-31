---
schema: "repo-plan/v1"
id: "RB-E-P503"
title: "TRACKING: Complete renderer bootstrap, surface client, and event/render loop"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P503B"
  - "RB-T-P503A"
  - "RB-T-P503C"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-03"
x_linear_id: "ROB-754"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-754/p5-03-tracking-complete-renderer-bootstrap-surface-client-and"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P503: TRACKING: Complete renderer bootstrap, surface client, and event/render loop

## Goal

Create a separate EL0 renderer that can draw, receive input, talk to BEAM, and fail without compromising the kernel.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P401, RB-E-P501, RB-T-P502.

## Deliverables

* Create `userspace/renderer` as a static no_std-capable Rust process using only native ABI wrappers.
* Provision display, pointer, clock, log, read-only assets, and two UI channel handles through the compiled boot plan.
* Implement the event loop for input readiness, protocol I/O, redraw requests, timers, and display presentation without busy-waiting.
* Define renderer memory/stack limits, panic report, exit cleanup, and restart/non-restart policy for the POC.

## Acceptance criteria

- [ ] The renderer maps no ERTS memory and has no ERTS release-tree or compatibility-ABI access.
- [ ] It presents a local test frame and reacts to pointer events while BEAM is absent.
- [ ] A renderer panic/invalid access terminates only that process and releases device/IPC resources.
- [ ] Idle operation blocks efficiently and does not spin a vCPU.
- [ ] Committed memory remains within its 64 MiB budget.

## Verification

* `just build-renderer`
* `just test-renderer-process`

## Evidence

* Run capability-denial, missing-handle, local-render, idle, panic, and cleanup tests.
* Inspect process mappings/handles and post-exit accounting.
* Save the renderer capability manifest and fault evidence.

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

Split process/capability bootstrap, display-surface client, and render/event/IPC loop. Block on RB-T-P500.
