---
schema: "repo-plan/v1"
id: "RB-G-GATE1"
title: "Decide whether the kernel spine is trustworthy enough for the musl contract"
type: "gate"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P100"
  - "RB-T-P114"
  - "RB-T-P113"
  - "RB-T-P112"
  - "RB-T-P111"
  - "RB-T-P110"
  - "RB-T-P109"
  - "RB-E-P108"
  - "RB-T-P107"
  - "RB-E-P105"
  - "RB-E-P106"
  - "RB-T-P101"
  - "RB-T-P102"
  - "RB-T-P104"
  - "RB-T-P103"
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
x_legacy_id: "GATE-1"
x_linear_id: "ROB-708"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-708/gate-1-decide-whether-the-kernel-spine-is-trustworthy-enough-for-the"
x_labels:
  - "ready-for-human"
---
# RB-G-GATE1: Decide whether the kernel spine is trustworthy enough for the musl contract

## Decision

[Architecture & Validation Plan](<../architecture.md>)

Approve, narrow, repair, or stop the kernel foundation before implementing deep libc/thread semantics.

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P101, RB-T-P102, RB-T-P103, RB-T-P104, RB-E-P105, RB-E-P106, RB-T-P107, RB-E-P108, RB-T-P109, RB-T-P110, RB-T-P111, RB-T-P112.

## Required evidence

* Run a fresh-session audit using only repository plan content and evidence artifacts.
* Publish the gate ADR/status update and name the next issue.
* Confirm downstream dependency links.

## Acceptance criteria

- [ ] Continue is forbidden while any unclassified kernel fault, user/kernel isolation failure, memory-accounting discrepancy, or non-reproducible flake remains.
- [ ] The decision links each milestone exit criterion to evidence.
- [ ] Any accepted residual risk has an owner, detection mechanism, and downstream constraint.
- [ ] All M2 issues remain blocked until this gate is Done and the user approves the decision.

## Decision record

Do not mark Done until every acceptance item has durable evidence from the exact build. Preserve any failing seed or trace; never convert a flake into success by blind retry.

## Out of scope

* ERTS, Elixir, musl/pthreads, GPU UI integration, networking, writable storage, and phone hardware.
* General POSIX/Linux compatibility or a production security claim.
* Broad optimization before correctness evidence.

## Additional context
### What to build

* Review the M1 milestone criteria, 1,000-boot report, fault-containment evidence, memory/scheduler model tests, image reproducibility, observability, and unsafe-code inventory.
* Confirm that core/kernel/platform boundaries match the architecture and no existing OS framework supplies the scheduler, VM, ABI, or VFS.
* List every known flake, unclassified fault, unchecked unsafe block, and deferred invariant.
* Record Continue, Repair within M1, Narrow the runtime target, Pivot, or Stop.
### Verification commands

* `just gate-report 1`
* `just evidence-check --phase 1`
### Learning checkpoint

Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process, the invariant this slice protects, one race or memory-corruption failure mode, and how the tests expose it.
### Readiness-audit correction — 2026-08-30

RB-G-GATE1 may authorize M2 only when all original criteria plus these hold:

- [ ] The guest platform identity matches the frozen versioned QEMU/CPU/GIC/HWCAP contract; no unapproved runner or feature drift is present.
- [ ] FP/AdvSIMD state is isolated across EL0 tasks, preemption, faults, task reuse, and available migration tests; unsupported extended state is disabled/unadvertised.
- [ ] Every executable load performs the reviewed D-cache/I-cache/barrier sequence and every translation change performs reviewed TLB maintenance through one API.
- [ ] W^X holds during load and permission transition, not just after it; no stale executable or stale translation canary remains.
- [ ] ELF/stack/auxv validation matches the exact native artifact shapes and fails closed on every unsupported header, relocation, TLS, or dynamic-loading form.
- [ ] Address-space/ASID/task/handle reuse has generation/lifetime evidence and zero cross-process data disclosure.
- [ ] The 1,000-boot and high-switch campaigns ran on RB-T-P016-approved profiles with no retried-away failure.

Any unresolved FP/SIMD corruption, stale-code/TLB behavior, W+X window, platform drift, or reuse leak is a hard blocker—not “follow-up hardening.”
### Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Strong corrected gate. Require single-CPU FP evidence; migration belongs to Gate 2. Add RB-T-P100 and fix EL wording.
