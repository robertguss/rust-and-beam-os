---
schema: "repo-plan/v1"
id: "RB-T-P507"
title: "Connect pointer actions through Rust, kernel IPC, ERTS port, and Elixir"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P407"
  - "RB-T-P502"
  - "RB-T-P506"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-07"
x_linear_id: "ROB-755"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-755/p5-07-connect-pointer-actions-through-rust-kernel-ipc-erts-port-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P507: Connect pointer actions through Rust, kernel IPC, ERTS port, and Elixir

## Goal

Prove the complete input path from QEMU pointer action to Elixir state transition and visible pixels.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P407, RB-T-P502, RB-T-P506.

## Deliverables

* Perform hit testing in the renderer and translate pointer gestures into allowlisted semantic actions rather than raw UI implementation details.
* Send sequenced events through the final protocol, show pending/disabled state where required, and apply the resulting Elixir snapshot/patch.
* Implement counter increment/decrement and one harmless status action first.
* Correlate raw input, normalized event, semantic action, protocol sequence, Elixir transition, returned model, redraw, and present timestamps.

## Acceptance criteria

- [ ] Every scripted button press reaches exactly one specified accepted/failed outcome and is sequence-accounted.
- [ ] Counter state changes only in Elixir and the visible value matches the authoritative returned model.
- [ ] Motion coalescing does not remove press/release transitions.
- [ ] Rapid/repeated/out-of-bounds/disabled presses follow documented behavior.
- [ ] A disconnect during an action becomes visibly unresolved/failed rather than falsely successful.

## Verification

* `just test-ui-actions-tcg`
* `just test-ui-actions-hvf`
* `just trace-ui-click`

## Evidence

* Run end-to-end scripted input on TCG and HVF.
* Inject disconnect at each path stage and inspect sequence accounting.
* Save one fully correlated click trace.

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

Define accepted/terminal outcomes, current-session sequence, disabled/pending behavior, and disconnect at each stage.
