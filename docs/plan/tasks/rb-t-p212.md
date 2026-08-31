---
schema: "repo-plan/v1"
id: "RB-T-P212"
title: "Build the complete static-musl conformance suite from the host contract"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P211C"
  - "RB-T-P211B"
  - "RB-T-P211A"
  - "RB-E-P204"
  - "RB-E-P210"
  - "RB-E-P209"
  - "RB-T-P207"
  - "RB-E-P206"
  - "RB-T-P202"
  - "RB-T-P203"
  - "RB-T-P208"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-12"
x_linear_id: "ROB-723"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-723/p2-12-build-the-complete-static-musl-conformance-suite-from-the-host"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P212: Build the complete static-musl conformance suite from the host contract

## Goal

Turn each admitted libc/thread behavior into a small diagnostic program that localizes failures before ERTS is introduced.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P202, RB-T-P203, RB-E-P204, RB-E-P206, RB-T-P207, RB-T-P208, RB-E-P209, RB-E-P210, RB-E-P211.

## Deliverables

* Create focused static C probes for startup, args/env/auxv, TLS/errno, files/directories, mappings/guards, pthread lifecycle, mutex/cond/once/TLS, futex races, robust cleanup, signals, pipes/poll, time, randomness, and system queries.
* Give each probe a machine-readable result schema, timeout, seed, cleanup assertion, and exact expected outcome.
* Map every `beam-host.yaml` entry to positive, negative, boundary, error, and concurrency cases where applicable.
* Run the same probes on pinned AArch64 Linux and normalize only intentionally different values.

## Acceptance criteria

- [ ] Contract coverage reports 100% of admitted entries and flags linked to executable evidence.
- [ ] A deliberately broken implementation in each major family causes the expected probe to fail.
- [ ] No probe relies on shell behavior, networking, dynamic linking, or an unrecorded host file.
- [ ] Failures identify the syscall family, operation, expected/actual result, seed, and last trace events.

## Verification

* `just test-musl-reference`
* `just test-musl-guest`
* `just beam-abi-coverage`

## Evidence

* Run the full suite on reference Linux and the custom guest.
* Run coverage mutation checks for each major family.
* Publish normalized comparison and known intentional differences.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit correction — 2026-08-30

### Coverage is semantic, not merely numeric

* Expand coverage units from “syscall entry” to every admitted operation, flag combination, structure size/version, input class, error precedence, blocking/interrupt/restart outcome, state transition, concurrency race, resource bound, and cleanup path.
* Include startup ELF/stack/auxv/HWCAP/TLS, atomic baseline, CPU/migration/TLB shootdown, VFS/path bytes, VMA generations, clone publication/rollback, clear-child-TID/join, futex, robust list, signal state/frame/return, waits/restarts/cancellation, streams/descriptors/poll, clocks/timers, entropy, and platform-query consistency.
* Parent tracking issues do not count as evidence. The report must enumerate and link each implementation child and its positive, negative, boundary, fault-injection, race, and conservation tests.

### Independent oracles

* Generate probe inventory and bookkeeping from `beam-host.yaml`, but do not generate expected behavior solely from the same implementation constants/code paths being tested. Use pinned AArch64 Linux results, ABI headers/specification, hand-reviewed canonical fixtures, simple independent reference models, and metamorphic invariants to avoid tautological tests.
* Thread, signal, TLS, auxv/HWCAP, robust-list, interruption/restart, and startup-gate reference results come from native AArch64 Linux or a full-system AArch64 VM. qemu-user results are smoke/differential hints only.
* Normalize only explicitly approved nondeterministic values. Preserve raw outputs before normalization and fail on any newly normalized field.
* Each probe runs with a sealed file/environment/CPU profile, exact static binary hash, timeout/progress oracle, deterministic seed where applicable, result schema version, and zero-resource-delta assertion.

### Mutation and evidence quality

* Mutation canaries must break at least one behavior in every major family, including wrong errno precedence, missing flag rejection, lost wake, stale generation, timeout extension, unsafe signal restore, robust-list omission, W^X/TLB fault, deterministic production entropy, and platform contradiction.
* Detect false passes: zero assertions, skipped cases, missing reference result, test process that never reached the target operation, trace overflow, unparsed output, timeout classified as expected, or harness exit masked by a guest sentinel.
* Report both implementation coverage and observed workload coverage. A behavior can remain admitted only when required or intentionally conservative with rationale; unused broad support is not rewarded as coverage.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Generate positive/negative/race/error tests from contract and publish behavior-level coverage, not syscall-name coverage.
