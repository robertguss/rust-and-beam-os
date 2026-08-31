---
schema: "repo-plan/v1"
id: "RB-E-P206"
title: "TRACKING: Complete thread start, futex-dependent exit, and reclamation"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P206B"
  - "RB-T-P206A"
  - "RB-E-P205"
  - "RB-T-P202"
  - "RB-E-P204"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-06"
x_linear_id: "ROB-714"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-714/p2-06-tracking-complete-thread-start-futex-dependent-exit-and"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P206: TRACKING: Complete thread start, futex-dependent exit, and reclamation

## Goal

Support the exact musl pthread creation/exit/join substrate used by the pinned runtime.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P202, RB-E-P204, RB-E-P205.

## Deliverables

* Implement only the `clone` flag combination(s) emitted by the pinned musl `pthread_create`; reject all others.
* Create threads sharing the process address space and required resources while owning kernel task state, stack, TLS pointer, and lifecycle state.
* Implement parent/child TID writes, clear-child-TID plus wake on exit, `set_tid_address`, join/detach-relevant lifecycle, and process-wide exit behavior.
* Preserve signal-mask inheritance and TLS/stack guard assumptions required by musl.

## Acceptance criteria

- [ ] C probes pass for create, argument/return value, join, detach, nested creation, TLS isolation, stack guard, thread exit, and process exit.
- [ ] Unsupported clone modes fail without partially creating a task.
- [ ] TID clear/wake behavior cannot miss a joining waiter.
- [ ] All thread stacks, tasks, TIDs, and mappings are reclaimed according to join/detach semantics.
- [ ] Thread creation under four-vCPU contention produces unique identities and correct TLS.

## Verification

* `just test-pthread-lifecycle`
* `just stress-pthread-lifecycle`

## Evidence

* Differentially trace the probes on reference Linux and the guest.
* Run create/exit/join races with deterministic preemption seeds.
* Audit every admitted clone flag and cleanup transition.

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

This issue is now a **tracking/integration issue**, not an agent-sized implementation ticket:

* RB-T-P206A owns admitted `clone` validation, child creation/publication, stack/TLS/TID setup, resource sharing, and atomic rollback.
* RB-T-P207 owns the real futex wait/wake primitive.
* RB-T-P206B owns `set_tid_address`, clear-child-TID, futex wake on exit, join/detach, last-thread exit, and final reclamation.
* RB-T-P208 later supplies robust-mutex owner-death cleanup before the full pthread lifecycle can satisfy the conformance gate.

Do not implement new code directly under this parent. It is Done only when both child issues pass and the combined lifecycle is checked against RB-T-P207/RB-T-P208 with generation-safe TID reuse and exact object conservation.

Additional parent acceptance:

- [ ] Every admitted clone failure point rolls back completely before a child can run.
- [ ] Clear-child-TID plus futex wake is linearizable with join and cannot lose a waiter.
- [ ] Joinable and detached threads each have exactly one legal reclamation path.
- [ ] Stack, TLS, TID, task, FP/SIMD state, mappings, and process references are reclaimed once and only once.
- [ ] Last-thread and process-wide exit semantics match the pinned musl/ERTS contract.
- [ ] One million create/exit/join or detach cycles return all counters to baseline with no stale-TID/ABA event.
### Implementation-readiness disposition — 2026-08-30

**Action:** TRACKING

Convert title/label consistently to tracking. Children 06a/06b own implementation.
