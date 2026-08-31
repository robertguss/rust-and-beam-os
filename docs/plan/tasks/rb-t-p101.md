---
schema: "repo-plan/v1"
id: "RB-T-P101"
title: "Scaffold the no_std kernel, linker layout, and direct QEMU runner"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-AUDIT0"
  - "RB-G-GATE0"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-01"
x_linear_id: "ROB-698"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-698/p1-01-scaffold-the-no-std-kernel-linker-layout-and-direct-qemu-runner"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P101: Scaffold the no_std kernel, linker layout, and direct QEMU runner

## Goal

Create the smallest auditable AArch64 kernel artifact and direct-boot loop without importing an existing OS framework.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-G-GATE0.

## Deliverables

* Create the `kernel` crate for `aarch64-unknown-none`, an explicit linker script, boot assembly, panic-safe build profile, and artifact conversion step.
* Add QEMU `virt` headless and debug runner profiles using the selected Phase 0 machine/device decisions.
* Keep architecture, platform, kernel core, ABI, and driver modules separated according to the repository plan.
* Add compile-time checks that forbid accidental `std`, host-only dependencies, and unsupported architectures in the guest artifact.

## Acceptance criteria

- [ ] QEMU directly loads the project kernel; no UEFI, Linux kernel, or guest bootloader is involved.
- [ ] The kernel reaches a deterministic Rust entry point and can terminate QEMU with a machine-readable result.
- [ ] The binary layout, entry address, sections, and target flags are documented and inspectable.
- [ ] A clean remote Linux builder reproduces the artifact and launch command.

## Verification

* `just build-kernel`
* `just inspect-kernel`
* `just run-headless`

## Evidence

* Inspect ELF/map output and direct-boot command.
* Run headless smoke tests in a clean builder.
* Save the first boot receipt and linker-layout ADR.

## Out of scope

* ERTS, Elixir, musl/pthreads, GPU UI integration, networking, writable storage, and phone hardware.
* General POSIX/Linux compatibility or a production security claim.
* Broad optimization before correctness evidence.

## Additional context
### Completion rule

Do not mark Done until every acceptance item has durable evidence from the exact build. Preserve any failing seed or trace; never convert a flake into success by blind retry.
### Learning checkpoint

Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process, the invariant this slice protects, one race or memory-corruption failure mode, and how the tests expose it.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Fix EL terminology; consume the versioned platform manifest and fail on runner drift. No implementation before Gate 0.
