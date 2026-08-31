---
schema: "repo-plan/v1"
id: "RB-T-P210B"
title: "Implement poll/ppoll registration, readiness, timeout, close, and reuse races"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P210"
depends_on:
  - "RB-T-P211A"
  - "RB-T-P210A"
  - "RB-T-P200"
  - "RB-T-P205B"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-10b"
x_linear_id: "ROB-790"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-790/p2-10b-implement-pollppoll-registration-readiness-timeout-close-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P210B: Implement poll/ppoll registration, readiness, timeout, close, and reuse races

## Goal

Provide a linearizable, bounded readiness multiplexer for the exact descriptors and event masks observed from portable ERTS.

## Context

Blocked by: RB-T-P210A, RB-E-P211, RB-T-P205B, RB-T-P200.

## Deliverables

* Derive the exact `poll`/`ppoll` calls, event bits, timeout form, signal-mask argument behavior, and descriptor classes from the pinned target trace.
* Define readiness as a level-triggered predicate for each admitted stream state, including readable buffered bytes, EOF/hangup, writable capacity, no-reader error, invalid descriptor, and unsupported event masks.
* Implement the atomic check/register/recheck/block protocol so a state transition cannot occur between readiness inspection and waiter registration without waking or being observed.
* Use descriptor/object generations in every registration; close/reuse must invalidate the old registration and never report a new descriptor's event.
* Integrate monotonic timeout deadlines, spurious wake/recheck behavior, process/thread exit, cancellation hooks, and later signal interruption without holding descriptor locks while blocking.
* Bound descriptor count per call, total registrations, wait objects, event result size, wake fanout, and per-transition work.
* Define deterministic precedence for ready events, invalid descriptors, close/hangup, timeout, signal/cancellation, and copyout failure according to the admitted Linux contract.
* Emit sequence-stamped traces for check, register, recheck, sleep, transition, wake, revalidate, result, close, and reuse.

## Acceptance criteria

- [ ] No readiness event is lost across the complete check/register/recheck/state-change interleaving matrix.
- [ ] A call returns immediately for already-ready/invalid descriptors and blocks without spinning otherwise.
- [ ] Close, half-close, timeout, descriptor reuse, thread exit, and simultaneous multiple-ready events produce only documented outcomes.
- [ ] Stale registrations cannot observe or wake for a reused descriptor/object generation.
- [ ] Unsupported masks, excessive arrays, invalid user memory, and exhaustion fail before unbounded allocation or partial hidden registration.
- [ ] Four-vCPU stress preserves progress, bounded fanout, no duplicate waiter ownership, and complete cleanup.

## Verification

* `just test-poll-model`
* `just test-poll-guest`
* `just stress-readiness`
* `just audit-poll-registrations`

## Evidence

* Model checker for check/register/recheck; deliberate lost-wakeup implementation canary; Linux differential fixtures for all admitted event combinations; close/reuse/timeout/copyout failure matrices; multi-poller/multi-producer four-vCPU stress.
* Trace replay that accounts for every registration and terminal result.

## Out of scope

* `epoll`, `kqueue`, sockets, edge-triggered behavior, arbitrary device descriptors, general POSIX polling, or signal delivery implementation itself.

## Additional context
### Completion rule

Done means the exact portable-ERTS readiness path is level-correct, race-safe, bounded, generation-safe, and independently replayable.
### Learning checkpoint

State the atomic check/register/recheck invariant, explain level-triggered readiness for EOF and no-reader states, and identify how descriptor generations eliminate stale-registration ABA.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong child. Depend directly on RB-T-P211A for deadlines and RB-T-P209C for signal interruption; preserve check/register/recheck proof.
### Normative readiness correction — 2026-08-30

Use RB-T-P211A directly for deadlines and integrate signal interruption through RB-T-P209C. Preserve check/register/recheck, generation-safe close/reuse, level-triggered readiness, and one-terminal-outcome evidence.
