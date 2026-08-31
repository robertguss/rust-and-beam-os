---
schema: "repo-plan/v1"
id: "RB-T-P209C"
title: "Integrate signal interruption, restart, cancellation, and wait-race semantics"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P209"
depends_on:
  - "RB-T-P211A"
  - "RB-T-P207"
  - "RB-T-P209B"
  - "RB-T-P210A"
  - "RB-T-P210B"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-09c"
x_linear_id: "ROB-793"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-793/p2-09c-integrate-signal-interruption-restart-cancellation-and-wait"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P209C: Integrate signal interruption, restart, cancellation, and wait-race semantics

## Goal

Make blocked syscalls, signal delivery, timeouts, partial I/O, futex wakeups, poll readiness, and musl cancellation interact exactly as required by the pinned contract.

## Context

Blocked by: RB-T-P209B, RB-T-P207, RB-T-P210B, RB-E-P211, RB-T-P210A.

## Deliverables

* Classify every admitted blocking call as never restartable, restartable under the admitted `SA_RESTART` conditions, internally restartable with an adjusted monotonic deadline, or returning a completed partial result.
* Derive the exact Linux outcomes for the pinned `read`/`readv`, `write`/`writev`, futex wait variants, `poll`/`ppoll`, sleep calls, and any musl cancellation-point wrappers observed in the trace.
* Define one wait-completion state machine with terminal reasons such as condition/readiness, timeout, signal selected, cancellation, close/unmap/exit, partial transfer, fault, and explicit retry/restart.
* Ensure only one terminal outcome wins. Preserve enough state to restart only when the contract requires it, with remaining time computed from an absolute monotonic deadline rather than resetting the full timeout.
* Implement the precise ordering among signal selection, signal-frame construction, syscall return/restart metadata, mask replacement for `ppoll` if admitted, and `rt_sigreturn` continuation.
* Integrate musl cancellation without inventing broad POSIX semantics: identify the exact cancellation signal/path and protect kernel object lifetimes while a blocked operation is unwound.
* For partial I/O, return transferred bytes when required rather than converting completed work into `EINTR`; for `poll`/`ppoll`, honor the frozen Linux rule rather than generalizing `SA_RESTART`.
* Emit sequence-stamped wait/signal/restart traces and carry generation identities for descriptor, futex mapping, task, timer, and signal delivery.

## Acceptance criteria

- [ ] Every admitted blocked call has a table-driven restart/EINTR/partial-result/deadline rule linked to reference evidence.
- [ ] Signal-vs-ready/wake/timeout/close/unmap/cancel races produce exactly one documented terminal result with no lost event, duplicate completion, or stranded waiter.
- [ ] Restarted timed waits never gain time; elapsed time is deducted from the original absolute deadline.
- [ ] `poll`/`ppoll` and other never-restarted calls return the required interruption result even when the action carries `SA_RESTART`.
- [ ] Partial reads/writes preserve transferred bytes according to the admitted Linux behavior.
- [ ] Cancellation/exit cannot reclaim a wait object, descriptor, futex key, timer, or task while another CPU can still complete it.
- [ ] Repeated handler return resumes either the restarted syscall or the original user continuation exactly once.

## Verification

* `just test-signal-wait-matrix`
* `just test-syscall-restart-contract`
* `just test-cancellation-races`
* `just stress-interrupted-waits`

## Evidence

* Differential AArch64 Linux matrix for every admitted blocking interface with and without `SA_RESTART`, before/after partial transfer, and at timeout boundaries.
* Deterministic signal-vs-futex, signal-vs-poll, signal-vs-sleep, signal-vs-I/O, cancel-vs-wake, close-vs-signal, unmap-vs-signal, and exit-vs-restart interleavings.
* Deliberately broken double-completion, reset-timeout, and restart-never-restartable canaries.
* Long four-vCPU mixed-wait campaign with complete terminal-reason conservation.

## Out of scope

* General Linux restart-block compatibility, ptrace interactions, stop/continue job control, every POSIX cancellation point, sockets, or arbitrary future syscalls.

## Additional context
### Completion rule

Done means every admitted wait has one linearizable terminal outcome and signal handling cannot reset deadlines, lose completed work, restart a never-restartable call, or reclaim live state.
### Learning checkpoint

Explain why `SA_RESTART` is interface-specific, why poll differs from many slow I/O calls, how absolute deadlines prevent timeout extension, and where the one-terminal-outcome linearization point lives.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong child. Depend directly on RB-T-P211A rather than tracking parent; retain one-terminal-outcome conservation and absolute deadlines.
### Normative readiness correction — 2026-08-30

Gate 2 requires interruption, restart, cancellation, deadline, partial-I/O, futex, and poll races to conserve exactly one terminal outcome. All retries retain the original absolute monotonic deadline from RB-T-P211A.
