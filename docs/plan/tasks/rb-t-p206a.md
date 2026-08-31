---
schema: "repo-plan/v1"
id: "RB-T-P206A"
title: "Implement the admitted clone/thread-start and TLS contract"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P206"
depends_on:
  - "RB-T-P200"
  - "RB-E-P204"
  - "RB-T-P205B"
  - "RB-T-P202"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-06a"
x_linear_id: "ROB-787"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-787/p2-06a-implement-the-admitted-clonethread-start-and-tls-contract"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P206A: Implement the admitted clone/thread-start and TLS contract

## Goal

Create musl threads with the exact shared-resource, stack, TLS, identity, and startup semantics needed by the pinned runtime, without prematurely claiming exit/join correctness.

## Context

Blocked by: RB-T-P202, RB-E-P204, RB-T-P205B, RB-T-P200.

Blocks: RB-T-P207.

## Deliverables

* Derive the exact `clone` call/flags/argument layout from the pinned AArch64 musl artifact and admit only those combinations.
* Validate flags as a coherent set; reject unsupported modes before allocating or modifying user/kernel state.
* Create a kernel task sharing the required process address space, descriptor table, signal dispositions, and process identity while owning thread state, user stack, TLS register, signal mask, TID, FP/AdvSIMD state, and lifecycle generation.
* Implement parent/child TID initialization writes and rollback semantics for every failure point.
* Establish the AArch64 child register/stack/TLS entry state and parent/child return values exactly as the observed contract requires.
* Define process-vs-thread ownership and locking for address space, descriptors, credentials placeholder, signal tables, and teardown references.
* Do not implement join or clear-child-TID wake here; those depend on the futex primitive and are owned by RB-T-P206B.

## Acceptance criteria

- [ ] Admitted musl thread creation succeeds with correct parent/child returns, TIDs, stack, TLS, inherited mask, shared resources, and isolated thread state.
- [ ] Unsupported flags, invalid pointers, overlapping/invalid stacks, bad TLS, resource exhaustion, and copyout faults create no visible partial thread and leak no object.
- [ ] Parent/child TID writes have explicit ordering and rollback; a child cannot run before all required user-visible/kernel state is published.
- [ ] Concurrent creation produces unique generation-safe identities and never exposes a reused TID/task prematurely.
- [ ] TLS values remain isolated through preemption and migration.
- [ ] The implementation is compared against reference Linux traces for the exact pinned musl call pattern.

## Verification

* `just test-pthread-start`
* `just stress-pthread-create`
* `just test-clone-rollback`

## Evidence

* C probes for create/start arguments, TLS, inherited signal mask, shared address-space/descriptor behavior, nested creation, bad flags/pointers/stacks/TLS, allocation/copyout failure injection, concurrent identity reuse, and child-before-parent races.
* State-machine/model tests for allocation/publication/rollback.

## Out of scope

* Futex waits/wakes, clear-child-TID wake, join/detach reclamation, robust-list cleanup, signals beyond mask inheritance, fork/exec, namespaces, or general clone flags.

## Additional context
### Completion rule

Done means the exact musl child can be created and enter correctly with atomic publication/rollback, while exit/join remains explicitly unclaimed.
### Learning checkpoint

Explain the admitted clone flag set, which resources are shared versus per-thread, when the child may first run, and how every partial-creation failure rolls back.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Exact pinned musl call pattern and pre-publication rollback are appropriate.
