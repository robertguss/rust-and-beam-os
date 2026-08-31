---
schema: "repo-plan/v1"
id: "RB-T-P206B"
title: "Implement thread exit, clear-child-TID wake, join/detach, and reclamation"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P206"
depends_on:
  - "RB-T-P205C"
  - "RB-T-P207"
  - "RB-T-P206A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-06b"
x_linear_id: "ROB-788"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-788/p2-06b-implement-thread-exit-clear-child-tid-wake-joindetach-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P206B: Implement thread exit, clear-child-TID wake, join/detach, and reclamation

## Goal

Complete the lifecycle protocol only after the futex wait/wake primitive exists, so musl join cannot depend on a fictional pre-futex wakeup.

## Context

Blocked by: RB-T-P206A, RB-T-P207, RB-T-P205C.

## Deliverables

* Implement `set_tid_address` and the exact clear-child-TID-on-exit behavior observed from pinned musl.
* Define the thread lifecycle state machine from running through exiting, user-visible TID clear, futex wake, zombie/joinable or detached state, final reference drop, and object/TID reuse.
* Order user memory clear, wake publication, scheduler removal, signal/robust cleanup hooks, descriptor/address-space reference release, stack/TLS mapping release, and kernel-task reclamation.
* Implement join/detach ownership, exactly-one reaper semantics, return-value handoff, self-join/double-join/detach-after-exit behavior as required by musl, and process-wide last-thread exit.
* Integrate generation-safe TIDs so a stale waiter/reaper cannot act on a reused thread.
* Reserve the robust-list cleanup hook; RB-T-P208 supplies the robust mutex operation before full contract qualification.
* Ensure user-copy failure, unmap races, cancellation/signal interruption, and concurrent join/detach do not strand or double-reclaim the thread.

## Acceptance criteria

- [ ] The clear-child-TID store and futex wake cannot be missed by a joining waiter across every order boundary.
- [ ] Exactly one legal owner reaps a joinable thread; detached threads reclaim automatically; double join/detach/reap cannot free twice.
- [ ] Stack, TLS, task, TID, FP state, mappings, and references are reclaimed once and only after no CPU/waiter can use them.
- [ ] Last-thread/process-wide exit terminates all required process resources without racing live sibling state.
- [ ] Unmapped/bad child-TID addresses and fault injection follow the observed contract without kernel failure or leaked tasks.
- [ ] TID reuse is generation-safe and stale waiters cannot consume a new thread's exit.

## Verification

* `just test-pthread-exit-join`
* `just stress-pthread-lifecycle`
* `just test-clear-child-tid-races`
* `just audit-thread-reclamation`

## Evidence

* Deterministic wait-before-clear, clear-before-wait, timeout-at-clear, signal-at-clear, exit-during-migration, unmap-at-exit, join-vs-detach, double-join, self-join, detached-early/late-exit, last-thread-exit, and allocation/copyout failure matrices.
* Long create/exit/join churn with object/TID conservation and exact trace replay.

## Out of scope

* Robust mutex owner-death mutation itself (RB-T-P208), general waitpid/process hierarchy, fork/exec, ptrace, or arbitrary clone modes.

## Additional context
### Completion rule

Done means join/detach/exit is one explicit, generation-safe lifecycle protocol built on the real futex primitive with no missed wake or double reclamation.
### Learning checkpoint

Explain why `clear_child_tid` and futex wake form one ordered protocol, identify the thread's final reclamation point, and show how TID reuse is prevented from creating an ABA bug.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Add explicit relation to RB-T-P208 and prove last-thread process teardown.
