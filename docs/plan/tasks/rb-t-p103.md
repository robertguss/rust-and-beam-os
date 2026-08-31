---
schema: "repo-plan/v1"
id: "RB-T-P103"
title: "Install AArch64 exception vectors, IRQ dispatch, and structured panic records"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P102"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-03"
x_linear_id: "ROB-702"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-702/p1-03-install-aarch64-exception-vectors-irq-dispatch-and-structured"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P103: Install AArch64 exception vectors, IRQ dispatch, and structured panic records

## Goal

Make every early kernel failure observable before concurrency and userspace make diagnosis harder.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P102.

## Deliverables

* Install aligned EL1 vector tables for synchronous exceptions, IRQ, FIQ, and SError paths from current and lower exception levels.
* Capture ESR, FAR, ELR, SPSR, general registers, CPU, current task identity, and last trace events.
* Create typed exception classification and a minimal IRQ registration/dispatch interface.
* Emit a bounded structured panic/fault record to serial and terminate or isolate according to the fault class.

## Acceptance criteria

- [ ] Intentional undefined instruction, data abort, instruction abort, and spurious IRQ tests produce correctly classified records.
- [ ] Exception entry/exit preserves required registers and stack alignment.
- [ ] A kernel fault stops deterministically; a future user fault path can return to the scheduler without corrupting kernel state.
- [ ] Host-side decoders validate panic-record schema and symbolization inputs.

## Verification

* `just test-exceptions`
* `just run-qemu-fault-matrix`

## Evidence

* Run one controlled test for each vector class.
* Inspect registers against QEMU/GDB state.
* Save panic fixtures and decoder tests.

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

Add guarded exception/IRQ stacks, nesting/reentrancy policy, full ESR/FAR/register classification, and dependency on RB-T-P100 design.
