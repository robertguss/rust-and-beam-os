---
schema: "repo-plan/v1"
id: "RB-T-P409"
title: "Qualify the Rust loopback service with one million messages and malformed input"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P400"
  - "RB-T-P406"
  - "RB-T-P407"
  - "RB-T-P408"
  - "RB-T-P405"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-09"
x_linear_id: "ROB-742"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-742/p4-09-qualify-the-rust-loopback-service-with-one-million-messages-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P409: Qualify the Rust loopback service with one million messages and malformed input

## Goal

Prove the complete guest Rust↔BEAM boundary under sustained traffic and adversarial protocol inputs before adding graphics.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P405, RB-T-P406, RB-T-P407, RB-T-P408.

## Deliverables

* Create a minimal native Rust loopback/service process using the final handles, codec, protocol state machine, and telemetry interfaces.
* Run one million bounded bidirectional messages across varied valid message types with sequence and payload checks.
* Inject canonical malformed/oversized frames, invalid terms, sequence errors, endpoint pauses, closures, and restarts during load.
* Track bytes, messages, latency, queue depth, coalescing, errors, memory, scheduler run queues, and resource cleanup.

## Acceptance criteria

- [ ] All expected messages complete with zero corruption, unexplained loss, deadlock, or unbounded memory growth.
- [ ] Every adversarial input produces the specified error/recovery and neither OS process crashes.
- [ ] BEAM schedulers remain responsive during transport pressure.
- [ ] Endpoint closure/restart converges or stops within the specified bound.
- [ ] Final page/descriptor/port/process/waiter accounting returns to baseline.

## Verification

* `just qualify-ui-ipc`
* `just analyze-ui-ipc`

## Evidence

* Run deterministic stress and fault campaigns on the final guest image.
* Replay injected failure positions.
* Publish p50/p95/p99 latency and high-water metrics.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Additional context
### Completion rule

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.
### Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Use mixed sizes/directions, saturation, closure, reconnect, malformed/decompression bombs, resource slopes, and sequence conservation.
