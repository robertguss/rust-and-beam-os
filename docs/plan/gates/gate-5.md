---
id: "GATE-5"
linear_id: "ROB-757"
linear_url: "https://linear.app/robert-guss/issue/ROB-757/gate-5-decide-whether-the-interactive-rustelixir-vertical-slice-is"
title: "Decide whether the interactive Rust/Elixir vertical slice is worth qualifying"
milestone: "M5"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P5-11"
  - "P5-13"
  - "P5-12"
  - "P5-10"
  - "P5-09"
  - "P5-08"
  - "P5-07"
  - "P5-01"
  - "P5-06"
  - "P5-03"
  - "P5-05"
  - "P5-04"
  - "P5-02"
blocks:
  - "P6-01"
---
# GATE-5: Decide whether the interactive Rust/Elixir vertical slice is worth qualifying

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Decide whether the complete demo is responsive, fault-aware, coherent, and promising enough for final qualification and productivity testing.

## Locked context

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

## What to build

* Review the Apple Silicon acceptance bundle, TCG evidence, UI/license ADR, capability boundary, visual states, input accounting, latency/freeze metrics, memory, supervised recovery, and reconnect behavior.
* Score H4 fault containment and make a preliminary H5 productivity judgment.
* Separate fixable POC roughness from evidence that the Rust-renderer/Elixir-state split is unpleasant or unproductive.
* Record Continue to qualification, Repair within M5, replace toolkit, redesign boundary, Narrow, Pivot, or Stop.

## Acceptance criteria

- [ ] Continue requires all explicit interaction thresholds or an evidence-backed approved exception that does not hide architecture failure.
- [ ] The renderer remains responsive and honest across worker crash and BEAM loss.
- [ ] The UI/license decision is explicit and acceptable to the user.
- [ ] No host bridge or fake recovery is present.
- [ ] M6 remains blocked until the user approves the decision.

## Required tests and evidence

* Conduct a fresh-session review using only repository plan content and evidence.
* Perform the demo for the user or preserve an equivalent reviewable capture.
* Publish gate ADR/status update and exact next issue.

## Verification commands

* `just gate-report 5`
* `just evidence-check --phase 5`

## Dependencies

Blocked by: P5-01, P5-02, P5-03, P5-04, P5-05, P5-06, P5-07, P5-08, P5-09, P5-10, P5-11, P5-12, P5-13.

## Out of scope

* GPU acceleration, browser/web runtime, Android UI compatibility, networking, writable storage, audio/camera/sensors, and physical phone hardware.
* Sending drawing commands or executable UI code from Elixir.
* Moving virtio queues, DMA, or unrestricted MMIO into the renderer.

## Completion rule

Done requires both semantic and visual evidence from the exact guest. A screenshot alone cannot prove correctness; every state must correlate with protocol, runtime, and kernel evidence.

## Learning checkpoint

Explain device-versus-renderer ownership, the click-to-pixel path, the failure boundary this slice demonstrates, and what measurement would falsify the design.

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Require P5-00, corrected metrics, calibrated thresholds, exact action ledger, and explicit UI/license compliance.
