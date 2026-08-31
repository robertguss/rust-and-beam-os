---
schema: "repo-plan/v1"
id: "RB-T-P209A"
title: "Implement signal dispositions, masks, pending state, and target selection"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P209"
depends_on:
  - "RB-T-P200"
  - "RB-E-P205"
  - "RB-E-P206"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-09a"
x_linear_id: "ROB-791"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-791/p2-09a-implement-signal-dispositions-masks-pending-state-and-target"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P209A: Implement signal dispositions, masks, pending state, and target selection

## Goal

Build the exact process/thread signal state machine required by the pinned musl/ERTS trace before constructing architecture-specific user frames or syscall restart behavior.

## Context

Blocked by: RB-E-P206, RB-E-P205, RB-T-P200.

## Deliverables

* Derive the exact signal numbers, `rt_sigaction` flags, `rt_sigprocmask` operations, kill/thread-target operations, default/ignore/catch dispositions, and query behavior used by the target.
* Model process-wide dispositions separately from per-thread masks, alternate-stack metadata, pending sets/queues, currently delivered signal, and termination state.
* Define standard-signal coalescing, ordering/selection among pending process-directed and thread-directed signals, target eligibility, mask inheritance at clone, mask restoration hooks, and delivery safe points.
* Implement install/query/replace validation with exact structure size/alignment, admitted flags, immutable/unblockable signals, restorer/trampoline policy, and atomic old/new copy behavior.
* Bound pending state and delivery nesting metadata; unsupported real-time queueing or other features fail explicitly unless the trace proves they are needed.
* Integrate enqueue/wakeup with the scheduler without yet building the AArch64 signal frame. Delivery selection emits a typed request consumed by RB-T-P209B.
* Define default termination/ignore behavior for the admitted subset and keep synchronous faults distinguishable from asynchronous delivery.

## Acceptance criteria

- [ ] Install/query, mask block/unblock/set, clone inheritance, ignore/default/catch, pending/coalescing, thread-directed, process-directed, and target-selection probes match the admitted AArch64 Linux behavior.
- [ ] A masked signal remains pending and wakes/delivers only when a legal target becomes eligible.
- [ ] Process and thread signal state cannot be confused during concurrent mask/disposition/exit changes.
- [ ] Invalid signal numbers, flags, sizes, pointers, masks, targets, or exhausted state fail atomically with the exact error and no partial mutation.
- [ ] Pending and nested-delivery metadata have explicit hard bounds and complete accounting.
- [ ] Selection/wakeup races preserve exactly one legal pending-or-delivered outcome without losing or duplicating a standard signal.

## Verification

* `just test-signal-state-model`
* `just test-signal-masks-targets`
* `just stress-signal-selection`

## Evidence

* Linux differential C probes, model-based pending/selection tests, multi-thread mask/target/exit races, invalid-copy rollback, standard-signal coalescing, ignored/default actions, and deliberately broken lost-signal canaries.
* Trace replay proving every enqueue transitions to ignored, pending, selected, delivered, or process termination.

## Out of scope

* User signal frames, alternate-stack switching, `rt_sigreturn`, register restoration, syscall interruption/restart, real-time queued-signal completeness, job control, process groups, or ptrace.

## Additional context
### Completion rule

Done means signal ownership, masking, pending state, selection, and default/ignore actions are bounded and linearizable independently of architecture-frame and wait-interruption code.
### Learning checkpoint

Explain which signal state is process-wide versus per-thread, how standard-signal coalescing works for the admitted subset, and the target-selection rule when several threads are eligible.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong child. Replace tracking-parent dependencies with completed implementation children where practical; keep exact admitted signal subset.
### Normative readiness correction — 2026-08-30

Gate 2 requires exact admitted signal/flag sets, deterministic process/thread target selection, bounded pending-state behavior, and direct dependencies on completed implementation children rather than tracking parents.
