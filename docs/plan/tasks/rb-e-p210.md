---
schema: "repo-plan/v1"
id: "RB-E-P210"
title: "TRACKING: Complete streams, descriptor lifecycle, and poll readiness"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P210B"
  - "RB-T-P210A"
  - "RB-T-P200"
  - "RB-E-P205"
  - "RB-T-P203"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-10"
x_linear_id: "ROB-722"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-722/p2-10-tracking-complete-streams-descriptor-lifecycle-and-poll"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P210: TRACKING: Complete streams, descriptor lifecycle, and poll readiness

## Goal

Provide bounded descriptor and readiness semantics for ERTS polling and the future fixed-fd UI port.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P203, RB-E-P205.

## Deliverables

* Implement bounded kernel byte streams with atomic admitted write size, capacity, backpressure, EOF, broken-pipe, and endpoint closure semantics.
* Expose the contracted pipe/descriptor operations, nonblocking flags, vector I/O, and `poll`/`ppoll` readiness path used by portable ERTS polling.
* Make readiness registration race-safe with concurrent read/write/close/timeout and thread/process exit.
* Instrument queue depth, blocked readers/writers, wake reason, bytes, closures, and overflow attempts.

## Acceptance criteria

- [ ] Blocking and nonblocking probes match documented capacity, partial-I/O, EOF, broken-pipe, and readiness behavior.
- [ ] No readiness notification is lost between condition check and waiter registration.
- [ ] Closing either endpoint wakes every affected waiter exactly into a legal outcome.
- [ ] Descriptor reuse cannot deliver an event to a stale registration.
- [ ] All buffers and waiter collections are bounded.

## Verification

* `just test-pipes`
* `just test-poll`
* `just stress-readiness`

## Evidence

* Run pipe capacity, producer/consumer, closure, reuse, timeout, and poll-race tests.
* Differentially test the admitted subset against Linux.
* Stress on four vCPUs with stored seeds.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit implementation split — 2026-08-30

This issue is now a tracking and integration issue. New implementation belongs in:

* RB-T-P210A for bounded byte streams, endpoint and descriptor lifetime, I/O semantics, flags, closure, reuse, and accounting.
* RB-T-P210B for level-triggered readiness, atomic check/register/recheck, poll timeouts/results, stale-registration prevention, and close/reuse races.
* RB-T-P209C for later signal interruption of completed blocking operations.

The parent is Done only after both children pass and integrated testing proves:

- [ ] Every stream, endpoint, descriptor, buffer, waiter, and registration has a documented owner, generation, lifetime, and bound.
- [ ] EOF, hangup, error, writable capacity, no-reader, timeout, close, and invalid descriptor states have exact readiness semantics.
- [ ] Fixed descriptor installation for the future ERTS fd port works without a shell or general process spawning.
- [ ] One million bidirectional bounded frames complete without silent byte loss, lost readiness, deadlock, stale-generation delivery, or resource drift.
- [ ] The wait path passes once without signals and again after RB-T-P209C adds interruption semantics.
### Implementation-readiness disposition — 2026-08-30

**Action:** TRACKING

Correct conversion. Remove ready-for-agent; children 10a–b own implementation. Keep signal-interruption integration in RB-T-P209C.
