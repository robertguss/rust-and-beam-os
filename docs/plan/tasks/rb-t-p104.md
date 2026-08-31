---
schema: "repo-plan/v1"
id: "RB-T-P104"
title: "Build the physical page allocator and bounded kernel heap"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P103"
  - "RB-T-P102"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-04"
x_linear_id: "ROB-697"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-697/p1-04-build-the-physical-page-allocator-and-bounded-kernel-heap"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P104: Build the physical page allocator and bounded kernel heap

## Goal

Provide explicit, testable physical-memory ownership before user mappings and processes exist.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P102, RB-T-P103.

## Deliverables

* Construct the usable physical-memory map from DTB ranges while reserving kernel, DTB, image, MMIO, and bootstrap regions.
* Implement a simple page-frame allocator with checked range arithmetic, double-free detection in debug builds, and allocation counters.
* Add a bounded kernel heap backed by explicit page allocations; document all allocation contexts that may run with interrupts disabled.
* Expose diagnostics for total, reserved, free, allocated, and high-water pages.

## Acceptance criteria

- [ ] No reserved or MMIO page can be allocated.
- [ ] Randomized allocate/free sequences preserve conservation and detect invalid frees.
- [ ] Heap exhaustion returns a controlled error or documented panic rather than corrupting metadata.
- [ ] Allocator counters reconcile after every test and appear in the serial evidence stream.

## Verification

* `just test-memory-host`
* `just test-memory-guest`

## Evidence

* Run host property tests over generated memory maps.
* Run guest allocation/exhaustion/reuse stress.
* Inspect guard values and page accounting after intentional failures.

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

Define no-allocation/limited emergency allocation contexts, metadata self-hosting, double-free/use-after-free canaries, and deterministic OOM behavior.
