---
id: "GATE-2"
linear_id: "ROB-721"
linear_url: "https://linear.app/robert-guss/issue/ROB-721/gate-2-decide-whether-the-erts-host-contract-is-bounded-and"
title: "Decide whether the ERTS host contract is bounded and trustworthy"
milestone: "M2"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P2-11c"
  - "P2-11b"
  - "P2-11a"
  - "P2-13a"
  - "P2-00"
  - "P2-14"
  - "P2-13"
  - "P2-09"
  - "P2-12"
  - "P2-10"
  - "P2-05"
  - "P2-08"
  - "P2-07"
  - "P2-02"
  - "P2-06"
  - "P2-03"
  - "P2-01"
  - "P2-04"
blocks:
  - "P3-01"
---
# GATE-2: Decide whether the ERTS host contract is bounded and trustworthy

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Make the final pre-ERTS decision: continue only if libc/thread semantics are correct and the compatibility adapter has not become a hidden Linux reimplementation.

## Locked context

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

## What to build

* Review the contract revision, conformance coverage, one-hour contention run, semantic-difference report, unsafe inventory, memory budget, and every unknown/unclassified event.
* Score H2 and update H1 using measured contract breadth and semantic depth.
* Identify which bugs would be ERTS blockers versus ordinary post-POC hardening.
* Record Continue, Repair within M2, Narrow the ERTS profile, Pivot to a direct ERTS port or Linux-based system, or Stop.

## Acceptance criteria

- [ ] Continue requires all admitted contract behavior tested, no unknown calls, no unexplained resource drift, and no unresolved pthread/futex/signal race.
- [ ] The decision explicitly addresses whether this is still a bounded compatibility personality rather than a general Linux/POSIX project.
- [ ] Any repair decision keeps M3 blocked and names exact failing tests.
- [ ] The user approves the decision and next issue.

## Required tests and evidence

* Conduct a fresh-session audit using only repository plan content and evidence.
* Publish the gate ADR/status update.
* Confirm every M3 issue is blocked by this gate.

## Verification commands

* `just gate-report 2`
* `just evidence-check --phase 2`

## Dependencies

Blocked by: P2-01, P2-02, P2-03, P2-04, P2-05, P2-06, P2-07, P2-08, P2-09, P2-10, P2-11, P2-12, P2-13, P2-14.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.

## Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.

## Readiness-audit correction — 2026-08-30

### Mandatory authorization conditions

M3 remains blocked unless all original criteria plus the following are satisfied:

- [ ] The exact platform/ABI identity is internally consistent: versioned machine/CPU/GIC/devices, page/cache properties, auxv/HWCAPs, atomic instruction policy, TLS, FP/SIMD, signal frame, vCPU count/affinity, clocks, entropy, limits, and artifact shape.
- [ ] Every admitted semantic unit—not just every syscall number—has independent positive, negative, boundary, fault-injection, race, error-precedence, resource-bound, cleanup, and mutation evidence as applicable.
- [ ] SMP CPU bring-up, scheduler/wakeup/migration, and acknowledged TLB shootdowns preserve task/page/ASID/FP-state ownership with no stale remote state.
- [ ] Clone publication/rollback, clear-child-TID, join/detach, futex, robust-list cleanup, and TID/object reuse form one proven lifecycle with no missed wake, ABA, or double reclamation.
- [ ] Signal state, AArch64 frame/alternate-stack/FPSIMD return, and syscall interruption/restart/cancellation pass the complete table-driven race matrix; unsupported context extensions remain disabled and rejected.
- [ ] Stream/descriptor and poll readiness semantics are bounded, level-correct, generation-safe, and pass close/reuse/interruption stress.
- [ ] All timed waits share the same absolute monotonic deadline; production entropy is non-deterministic/fail-closed; guest identity cannot leak the host.
- [ ] The preregistered M2 campaign met duration and operation floors on an evidence-appropriate runner with valid artifacts, zero unexplained drift, and no retried-away failure.
- [ ] The revision-2 audit found no reachable undocumented behavior, hidden Linux expansion, host passthrough, permissive fallback, or semantic workaround.
- [ ] In particular, no spin/yield/readiness-marker/futex relaxation is being accepted merely because it lets ERTS boot; any such diagnostic result is an unresolved central-hypothesis failure.

### Decision rule

The decision must be exactly one of **Authorize M3**, **Repair M2**, **Narrow the ERTS profile**, **Pivot to a direct ERTS port**, **Pivot to a Linux-based system**, or **Stop**. The user must explicitly approve authorization. Automated green checks are necessary but not sufficient.

A contract that is small by call count but deep enough to require general process, signal, VFS, networking, dynamic-loading, or writable-filesystem behavior does not qualify as bounded. The gate report must quantify both breadth and semantic depth and compare them with the Phase 0 estimate.

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Add hard blockers for unexplained wait workaround, signal-frame uncertainty, time/entropy substitution, fd/poll lifetime gap, or shootdown failure.
