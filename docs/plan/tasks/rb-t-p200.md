---
schema: "repo-plan/v1"
id: "RB-T-P200"
title: "Prove the AArch64 atomic and memory-ordering foundation for SMP"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P114"
  - "RB-G-GATE1"
  - "RB-T-P014"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-00"
x_linear_id: "ROB-783"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-783/p2-00-prove-the-aarch64-atomic-and-memory-ordering-foundation-for-smp"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P200: Prove the AArch64 atomic and memory-ordering foundation for SMP

## Goal

Establish one explicit, tested AArch64 memory model and synchronization primitive layer before SMP scheduling, futexes, descriptor readiness, or ERTS threads depend on it.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-G-GATE1, RB-T-P014, RB-T-P114.

Blocks: RB-E-P205, RB-T-P207, RB-E-P210, RB-G-GATE2.

## Deliverables

* Freeze whether the kernel/native builds use baseline LL/SC atomics, LSE atomics, or compiler outline-atomics; reconcile this with `HWCAP_ATOMICS` and every target flag.
* Define supported atomic widths/alignment, compare-exchange failure ordering, refcount rules, spinlock/ticket-lock or other minimal lock semantics, once initialization, interrupt-safe lock restrictions, and memory reclamation/lifetime rules.
* Provide reviewed wrappers for acquire, release, acquire-release, sequentially consistent operations, full system barriers, instruction barriers, and device/DMA barriers; forbid unexplained inline assembly outside the architecture module.
* Specify the sleep/wakeup publication invariant used by scheduler wait queues, futexes, poll, and cross-CPU IPIs.
* Add model/litmus tests for message passing, store buffering, load buffering, IRIW/multi-copy visibility where relevant, lock handoff, refcount finalization, wait/wake, and interrupt/CPU interactions.
* Run architecture-appropriate stress on TCG, HVF, and native/KVM profiles where available. A passing x86 host model is supportive only.
* Add static checks/lints for atomic ordering choices and require an invariant comment at every nontrivial relaxed atomic.

## Acceptance criteria

- [ ] CPU, compiler, auxv/HWCAP, and emitted atomic instruction strategy agree exactly.
- [ ] Every kernel synchronization primitive has a documented linearization point, memory-order guarantee, interrupt-context rule, and ownership/lifetime invariant.
- [ ] Sleep/wakeup and cross-CPU notification tests cannot lose an event across all enumerated boundary interleavings.
- [ ] Device/DMA ordering is not implemented by reusing normal-memory barriers without an explicit architecture proof.
- [ ] Litmus/model tests include failing negative implementations that demonstrate the harness detects missing ordering.
- [ ] No unsupported optional instruction is emitted or advertised, and every relaxed operation has a reviewed justification.

## Verification

* `just test-memory-model`
* `just stress-atomics-aarch64`
* `just audit-atomic-instructions`
* `just audit-memory-ordering`

## Evidence

* Host model checks plus guest litmus/stress on every approved semantic runner.
* Disassembly audit of kernel/native synchronization paths.
* Fault/preemption/IPI injection at ordering boundaries.
* Machine-readable primitive inventory linked to callers and invariants.

## Out of scope

* Lock-free optimization for its own sake, NUMA, heterogeneous CPUs, SVE/SME, production RCU, or claiming one emulator exhaustively proves the Arm memory model.

## Additional context
### Why this is a blocker

AArch64 is weakly ordered. Interrupt masking is not a substitute for inter-CPU ordering, release/acquire is not automatically a full barrier, device/DMA ordering differs from normal memory ordering, and LSE availability depends on the frozen CPU/HWCAP/toolchain contract. Races can disappear under one QEMU profile while remaining architecturally legal.
### Completion rule

Done means every later M2 concurrent protocol is built on a pinned, inspected, negative-tested AArch64 synchronization layer rather than incidental emulator behavior.
### Learning checkpoint

Explain the difference between compiler ordering, CPU normal-memory ordering, full-system barriers, I/O/DMA ordering, and interrupt masking, then state the wait/wakeup publication invariant.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Excellent. Do not use it to defer M1 IRQ/locking policy. Keep negative litmus/model evidence and emitted-instruction audit.
