---
schema: "repo-plan/v1"
id: "RB-T-P510"
title: "Implement BEAM disconnect, reconnect, resnapshot, and last-valid-view UX"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P408"
  - "RB-T-P506"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-10"
x_linear_id: "ROB-749"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-749/p5-10-implement-beam-disconnect-reconnect-resnapshot-and-last-valid"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P510: Implement BEAM disconnect, reconnect, resnapshot, and last-valid-view UX

## Goal

Keep the renderer stable and honest when the application runtime or channel is unavailable.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P408, RB-T-P506.

## Deliverables

* Render explicit connecting, ready, stale/degraded, disconnected, incompatible, resynchronizing, and fatal states.
* Preserve the last valid dynamic view with freshness/error indicators while disabling actions that cannot be accepted.
* On compatible reconnect, perform handshake and full snapshot before accepting patches or new actions.
* Bound reconnect attempts/backoff for the POC and make permanent incompatibility terminal until image replacement.

## Acceptance criteria

- [ ] Killing BEAM does not crash or freeze the renderer or kernel.
- [ ] No action appears successful while disconnected.
- [ ] Reconnect produces a fresh authoritative snapshot and discards obsolete pending state according to protocol.
- [ ] Repeated disconnect/reconnect cycles leak no process, descriptor, queue, timer, or memory resource.
- [ ] Version mismatch is visible and never enters Ready.

## Verification

* `just test-beam-disconnect-ui`
* `just stress-ui-reconnect`

## Evidence

* Inject closure/restart at every protocol state and repeat cycles under load.
* Measure heartbeat continuity and resource accounting.
* Save state-transition screenshots/traces.

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

**Action:** KEEP

Strong. Add session-generation invalidation and exact resource baseline after repeated cycles.
