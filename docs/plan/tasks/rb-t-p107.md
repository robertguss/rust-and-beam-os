---
schema: "repo-plan/v1"
id: "RB-T-P107"
title: "Define native ABI v1 and capability-scoped handle tables"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-E-P106"
  - "RB-E-P105"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-07"
x_linear_id: "ROB-703"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-703/p1-07-define-native-abi-v1-and-capability-scoped-handle-tables"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P107: Define native ABI v1 and capability-scoped handle tables

## Goal

Give new Rust userspace services a project-owned ABI that does not inherit the ERTS Linux personality.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-E-P105, RB-E-P106.

## Deliverables

* Specify `abi/native-v1.md` with calling convention, result/error representation, ABI versioning, and the initial handle, VM, thread, time, log, and process-exit operations.
* Implement per-process typed handle tables with rights, generation protection, duplication policy, closure, and wait/read/write dispatch.
* Implement the EL0 syscall entry/return path and a small userspace runtime wrapper.
* Make image-build manifests, not path names or ambient authority, provision handles.

## Acceptance criteria

- [ ] A process can use only explicitly provisioned handles and rights.
- [ ] Wrong type, stale generation, missing right, invalid operation, and table exhaustion return specified errors.
- [ ] Handle closure wakes or fails waiters according to documented semantics.
- [ ] ABI layout tests compare kernel and userspace definitions and fail on accidental drift.

## Verification

* `just test-native-abi`
* `just fuzz-handles`

## Evidence

* Run positive/negative handle tests and syscall ABI fixtures.
* Fuzz handle indices, generations, rights, and user arguments.
* Save the native-v1 ABI and capability-model ADR.

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

Define generation-safe handles, rights attenuation, close/wait races, process teardown, ABI versioning, and exact copy rules.
