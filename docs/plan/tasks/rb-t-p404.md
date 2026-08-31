---
schema: "repo-plan/v1"
id: "RB-T-P404"
title: "Implement kernel-provisioned bounded UI streams and ERTS fd mapping"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-E-P210"
  - "RB-T-P401"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-04"
x_linear_id: "ROB-740"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-740/p4-04-implement-kernel-provisioned-bounded-ui-streams-and-erts-fd"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P404: Implement kernel-provisioned bounded UI streams and ERTS fd mapping

## Goal

Expose the native bounded IPC channels to ERTS as pre-opened file descriptors without sockets, fork/exec, or a dynamic driver.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P401, RB-E-P210.

## Deliverables

* Create two unidirectional kernel streams from the compiled boot plan before either process starts.
* Map the BEAM endpoints to fixed, collision-checked input/output descriptors and renderer endpoints to native typed handles.
* Implement read/write/poll/close/nonblocking semantics through the already-qualified descriptor and native-handle layers.
* Enforce declared capacity, per-process accounting, endpoint rights, lifecycle/closure ordering, and no ambient endpoint discovery.

## Acceptance criteria

- [ ] Only the declared renderer and BEAM endpoints can access each stream direction.
- [ ] Both ABI surfaces observe equivalent bytes, EOF, backpressure, readiness, and closure semantics.
- [ ] Process crash/exit closes owned endpoints and wakes blocked peers into documented states.
- [ ] No socket, device node, path lookup, process spawning, shared memory, or NIF is used.
- [ ] Queue memory remains bounded under a non-reading peer.

## Verification

* `just test-ui-streams`
* `just test-cross-abi-ipc`

## Evidence

* Run cross-ABI byte-stream, capacity, closure, process-death, fd-collision, and permission tests.
* Inspect capability/fd inventories at boot and after exit.
* Save queue-depth and waiter traces.

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

Kernel is bounded byte stream only; freeze capacity/atomicity/close/poll behavior and exact fd numbers; no second packet prefix.
### Normative readiness correction — 2026-08-30

The kernel transports bounded bytes and owns endpoint lifecycle. Freeze capacity, atomicity, close, poll, fixed-fd mapping, packet-size, and busy limits. The kernel does not parse ETF or add a second packet prefix.
