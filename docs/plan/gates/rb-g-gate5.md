---
schema: "repo-plan/v1"
id: "RB-G-GATE5"
title: "Decide whether the interactive Rust/Elixir vertical slice is worth qualifying"
type: "gate"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P511"
  - "RB-T-P513"
  - "RB-T-P512"
  - "RB-T-P510"
  - "RB-T-P509"
  - "RB-T-P508"
  - "RB-T-P507"
  - "RB-E-P501"
  - "RB-T-P506"
  - "RB-E-P503"
  - "RB-T-P505"
  - "RB-T-P504"
  - "RB-T-P502"
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
x_legacy_id: "GATE-5"
x_linear_id: "ROB-757"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-757/gate-5-decide-whether-the-interactive-rustelixir-vertical-slice-is"
x_labels:
  - "ready-for-human"
---
# RB-G-GATE5: Decide whether the interactive Rust/Elixir vertical slice is worth qualifying

## Decision

[Architecture & Validation Plan](<../architecture.md>)

Decide whether the complete demo is responsive, fault-aware, coherent, and promising enough for final qualification and productivity testing.

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-E-P501, RB-T-P502, RB-E-P503, RB-T-P504, RB-T-P505, RB-T-P506, RB-T-P507, RB-T-P508, RB-T-P509, RB-T-P510, RB-T-P511, RB-T-P512, RB-T-P513.

## Required evidence

* Conduct a fresh-session review using only repository plan content and evidence.
* Perform the demo for the user or preserve an equivalent reviewable capture.
* Publish gate ADR/status update and exact next issue.

## Acceptance criteria

- [ ] Continue requires all explicit interaction thresholds or an evidence-backed approved exception that does not hide architecture failure.
- [ ] The renderer remains responsive and honest across worker crash and BEAM loss.
- [ ] The UI/license decision is explicit and acceptable to the user.
- [ ] No host bridge or fake recovery is present.
- [ ] M6 remains blocked until the user approves the decision.

## Decision record

Done requires both semantic and visual evidence from the exact guest. A screenshot alone cannot prove correctness; every state must correlate with protocol, runtime, and kernel evidence.

## Out of scope

* GPU acceleration, browser/web runtime, Android UI compatibility, networking, writable storage, audio/camera/sensors, and physical phone hardware.
* Sending drawing commands or executable UI code from Elixir.
* Moving virtio queues, DMA, or unrestricted MMIO into the renderer.

## Additional context
### What to build

* Review the Apple Silicon acceptance bundle, TCG evidence, UI/license ADR, capability boundary, visual states, input accounting, latency/freeze metrics, memory, supervised recovery, and reconnect behavior.
* Score H4 fault containment and make a preliminary H5 productivity judgment.
* Separate fixable POC roughness from evidence that the Rust-renderer/Elixir-state split is unpleasant or unproductive.
* Record Continue to qualification, Repair within M5, replace toolkit, redesign boundary, Narrow, Pivot, or Stop.
### Verification commands

* `just gate-report 5`
* `just evidence-check --phase 5`
### Learning checkpoint

Explain device-versus-renderer ownership, the click-to-pixel path, the failure boundary this slice demonstrates, and what measurement would falsify the design.
### Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Require RB-T-P500, corrected metrics, calibrated thresholds, exact action ledger, and explicit UI/license compliance.
