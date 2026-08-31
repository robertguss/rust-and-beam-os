---
schema: "repo-plan/v1"
id: "RB-T-P408"
title: "Enforce UI backpressure, disconnect, reconnect, and last-valid-model behavior"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P407"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-08"
x_linear_id: "ROB-738"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-738/p4-08-enforce-ui-backpressure-disconnect-reconnect-and-last-valid"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P408: Enforce UI backpressure, disconnect, reconnect, and last-valid-model behavior

## Goal

Ensure overload or endpoint failure degrades visibly and boundedly instead of freezing BEAM, renderer, or kernel memory.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P407.

## Deliverables

* Implement bounded per-direction queues and explicit policies: never silently drop button presses; coalesce pointer motion; replace stale view patches; rate-limit metrics/status.
* Define high-water, full, peer-not-reading, closure, BEAM restart, renderer restart, reconnect, resnapshot, and permanent-incompatibility behavior.
* Preserve and mark the last valid Rust view model while disconnected; do not invent successful Elixir state changes.
* Expose queue depth, drops/coalesces, acknowledgements, reconnect attempts, and state transitions to telemetry.

## Acceptance criteria

- [ ] A non-reading peer cannot exceed declared kernel/userspace queue memory.
- [ ] Every accepted button press is acknowledged or reaches a visible failed/disconnected outcome.
- [ ] Only allowed message classes are coalesced/replaced, with sequence accounting.
- [ ] Disconnect/reconnect produces a fresh compatible snapshot before patches resume.
- [ ] Repeated endpoint restarts do not leak descriptors, ports, processes, waiters, or queues.

## Verification

* `just test-ui-backpressure`
* `just test-ui-reconnect`

## Evidence

* Run slow/non-reading peer, saturation, closure-at-each-transition, restart-loop, and version-mismatch tests.
* Measure scheduler responsiveness and queue high-water marks.
* Save sequence accounting for fault cases.

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

**Action:** KEEP

Good. Add exact queue counts/bytes, producer blocking policy, replacement/coalescing eligibility, and fairness.
