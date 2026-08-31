---
schema: "repo-plan/v1"
id: "RB-T-P211A"
title: "Implement counter-based clocks, absolute deadlines, sleeps, and timer cancellation"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P211"
depends_on:
  - "RB-T-P205B"
  - "RB-T-P200"
  - "RB-T-P201"
  - "RB-T-P205A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-11a"
x_linear_id: "ROB-794"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-794/p2-11a-implement-counter-based-clocks-absolute-deadlines-sleeps-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P211A: Implement counter-based clocks, absolute deadlines, sleeps, and timer cancellation

## Goal

Provide one overflow-safe monotonic-deadline model shared by sleep, futex, poll, signal restart, and qualification timestamps.

## Context

Blocked by: RB-T-P201, RB-T-P205A, RB-T-P205B, RB-T-P200.

## Deliverables

* Derive generic-counter frequency, accessibility, width, and per-CPU synchronization assumptions from the frozen platform/DTB contract; reject drift or unsupported counter behavior.
* Represent internal deadlines as absolute monotonic instants with checked/saturating conversion rules. Define resolution, rounding, maximum duration, deadline-in-past, infinite wait, and wrap handling.
* Implement the exact admitted clock queries and sleep operations, distinguishing monotonic from any limited realtime clock source; do not synthesize wall-clock truth from elapsed time without an explicit boot epoch.
* Build bounded per-CPU or global timer queues with generation-safe cancellation, wakeup, task exit, CPU migration, and timer-object reuse.
* Define the timer-state machine and one terminal outcome when expiry races condition wake, signal/cancellation, explicit cancellation, thread exit, or CPU migration.
* Calibrate and measure scheduler/timer latency separately for TCG, KVM, and HVF; correctness tolerances may be runner-specific but monotonicity/ordering may not be weakened.
* Expose deterministic virtual-time/fault-injection mode for model tests without allowing production qualification to silently use it.

## Acceptance criteria

- [ ] Monotonic time never moves backward for one thread or across migration among the frozen CPUs.
- [ ] Conversions cannot overflow, wrap early, extend a timeout, or turn an expired deadline into a future wait.
- [ ] Every timer is pending, firing, completed, canceled, or reclaimed exactly once; stale callbacks cannot target reused tasks/timers.
- [ ] Futex, poll, sleep, and later signal restart all consume the same absolute-deadline API.
- [ ] Expiry-vs-wake/cancel/signal/exit/migration races produce one documented result with no stranded task or timer.
- [ ] Realtime queries are either backed by an explicit reproducible epoch/source or fail/return the frozen limited semantics; they never masquerade as trustworthy civil time.

## Verification

* `just test-time-model`
* `just test-timer-races`
* `just stress-timers-smp`
* `just qualify-clock-profiles`

## Evidence

* Counter conversion/wrap model tests; cross-CPU monotonicity; past/zero/max deadlines; high-volume timer insertion/cancel/reuse; forced expiry races; migration; deterministic virtual-time negative canaries; runner-specific latency distributions.

## Out of scope

* NTP, timezone/localtime databases, leap-second policy, battery-backed RTC, suspend/resume, production real-time guarantees, or high-resolution timer optimization beyond the POC.

## Additional context
### Completion rule

Done means all admitted timed waits share one absolute, monotonic, generation-safe mechanism with no timeout extension or double completion.
### Learning checkpoint

Explain counter-to-time conversion, absolute versus relative deadlines, timer cancellation ABA, and why restartable waits must retain the original deadline.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Strong child. If realtime is admitted, freeze PL031 or immutable boot epoch explicitly; timed wait users depend directly on this child.
### Normative readiness correction — 2026-08-30

If the frozen musl/ERTS contract admits `CLOCK_REALTIME`, select and test either the QEMU `virt` PL031 RTC or an explicitly provisioned immutable boot epoch. Civil time may not be derived silently from monotonic elapsed time.
