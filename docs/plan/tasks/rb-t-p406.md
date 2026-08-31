---
schema: "repo-plan/v1"
id: "RB-T-P406"
title: "Connect Elixir to fixed descriptors with an fd port"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P009"
  - "RB-T-P402"
  - "RB-T-P404"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-06"
x_linear_id: "ROB-746"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-746/p4-06-connect-elixir-to-fixed-descriptors-with-an-fd-port"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P406: Connect Elixir to fixed descriptors with an fd port

## Goal

Use the standard upstream ERTS port mechanism to exchange framed binary protocol messages with the Rust service.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P402, RB-T-P404, RB-T-P009.

## Deliverables

* Open the pre-provisioned input/output descriptors with `Port.open({:fd, in_fd, out_fd}, [:binary, packet: 4])` or the exact verified equivalent.
* Implement one owning connection process that translates port messages into typed domain events and serializes typed outbound messages.
* Configure bounded busy/queue behavior, lifecycle monitoring, closure/error handling, and restart policy without blocking scheduler processes.
* Validate inbound terms with safe atom behavior, fixed schema, limits, sequence/version rules, and no dynamic code/native extension.

## Acceptance criteria

- [ ] Handshake and bidirectional canonical messages cross the real guest fd-port path.
- [ ] Partial transport reads are hidden by packet framing and oversized packets are rejected as specified.
- [ ] Port closure, owner exit, BEAM shutdown, and malformed input yield bounded observable state.
- [ ] No NIF, linked-in driver, socket, fork/exec, or host bridge is used.
- [ ] The connection process cannot create atoms from untrusted payload data.

## Verification

* `just test-elixir-fd-port`
* `just trace-ui-port`

## Evidence

* Run guest positive, malformed, closure, owner-restart, and scheduler-responsiveness tests.
* Trace port queue lengths and descriptor readiness.
* Compare message bytes with canonical fixtures.

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

Allow unchanged upstream built-in fd port driver; prohibit project/dynamic drivers/NIFs. Add packet_size and busy limits.
### Normative readiness correction — 2026-08-30

Use the unchanged upstream built-in fd port driver with `{packet, 4}`, the frozen `{packet_size, Limit}`, and bounded port/message-queue busy limits. Load no project-specific or dynamically loaded port driver, NIF, or native extension. Test ownership, closure in either direction, and busy/backpressure behavior.
