---
schema: "repo-plan/v1"
id: "RB-T-P114"
title: "Implement executable-page cache maintenance and page-table/TLB coherency"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P105B"
  - "RB-T-P105A"
  - "RB-T-P014"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-14"
x_linear_id: "ROB-782"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-782/p1-14-implement-executable-page-cache-maintenance-and-page-tabletlb"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P114: Implement executable-page cache maintenance and page-table/TLB coherency

## Goal

Make loaded code and changed translations architecturally visible before EL0 executes them, with one reviewed API that later extends safely to SMP.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-E-P105, RB-E-P108, RB-T-P014.

Blocks: RB-T-P112, RB-G-GATE1, RB-E-P204, RB-E-P205.

## Deliverables

* Define a single architecture abstraction for page-table publication, permission transition, unmap, ASID change, TLB invalidation, and executable-code synchronization.
* Implement the Arm-recommended data-cache clean to Point of Unification, instruction-cache invalidate, DSB, and ISB sequence for newly loaded or modified executable ranges according to discovered cache-line geometry.
* Prohibit writable-plus-executable mappings. Load into writable/non-executable pages, complete cache maintenance, then publish read/execute permissions.
* Implement single-core TLB invalidation and barrier rules for map, unmap, remap, and permission changes; design the API so SMP shootdowns can be added without bypassing callers.
* Handle aliases carefully: a physical page cannot retain writable and executable aliases unless an explicit later JIT design proves the required discipline.
* Validate ranges, align safely, use checked arithmetic, and prevent user-controlled addresses from causing maintenance outside the owned mapping.
* Emit structured evidence for every executable publication and translation invalidation in debug/qualification builds.

## Acceptance criteria

- [ ] Dynamically copied test code executes correctly only after the required publish sequence; a deliberately skipped clean/invalidate/barrier canary is detected under at least one controlled model or simulator test.
- [ ] ELF text is never simultaneously writable and executable, including temporary aliases.
- [ ] Permission downgrade, unmap/remap, and address-space reuse cannot execute or access a stale translation.
- [ ] Every page-table mutation path calls the common coherency API and is covered by a static/code review check.
- [ ] Cache-line sizes and maintenance scope derive from the frozen platform contract rather than an unexplained constant.
- [ ] The design states the future SMP shootdown acknowledgement invariant and blocks SMP mappings until it is implemented.

## Verification

* `just test-exec-cache-coherency`
* `just test-tlb-coherency-single-core`
* `just audit-page-table-publication`

## Evidence

* Executable-load/reload tests, stale-code canary, W^X negative tests, unmap/remap/access-fault tests, ASID/address-space reuse tests, and randomized permission transitions.
* Page-table model tests that compare expected translations/permissions with hardware-observed behavior.
* Disassembly and trace evidence showing the exact Arm cache/TLBI/barrier sequence.
* Review against Arm architecture requirements and Linux cache/TLB interface semantics as implementation oracles, without copying Linux architecture.

## Out of scope

* JIT, dual mappings, self-modifying application code, SVE/SME, or complete SMP shootdowns; the latter is a separate M2 proof.

## Additional context
### Why this is a blocker

On AArch64, writing ELF code bytes and marking pages executable is not sufficient by itself. The data and instruction caches may require explicit clean/invalidate operations and barriers. Page-table changes can also leave stale TLB translations. A loader can appear reliable under one emulator while failing or executing stale code elsewhere.
### Completion rule

Done means every executable-page and translation change is routed through a tested architecture-correct publication/invalidation path with no W+X window.
### Learning checkpoint

Explain why D-cache, I-cache, TLB, DSB, and ISB are separate concerns, and state the ordering required before a different execution context may run newly loaded code.
### Implementation-readiness disposition — 2026-08-30

**Action:** RELATION

Remove dependency on RB-E-P108. Block RB-T-P108B instead. Negative canary may use architecture model/instrumentation if an emulator does not manifest stale code.
