---
schema: "repo-plan/v1"
id: "RB-T-P205A"
title: "Bring up secondary CPUs, per-CPU state, timers, and GIC routing"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P205"
depends_on:
  - "RB-G-GATE1"
  - "RB-T-P200"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-05a"
x_linear_id: "ROB-784"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-784/p2-05a-bring-up-secondary-cpus-per-cpu-state-timers-and-gic-routing"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P205A: Bring up secondary CPUs, per-CPU state, timers, and GIC routing

## Goal

Start the frozen four-vCPU platform deterministically and establish isolated per-CPU execution infrastructure before sharing scheduler state.

## Context

Blocked by: RB-G-GATE1, RB-T-P200.

## Deliverables

* Discover enabled CPUs and interrupt-controller topology from the frozen DTB; reject platform drift.
* Start secondaries through the selected PSCI conduit/function and define boot-state, timeout, duplicate-start, and failed-start behavior.
* Allocate guarded per-CPU boot/kernel/interrupt stacks, current-task pointer, logical/physical CPU ID mapping, local timer state, idle task, trace buffer, and interrupt nesting state.
* Initialize the frozen GIC version, redistributors/interfaces, priorities, routing, SGIs/IPIs, and per-CPU generic timer without hard-coded redistributor addresses.
* Publish per-CPU readiness with RB-T-P200 synchronization primitives and release secondaries into a diagnostic work loop—not the shared production scheduler yet.
* Support deterministic single-vCPU mode with the same kernel image and explicit disabled-CPU state.

## Acceptance criteria

- [ ] Exactly the DTB-declared CPUs enter once, report unique IDs/stacks/state, receive local timer interrupts, process targeted SGIs, and enter/leave idle.
- [ ] Missing, late, duplicate, wrong-ID, or partially initialized CPU starts fail loudly with bounded timeout and evidence.
- [ ] Interrupts cannot run before that CPU's stack, exception vector, GIC interface, trace buffer, and current-task state are valid.
- [ ] Per-CPU memory does not overlap and is reclaimed or permanently accounted according to the boot policy.
- [ ] TCG and HVF runs match the declared semantic topology; runner-specific differences are documented.
- [ ] Single-vCPU mode exercises no uninitialized SMP path.

## Verification

* `just test-smp-bringup`
* `just test-gic-routing`
* `just qualify-secondary-cpu-boot`

## Evidence

* 100 repeated four-vCPU boots, targeted/broadcast SGI matrix, timer skew/progress tests, failed-CPU injection, duplicate PSCI request, and single-vCPU regression.
* DTB/GIC/CPU inventory and per-CPU lifecycle traces.

## Out of scope

* Shared run queues, task migration, TLB shootdowns, futexes, ERTS, CPU hotplug, heterogeneous CPUs, or NUMA.

## Additional context
### Completion rule

Done means CPU and interrupt-controller bring-up is deterministic, bounded, repeatable, and independent of the later shared scheduler.
### Learning checkpoint

Explain the PSCI boot handshake, GIC per-CPU initialization order, readiness publication barrier, and why an interrupt before stack/vector initialization is catastrophic.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong, self-contained child. Ensure platform drift and failed CPU start remain explicit failures.
