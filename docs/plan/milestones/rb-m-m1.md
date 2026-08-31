---
schema: "repo-plan/v1"
id: "RB-M-M1"
title: "Bootable Rust Kernel Spine"
type: "milestone"
order: 1
authorized_by: "RB-G-GATE0"
x_legacy_id: "M1"
---
## Outcome

Create the smallest project-owned AArch64 Rust kernel with a trustworthy debugging loop and one isolated native userspace process.

## Scope

* Direct boot on the Gate-0-frozen versioned QEMU `virt-X.Y` profile, early EL normalization, DTB discovery, UART, and panic records.
* Exceptions, IRQs, physical and virtual memory, page tables, timer preemption, and one CPU.
* Static AArch64 ELF loading and the native typed-handle ABI.
* EL0 isolation, user-pointer validation, per-process address spaces, and fault containment.
* Read-only system archive and initial image builder.
* Headless QEMU, GDB, QMP, serial sentinels, host tests, and reproducible boot evidence.

## Exit criteria

* The kernel boots and exits 1,000 times headlessly without hanging.
* An EL0 hello process runs through the native ABI.
* User faults terminate only the offending process.
* Invalid pointers cannot access kernel memory.
* Randomized allocator and mapping tests pass.
* Timer-driven preemption is observable.
* RB-G-GATE1 records whether the kernel spine is trustworthy enough for the musl contract.

## Implementation-readiness status — 2026-08-30

**Gate-blocked; not authorized.** Consume the Gate-0-frozen versioned platform. RB-T-P100 governs single-CPU IRQ/preemption/locking/exception stacks. VM, timer/wait, and ELF work are tracking parents with bounded children. Gate 1 additionally requires user-copy fault fixups and lifetime locking, executable D/I-cache publication, TLB/ASID reuse, and single-CPU FP/AdvSIMD isolation.
