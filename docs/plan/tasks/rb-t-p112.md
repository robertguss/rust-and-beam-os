---
schema: "repo-plan/v1"
id: "RB-T-P112"
title: "Qualify the kernel spine with 1,000 boots and randomized memory/scheduler tests"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P100"
  - "RB-T-P114"
  - "RB-T-P113"
  - "RB-T-P111"
  - "RB-T-P103"
  - "RB-E-P108"
  - "RB-T-P110"
  - "RB-T-P109"
  - "RB-T-P107"
  - "RB-T-P102"
  - "RB-T-P104"
  - "RB-E-P106"
  - "RB-E-P105"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-12"
x_linear_id: "ROB-709"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-709/p1-12-qualify-the-kernel-spine-with-1000-boots-and-randomized"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P112: Qualify the kernel spine with 1,000 boots and randomized memory/scheduler tests

## Goal

Demonstrate that the kernel foundation is repeatable enough to host a C runtime rather than merely producing one successful boot.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P102, RB-T-P103, RB-T-P104, RB-E-P105, RB-E-P106, RB-T-P107, RB-E-P108, RB-T-P109, RB-T-P110, RB-T-P111.

## Deliverables

* Create a seeded headless qualification harness covering boot/exit, native process success, user faults, invalid pointers, mappings, guard pages, allocation, preemption, sleep/wakeup, handle failures, and cleanup.
* Run 1,000 complete boot/exit iterations across declared remote-Linux runner profiles.
* Aggregate failures, longest boot, resource high-water marks, trace overflows, and reproducibility metadata.
* Make the harness stop on unclassified faults and preserve the failing seed and complete evidence bundle.

## Acceptance criteria

- [ ] All 1,000 boots terminate with the expected sentinel and no unexplained timeout.
- [ ] All randomized suites preserve their model invariants and leak no pages/handles/tasks.
- [ ] Intentional user failures never become kernel failures.
- [ ] Results are reproducible from stored seeds and the exact build receipt.
- [ ] Any flake remains a blocker rather than being retried away.

## Verification

* `just qualify-kernel-spine`
* `just replay-seed SEED=<recorded>`

## Evidence

* Run the complete qualification from a clean image.
* Replay at least one intentional failing seed to prove evidence capture.
* Publish the Phase 1 qualification report.

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

The campaign is valid only after RB-T-P113 and RB-T-P114. Each boot must also assert:

* The exact versioned machine/CPU/GIC/platform baseline matches RB-T-P014.
* EL0 FP/AdvSIMD isolation canaries pass, kernel FP/SIMD policy is unchanged, and advertised HWCAPs match enabled state.
* Every executable image was published through the cache-coherency path; no W+X mapping or stale-code/TLB canary fires.
* ASID/address-space reuse, task-structure reuse, page/handle generation reuse, and malformed-image cleanup return to baseline.
* Failure classification distinguishes guest invariant failure, QEMU/runner invalidity, harness failure, and host interruption. Automatic retries cannot convert a first failure into a pass.
* Runner preflight and campaign capacity come from RB-T-P016; performance numbers from TCG are informative unless explicitly qualified.

In addition to 1,000 clean boots, run a separate deterministic high-switch phase that covers the new FP/SIMD and translation-reuse invariants. Boot count alone is not a concurrency proof.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

The appended correction is strong. Add RB-T-P100 and fixed RB-T-P108B relations; correct EL terminology.
