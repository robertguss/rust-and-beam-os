---
schema: "repo-plan/v1"
id: "RB-T-P512"
title: "Build QMP screenshot and visual-regression checks"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P505"
  - "RB-T-P508"
  - "RB-T-P510"
  - "RB-T-P506"
  - "RB-T-P509"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-12"
x_linear_id: "ROB-758"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-758/p5-12-build-qmp-screenshot-and-visual-regression-checks"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P512: Build QMP screenshot and visual-regression checks

## Goal

Turn the key visual states into repeatable evidence without making pixel identity the only correctness oracle.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P505, RB-T-P506, RB-T-P508, RB-T-P509, RB-T-P510.

## Deliverables

* Use QMP to drive lifecycle and capture screenshots for connecting, ready, counter update, stress, worker restarting/recovered, BEAM disconnected, and incompatible states.
* Define stable landmarks, regions, masks, color/tolerance policy, font-rendering variance, and per-runner baselines.
* Pair screenshots with semantic state hashes and serial/protocol sentinels so a visually similar incorrect state cannot pass.
* Store approved baselines with source/image/toolchain provenance.

## Acceptance criteria

- [ ] Every named state produces both semantic evidence and a screenshot containing its required landmarks.
- [ ] A deliberately wrong value/state fails even if most pixels match.
- [ ] Permitted antialias/font variance does not make the suite flaky.
- [ ] Baselines are separate when TCG/HVF rendering differs materially.
- [ ] Baseline updates require an explicit reviewed reason.

## Verification

* `just test-ui-screenshots-tcg`
* `just test-ui-screenshots-hvf`

## Evidence

* Run deterministic screenshot suites on both runner profiles.
* Inject one semantic and one visual regression to prove detection.
* Publish baseline inventory and comparison report.

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

Good paired semantic/visual evidence. Treat QMP capture timing as visual evidence, not precise host-visible latency.
