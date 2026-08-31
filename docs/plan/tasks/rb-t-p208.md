---
schema: "repo-plan/v1"
id: "RB-T-P208"
title: "Implement robust-list and thread-exit synchronization cleanup"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P206B"
  - "RB-T-P207"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-08"
x_linear_id: "ROB-719"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-719/p2-08-implement-robust-list-and-thread-exit-synchronization-cleanup"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P208: Implement robust-list and thread-exit synchronization cleanup

## Goal

Prevent rare permanent deadlocks when a thread exits while owning musl synchronization state.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-E-P206, RB-T-P207.

## Deliverables

* Implement the contracted robust-list registration/query behavior and validate list pointers, bounds, cycles, offsets, and owner TIDs.
* On thread exit, walk only the bounded safe subset required by musl, mark owner-death state, and wake eligible waiters.
* Integrate robust cleanup with clear-child-TID, process exit, fault termination, and resource teardown ordering.
* Create probes for normal unlock, owner death, malformed/cyclic lists, thread fault, concurrent waiter arrival, and process exit.

## Acceptance criteria

- [ ] A waiter observes the correct owner-death outcome and can recover according to musl semantics.
- [ ] Malformed user lists cannot hang or corrupt the kernel.
- [ ] Exit cleanup neither misses required wakeups nor touches unrelated futex words.
- [ ] Cleanup runs exactly once for normal exit, fault exit, and process-wide termination.
- [ ] Stress shows no monotonic waiter/resource leak.

## Verification

* `just test-robust-futex`
* `just stress-thread-exit-cleanup`

## Evidence

* Run robust-mutex and adversarial-list probes under randomized preemption.
* Compare admitted outcomes with the Linux robust-futex ABI.
* Inspect cleanup traces and waiter conservation.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit correction — 2026-08-30

* Derive the exact `set_robust_list`/`get_robust_list` structure, length, signed futex offset, owner/TID bit encoding, `list_op_pending` handling, owner-death mutation, and wake count from pinned AArch64 musl/Linux evidence. Do not infer the ABI from a high-level pthread test alone.
* Registration is per-thread and generation-bound. Invalid size/alignment/user range is rejected atomically; a stale registration cannot survive task/TID/address-space reuse.
* Exit traversal must be bounded by an explicit element/byte/time budget, detect cycles/duplicates/overflow, and use fault-tolerant user copies. A malformed list may truncate cleanup according to the frozen policy but can never loop, panic, touch kernel/unrelated mappings, or block forever.
* Handle `list_op_pending` exactly so death in the middle of a lock/unlock list mutation does not miss the one futex currently being acquired or process it twice.
* Validate that a listed futex belongs to the exiting process/address-space generation and that its owner bits identify the exiting TID before setting the admitted owner-death state and issuing the required futex wake.
* Freeze and test the exit ordering among robust cleanup, cancellation/signal teardown, clear-child-TID store/wake, scheduler removal, address-space unmap, TID reuse, and final task reclamation. No user mapping may be destroyed before every required cleanup access is complete.
* Cleanup is exactly-once across normal return, explicit thread exit, synchronous fault, cancellation, process-wide termination, and racing reapers. Re-entry or duplicate cleanup is detected.

### Required additional evidence

* Reference Linux byte/state fixtures; normal owner death and recovery; death at every list-mutation boundary; `list_op_pending`; cyclic/self/duplicate/overlong/misaligned/unmapped/kernel-address lists; signed-offset overflow; owner mismatch; concurrent waiter arrival; signal/cancel/clear-child-TID ordering; address unmap/remap; TID reuse; process-wide exit; and failure-injection at every user-copy/wake step.
* Trace conservation must show each candidate entry as validated-and-cleaned, rejected, faulted, duplicate, over-budget, or not owned—never silently omitted.
### Implementation-readiness disposition — 2026-08-30

**Action:** RELATION + AMEND

Block on RB-T-P206B. Implement only if admitted; exact owner-death/list-walk/fault semantics and bounded traversal.
