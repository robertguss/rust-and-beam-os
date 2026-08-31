---
schema: "repo-plan/v1"
id: "RB-T-P207"
title: "Implement futex wait, wake, timeout, and required bitset semantics"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P205B"
  - "RB-T-P211A"
  - "RB-T-P206A"
  - "RB-T-P200"
  - "RB-E-P204"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-07"
x_linear_id: "ROB-718"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-718/p2-07-implement-futex-wait-wake-timeout-and-required-bitset-semantics"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P207: Implement futex wait, wake, timeout, and required bitset semantics

## Goal

Provide a linearizable futex substrate for musl synchronization and ERTS native threads.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-E-P204, RB-E-P205, RB-E-P206, RB-E-P211.

## Deliverables

* Implement the exact private/shared, wait, wake, bitset, and timed operations admitted by the contract; reject unobserved operations.
* Define atomic value check, waiter enqueue, wake selection, timeout clock, interruption, spurious wake, unmap/exit, and address-reuse behavior.
* Shard or bound wait queues without permitting unbounded kernel allocation from user-controlled addresses.
* Instrument wait duration, wake reason, queue depth, timeouts, and unmatched wakes.

## Acceptance criteria

- [ ] Mutex, condition-variable, once, semaphore/barrier-if-required, timeout, spurious-wakeup, and contention probes pass.
- [ ] The value-check-to-sleep transition cannot lose a wake.
- [ ] Timeout/wake/unmap/exit races have documented legal outcomes and no stranded waiters.
- [ ] Invalid alignment, inaccessible addresses, unsupported flags, and exhausted queues return specified errors.
- [ ] Four-vCPU stress preserves mutual exclusion and progress.

## Verification

* `just test-futex`
* `just stress-futex`
* `just futex-model-check`

## Evidence

* Run model-based interleaving tests and guest contention stress.
* Replay Linux-reference behavioral cases for the admitted subset.
* Save wait-queue traces for every terminal reason.

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

* This issue depends on RB-T-P206A (thread creation), **not** the completed RB-E-P206 lifecycle parent. RB-T-P206B deliberately depends on this futex primitive for clear-child-TID/join.
* Define the futex key as the exact process/address-space/address/alignment/generation identity required by the admitted private-musl calls. A stale waiter cannot attach to a newly mapped object at the same virtual address.
* The value comparison and enqueue/block transition must be atomic with respect to matching wake and value-changing synchronization. Specify the linearization point, lock order, user-memory fault handling, and ordering guaranteed before/after sleep and wake.
* Enumerate exact admitted operations/flags, absolute-versus-relative timeout clock, bitset matching, wake-count behavior, spurious wake permission, `EAGAIN`, `EINTR`, `ETIMEDOUT`, alignment, zero/negative counts, overflow, unmap/remap, process exit, and concurrent waiter teardown.
* No boot-time spin/yield valve or readiness-marker change to normal semantics is acceptable as an implementation result. It may exist only as a diagnostic experiment tied to an explicit failed hypothesis and must never satisfy conformance.
* Test wait-vs-wake at every boundary, wake-before-wait, value-change-before-enqueue, timeout-vs-wake, signal-vs-wake, unmap/remap/ASID-reuse, duplicate wake, waiter exit, and high-contention hash-bucket collision.
* Use RB-T-P200 ordering primitives and include a model checker/reference state machine with deliberately broken lost-wakeup variants.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Derive exact ops/clocks/flags from pinned musl/ERTS; define atomic compare-and-block, unmap/exit races, interruption, timeout, and waiter lifetime.
