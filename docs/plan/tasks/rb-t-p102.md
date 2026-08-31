---
schema: "repo-plan/v1"
id: "RB-T-P102"
title: "Implement EL normalization, UART, and QEMU device-tree discovery"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P101"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-02"
x_linear_id: "ROB-699"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-699/p1-02-implement-el-normalization-uart-and-qemu-device-tree-discovery"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P102: Implement EL normalization, UART, and QEMU device-tree discovery

## Goal

Establish trustworthy early boot output and discover the QEMU platform rather than spreading fixed addresses through the kernel.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P101.

## Deliverables

* Normalize the QEMU entry exception level and establish the initial stack before entering Rust.
* Implement early PL011 UART output with a minimal panic-safe writer.
* Parse the QEMU-provided DTB for RAM, CPUs, interrupt controller, timer, UART, virtio, and power-control nodes.
* Create a platform descriptor consumed by later drivers; confine unavoidable bootstrap constants to one documented module.

## Acceptance criteria

- [ ] Serial milestones identify entry EL, DTB address, RAM ranges, CPU count, and discovered devices.
- [ ] Invalid or missing DTB properties fail with a precise panic record.
- [ ] Core kernel modules receive discovered resources through typed platform data rather than QEMU constants.
- [ ] The same parser passes host tests using recorded DTB fixtures.

## Verification

* `just test-dtb`
* `just run-headless --boot-milestones`

## Evidence

* Boot with at least two QEMU memory/CPU configurations.
* Run DTB positive, missing-node, malformed-range, and overflow tests.
* Save serial logs and the exact DTB fixture.

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

Replace reset-to-EL0 wording; define EL2→EL1/EL1 entry, SCTLR/HCR state, DTB validation, UART bounds, and malformed-DTB failure.
