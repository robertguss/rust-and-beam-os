---
schema: "repo-plan/v1"
id: "RB-E-P105"
title: "TRACKING: Complete kernel VM, address-space lifecycle, and single-core mapping safety"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P105A"
  - "RB-T-P105B"
  - "RB-T-P105C"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-05"
x_linear_id: "ROB-701"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-701/p1-05-tracking-complete-kernel-vm-address-space-lifecycle-and-single"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P105: TRACKING: Complete kernel VM, address-space lifecycle, and single-core mapping safety

## Goal

Create correct AArch64 address spaces with explicit permissions and no accidental kernel exposure.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P104.

## Deliverables

* Implement page-table creation, walking, mapping, unmapping, permission changes, TLB maintenance, and address-range validation.
* Define the kernel and user virtual layouts, guard regions, MMIO mappings, stack policy, and W^X invariant.
* Create distinct user translation tables while preserving the required kernel mapping strategy.
* Add checked abstractions around unsafe table writes and document architectural barriers.

## Acceptance criteria

- [ ] Generated map/unmap/protect sequences match the reference software model.
- [ ] User mappings cannot cover kernel, MMIO, page-table, or reserved ranges.
- [ ] Writable-plus-executable user mappings are rejected.
- [ ] Unmapped, read-only, execute-never, and guard-page accesses fault as expected.
- [ ] Mapping teardown returns every owned frame exactly once.

## Verification

* `just test-vm-host`
* `just test-vm-guest`
* `just inspect-page-tables`

## Evidence

* Run host model/property tests and guest fault probes.
* Inspect representative translation tables with GDB.
* Save the virtual-layout ADR and unsafe proof obligations.

## Out of scope

* ERTS, Elixir, musl/pthreads, GPU UI integration, networking, writable storage, and phone hardware.
* General POSIX/Linux compatibility or a production security claim.
* Broad optimization before correctness evidence.

## Additional context
### Completion rule

Do not mark Done until every acceptance item has durable evidence from the exact build. Preserve any failing seed or trace; never convert a flake into success by blind retry.
### Learning checkpoint

Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process, the invariant this slice protects, one race or memory-corruption failure mode, and how the tests expose it.
### Readiness-audit correction — 2026-08-30

* Model address spaces with explicit ownership, ASID generation/reuse policy, page-table lifetime, and one API for map/unmap/protect. Even before SMP, an address-space identifier cannot be reused until stale translations are invalidated.
* All page-table writes and permission transitions must use the architecture publication/TLB API completed in RB-T-P114; no caller may issue ad hoc barriers or TLBI.
* Enforce W^X during construction as well as steady state. ELF loading uses writable+NX staging and only later transitions to RX after executable-cache maintenance.
* Define behavior for zero-size/overflow/unaligned/overlapping ranges, physical aliases, guard pages, stack growth policy, page-table allocation failure, partial-operation rollback, and destruction with outstanding handles.
* Host model/property tests must include randomized map/unmap/protect sequences, ASID reuse, page-table failure injection, alias attempts, and comparison against a simple reference translation model.
* Record the single-core invariant now and the cross-CPU shootdown/acknowledgement obligation that blocks completed SMP VM operation in M2.
### Implementation-readiness disposition — 2026-08-30

**Action:** SPLIT/TRACK

Use three children. Keep appended ASID/W^X corrections; remove ad hoc TLBI and fix learning-checkpoint terminology.
