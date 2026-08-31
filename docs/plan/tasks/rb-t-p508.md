---
schema: "repo-plan/v1"
id: "RB-T-P508"
title: "Expose runtime identity, kernel metrics, and bounded stress controls"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P506"
  - "RB-T-P403"
  - "RB-T-P507"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-08"
x_linear_id: "ROB-756"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-756/p5-08-expose-runtime-identity-kernel-metrics-and-bounded-stress"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P508: Expose runtime identity, kernel metrics, and bounded stress controls

## Goal

Make the Runtime Lab useful as an observability surface rather than only a decorative demonstration.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-T-P403, RB-T-P506, RB-T-P507.

## Deliverables

* Populate cards for OTP/Elixir/ERTS identity, normal scheduler count, worker PID/generation/restarts, kernel uptime/free/committed pages, protocol connection, and queue/frame/latency status.
* Implement an Elixir-owned bounded stress action covering process churn, timers, binaries, ETS, and GC with start/progress/completion/cancel/failure state.
* Source kernel metrics through an explicit renderer/native capability and versioned protocol message, not unrestricted kernel memory.
* Rate-limit and bound metric sampling and updates.

## Acceptance criteria

- [ ] Every displayed metric names source, unit, sample time, and unavailable/stale behavior.
- [ ] The stress action remains bounded and the UI stays interactive throughout.
- [ ] Kernel metrics cannot be requested outside the renderer's declared capability.
- [ ] Metric/status messages cannot mutate feature state or bypass protocol limits.
- [ ] Values correlate with serial/kernel/BEAM evidence within declared sampling tolerance.

## Verification

* `just test-runtime-metrics`
* `just test-ui-stress`

## Evidence

* Run normal, max-stress, cancel, stale, unavailable, and disconnect cases.
* Compare displayed values with source telemetry.
* Measure metric update load and queue depth.

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

Separate native telemetry from feature model; pin sources/units/staleness and avoid telemetry echo loop.
### Normative readiness correction — 2026-08-30

Keep `application_state` and `native_telemetry` as separate namespaces. Elixir is authoritative for feature state; renderer/kernel are authoritative for native telemetry and heartbeat. Do not route kernel telemetry through Elixir merely to echo it back.
