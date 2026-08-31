---
schema: "repo-plan/v1"
id: "RB-E-P205"
title: "TRACKING: Complete SMP CPU, scheduler, and TLB safety"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P205A"
  - "RB-T-P205C"
  - "RB-T-P205B"
  - "RB-T-P200"
  - "RB-T-P114"
  - "RB-G-GATE1"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-05"
x_linear_id: "ROB-715"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-715/p2-05-tracking-complete-smp-cpu-scheduler-and-tlb-safety"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P205: TRACKING: Complete SMP CPU, scheduler, and TLB safety

## Goal

Provide four-vCPU execution and correct cross-CPU wakeups before musl pthread semantics depend on them.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-G-GATE1.

## Deliverables

* Discover CPUs from the DTB and start secondaries through the QEMU `virt` PSCI path.
* Create per-CPU state, stacks, current-task pointers, timer initialization, idle tasks, and trace buffers.
* Make run queues, blocking/wakeup paths, address-space switches, TLB invalidation, and resource accounting safe across four vCPUs.
* Implement the minimal affinity/CPU-count behavior admitted by the ERTS contract; avoid NUMA and production scheduler policy.

## Acceptance criteria

- [ ] All four vCPUs enter the scheduler and execute tagged work.
- [ ] Cross-CPU wakeups cannot be lost when racing with sleep, timeout, exit, or migration.
- [ ] Concurrent mapping/protection changes perform the required TLB maintenance.
- [ ] Seeded scheduler stress runs without deadlock, duplicate runnable tasks, or task loss.
- [ ] Single-vCPU diagnostic mode remains available.

## Verification

* `just test-smp`
* `just stress-scheduler-smp`

## Evidence

* Run cross-CPU scheduling, wakeup, mapping, and shutdown matrices.
* Inspect per-CPU traces and task conservation.
* Replay failing seeds exactly.

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

This issue is now a **tracking/gate issue**, not an agent-sized implementation ticket. Its original scope concealed three independently dangerous mechanisms:

* RB-T-P205A — secondary CPU, per-CPU, timer, PSCI, and GIC bring-up;
* RB-T-P205B — shared scheduling, blocking/wakeup, lock-order, task migration, and FP-state migration;
* RB-T-P205C — concurrent VM, ASID lifetime, acknowledged cross-CPU TLB shootdowns, and safe reclamation.

Do not implement new code directly under this parent. It is Done only when all three child issues pass, their evidence is cross-checked as one system, single-vCPU regression remains green, and no workaround bypasses RB-T-P200's memory-ordering primitives.

Additional parent acceptance:

- [ ] CPU topology and per-CPU initialization are deterministic for 100 repeated boots.
- [ ] Scheduler task conservation and wakeup invariants hold under four-vCPU seeded stress.
- [ ] FP/AdvSIMD state remains isolated during migration.
- [ ] Page/ASID reuse occurs only after acknowledged remote invalidation.
- [ ] The combined system has no deadlock cycle across scheduler, VM, IPI, timer, and trace locks.
### Implementation-readiness disposition — 2026-08-30

**Action:** TRACKING

Correct conversion. Remove ready-for-agent; parent closes only when 05a–c pass.
