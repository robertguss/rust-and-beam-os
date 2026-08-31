---
id: "GATE-1"
linear_id: "ROB-708"
linear_url: "https://linear.app/robert-guss/issue/ROB-708/gate-1-decide-whether-the-kernel-spine-is-trustworthy-enough-for-the"
title: "Decide whether the kernel spine is trustworthy enough for the musl contract"
milestone: "M1"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P1-00"
  - "P1-14"
  - "P1-13"
  - "P1-12"
  - "P1-11"
  - "P1-10"
  - "P1-09"
  - "P1-08"
  - "P1-07"
  - "P1-05"
  - "P1-06"
  - "P1-01"
  - "P1-02"
  - "P1-04"
  - "P1-03"
blocks:
  - "P2-05a"
  - "P2-00"
  - "P2-01"
  - "P2-05"
---
# GATE-1: Decide whether the kernel spine is trustworthy enough for the musl contract

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Approve, narrow, repair, or stop the kernel foundation before implementing deep libc/thread semantics.

## Locked context

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

## What to build

* Review the M1 milestone criteria, 1,000-boot report, fault-containment evidence, memory/scheduler model tests, image reproducibility, observability, and unsafe-code inventory.
* Confirm that core/kernel/platform boundaries match the architecture and no existing OS framework supplies the scheduler, VM, ABI, or VFS.
* List every known flake, unclassified fault, unchecked unsafe block, and deferred invariant.
* Record Continue, Repair within M1, Narrow the runtime target, Pivot, or Stop.

## Acceptance criteria

- [ ] Continue is forbidden while any unclassified kernel fault, user/kernel isolation failure, memory-accounting discrepancy, or non-reproducible flake remains.
- [ ] The decision links each milestone exit criterion to evidence.
- [ ] Any accepted residual risk has an owner, detection mechanism, and downstream constraint.
- [ ] All M2 issues remain blocked until this gate is Done and the user approves the decision.

## Required tests and evidence

* Run a fresh-session audit using only repository plan content and evidence artifacts.
* Publish the gate ADR/status update and name the next issue.
* Confirm downstream dependency links.

## Verification commands

* `just gate-report 1`
* `just evidence-check --phase 1`

## Dependencies

Blocked by: P1-01, P1-02, P1-03, P1-04, P1-05, P1-06, P1-07, P1-08, P1-09, P1-10, P1-11, P1-12.

## Out of scope

* ERTS, Elixir, musl/pthreads, GPU UI integration, networking, writable storage, and phone hardware.
* General POSIX/Linux compatibility or a production security claim.
* Broad optimization before correctness evidence.

## Completion rule

Do not mark Done until every acceptance item has durable evidence from the exact build. Preserve any failing seed or trace; never convert a flake into success by blind retry.

## Learning checkpoint

Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process, the invariant this slice protects, one race or memory-corruption failure mode, and how the tests expose it.

## Readiness-audit correction — 2026-08-30

GATE-1 may authorize M2 only when all original criteria plus these hold:

- [ ] The guest platform identity matches the frozen versioned QEMU/CPU/GIC/HWCAP contract; no unapproved runner or feature drift is present.
- [ ] FP/AdvSIMD state is isolated across EL0 tasks, preemption, faults, task reuse, and available migration tests; unsupported extended state is disabled/unadvertised.
- [ ] Every executable load performs the reviewed D-cache/I-cache/barrier sequence and every translation change performs reviewed TLB maintenance through one API.
- [ ] W^X holds during load and permission transition, not just after it; no stale executable or stale translation canary remains.
- [ ] ELF/stack/auxv validation matches the exact native artifact shapes and fails closed on every unsupported header, relocation, TLS, or dynamic-loading form.
- [ ] Address-space/ASID/task/handle reuse has generation/lifetime evidence and zero cross-process data disclosure.
- [ ] The 1,000-boot and high-switch campaigns ran on P0-16-approved profiles with no retried-away failure.

Any unresolved FP/SIMD corruption, stale-code/TLB behavior, W+X window, platform drift, or reuse leak is a hard blocker—not “follow-up hardening.”

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Strong corrected gate. Require single-CPU FP evidence; migration belongs to Gate 2. Add P1-00 and fix EL wording.
