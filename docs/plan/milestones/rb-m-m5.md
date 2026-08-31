---
schema: "repo-plan/v1"
id: "RB-M-M5"
title: "Interactive Rust GUI Proof"
type: "milestone"
order: 5
authorized_by: "RB-G-GATE4"
x_legacy_id: "M5"
---
## Outcome

Deliver the human-visible vertical slice: a Rust-rendered Runtime Lab controlled by Elixir, with input, telemetry, and visibly isolated supervised failure.

## Scope

* Kernel virtio GPU/input paths and renderer capabilities.
* Toolkit-neutral `UiBackend` plus the recorded Slint `no_std` software-renderer decision.
* Runtime Lab shell, native heartbeat animation, runtime cards, counter, stress action, and Crash Feature action.
* Pointer event normalization, semantic input events, snapshots/patches, reconnect state, and last-valid-model behavior.
* End-to-end latency, frame cadence, screenshot, and visual-regression evidence.
* Interactive Apple Silicon/HVF run and headless QMP-controlled checks.

## Exit criteria

* Guest event-to-present-completion meets the profile-calibrated provisional 50 ms p95 and 100 ms p99 targets; host-visible pixel claims require a host observer, clock correlation, and error bound.
* Native animation sustains at least 30 fps and never pauses longer than 100 ms during 100 worker crashes.
* Button presses are never silently lost; pointer motion is coalesced only by documented policy.
* BEAM disconnect/reconnect is visible and does not crash the renderer.
* Combined userland committed memory stays within 256 MiB or a measured exception is explicitly accepted.
* RB-G-GATE5 confirms the vertical slice is both technically credible and compelling enough to qualify.

## Implementation-readiness status — 2026-08-30

**Gate-blocked; not authorized.** RB-T-P500 freezes the kernel-owned double-buffered mapped-surface and present-completion capability ABI. VirtIO GPU and renderer work are tracking parents with bounded children. The guest latency metric is event-to-present-completion; host-visible pixel claims require a host observer, clock correlation, and error bound.
