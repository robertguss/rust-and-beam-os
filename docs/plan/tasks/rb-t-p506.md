---
schema: "repo-plan/v1"
id: "RB-T-P506"
title: "Render Elixir-controlled cards and apply snapshots/patches safely"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P505"
  - "RB-T-P407"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-06"
x_linear_id: "ROB-750"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-750/p5-06-render-elixir-controlled-cards-and-apply-snapshotspatches-safely"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P506: Render Elixir-controlled cards and apply snapshots/patches safely

## Goal

Make Elixir the authoritative source of dynamic feature state while Rust owns only rendering and local connection state.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P407, RB-T-P505.

## Deliverables

* Define the typed renderer view model for runtime identity, counter, worker, kernel metric, stress, status, actions, and latency/frame readout cards.
* Map protocol snapshots and patches into validated state transitions and UI properties.
* Preserve the last valid model on invalid/stale messages and visibly mark connection freshness.
* Bound card counts, labels, values, action identifiers, text lengths, and update work per frame.

## Acceptance criteria

- [ ] A canonical Elixir snapshot populates every Runtime Lab card correctly.
- [ ] Valid patches change only declared fields; invalid/stale patches do not partially mutate state.
- [ ] Unknown optional fields are ignored according to v1 rules; unknown required structure is rejected visibly.
- [ ] Elixir controls values, enabled state, and actions without sending drawing commands or arbitrary executable UI code.
- [ ] Rendered text/layout remains within declared bounds for boundary fixtures.

## Verification

* `just test-view-model`
* `just test-view-model-guest`

## Evidence

* Run snapshot/patch property tests through mock backend.
* Run guest canonical, stale, invalid, maximum-size, and reconnect snapshots.
* Compare renderer state hash with Elixir source state.

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

Keep feature state authoritative in Elixir; overlay native telemetry separately; validate full next state before atomic swap.
