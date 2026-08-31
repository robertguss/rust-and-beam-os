---
schema: "repo-plan/v1"
id: "RB-T-P306"
title: "Bring ERTS to the final two-scheduler SMP profile"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P305"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-06"
x_linear_id: "ROB-732"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-732/p3-06-bring-erts-to-the-final-two-scheduler-smp-profile"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P306: Bring ERTS to the final two-scheduler SMP profile

## Goal

Prove that ERTS scheduler threads and the custom kernel execute real work concurrently on four vCPUs.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P305.

## Deliverables

* Boot with `+S 2:2 +SDcpu 1:1 +SDio 1 +A 1` on four vCPUs and record the actual native thread set.
* Identify scheduler, dirty CPU, dirty I/O, async, auxiliary, poll, and other threads by creation/lifecycle evidence rather than assumptions.
* Run tagged concurrent workloads and correlate BEAM scheduler activity with kernel CPUs, context switches, futex waits, wakeups, and run queues.
* Exercise thread startup/shutdown and process-wide halt repeatedly.

## Acceptance criteria

- [ ] Two normal BEAM schedulers report online and execute tagged work concurrently.
- [ ] All required dirty/async/auxiliary threads start and exit without leaking kernel tasks, stacks, TLS, or waiters.
- [ ] No scheduler remains permanently starved and no kernel CPU is assumed to equal a BEAM scheduler.
- [ ] The single-scheduler profile remains diagnostic only; all final tests use the required SMP profile.

## Verification

* `just test-erts-smp`
* `just trace-erts-thread-topology`

## Evidence

* Run concurrency and lifecycle tests across 100 short boots.
* Inspect per-CPU and per-thread traces.
* Publish the final ERTS native-thread topology.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Additional context
### Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.
### Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.
### Readiness-audit correction — 2026-08-30

* Verify the final VM argument vector against the pinned OTP artifact/reference run. Record the exact meanings and accepted ranges of `+S 2:2`, dirty CPU/IO scheduler arguments, async-thread count, poll options, and any allocator flags; unknown or ignored arguments are failures.
* Enumerate actual native threads from create/exit/TID/TLS evidence and correlate them with ERTS-reported scheduler/dirty/async/poll identities where available. Do not assume a name/count from documentation is what this build created.
* “Two schedulers online” is necessary but insufficient. Use CPU-intensive tagged Erlang work with synchronized start windows and prove overlapping reductions/work on both normal scheduler threads and distinct vCPUs, while measuring run-queue progress and excluding serial alternation or one starved scheduler.
* Exercise normal, dirty CPU, dirty I/O, async, auxiliary, signal/poll, and timer thread paths only to the extent enabled/required by the frozen profile. Any unexpected thread or host call reopens contract analysis.
* Run migration/preemption stress with randomized FP/AdvSIMD canaries, TLS values, signal delivery, futex waits, poll wakeups, timers, and VMA activity so final ERTS load revalidates the M2 cross-CPU invariants rather than merely benefiting from them.
* Define progress floors and starvation bounds appropriate to each approved runner. Performance is profile-specific, but no runner may permit permanent starvation, lost wakeup, scheduler collapse, or unexplained idle time while runnable work exists.
* For repeated startup/halt, account exactly for native tasks, stacks, TLS, TIDs, robust registrations, futex waiters, poll registrations, timers, signals, VMAs/pages/ASIDs, and scheduler-visible resources. Every failure preserves the first trace and build/seed.
* The single-scheduler result remains diagnostic and cannot be used to waive a final-profile defect. Any change of scheduler/dirty/async counts made to avoid a failure is a new narrower profile requiring Gate 3 disposition.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Use barrier-synchronized CPU work and overlapping per-vCPU/OS-thread evidence. Online threads are not concurrency proof.
### Normative readiness correction — 2026-08-30

Use a barrier-synchronized CPU-bound workload that cannot complete on one scheduler within the measured overlap window. Correlate ERTS scheduler identity, OS thread identity, vCPU execution intervals, and reductions/work completion. Scheduler threads merely existing or being online is not concurrency proof.
