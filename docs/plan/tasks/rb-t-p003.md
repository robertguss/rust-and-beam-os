---
schema: "repo-plan/v1"
id: "RB-T-P003"
title: "Pin the complete host and target toolchain with build receipts"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P001"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-03"
x_linear_id: "ROB-685"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-685/p0-03-pin-the-complete-host-and-target-toolchain-with-build-receipts"
x_labels:
  - "ready-for-agent"
---
# RB-T-P003: Pin the complete host and target toolchain with build receipts

## Goal

Replace moving toolchain assumptions with one reproducible, auditable candidate set.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P001.

## Deliverables

* Experimentally verify and pin a compatible OTP/Elixir pair; begin with OTP 29.0.5 and Elixir 1.20.4 unless evidence selects another maintained pair.
* Pin Rust, Cargo, the AArch64 bare-metal target, C/C++ cross compiler, musl source/toolchain, QEMU, build utilities, and container base by immutable version or digest.
* Document x86_64-Linux and AArch64-Linux builder paths and the Apple Silicon QEMU runner requirement.
* Generate a machine-readable build receipt and human-readable toolchain report.

## Acceptance criteria

- [ ] A clean builder resolves no unpinned `latest` dependency.
- [ ] The receipt includes source URLs, versions, hashes, licenses, compiler/linker identity, target triples, and container digest.
- [ ] Two fresh Linux builders produce matching toolchain metadata.
- [ ] The selected OTP/Elixir pair runs the reference application before it is frozen.

## Verification

* `just toolchain-bootstrap`
* `just toolchain-report`
* `just toolchain-verify`

## Evidence

* Recreate the environment in two clean VMs or clean containers.
* Compare normalized receipts and explain any host-specific fields.
* Commit the version-selection ADR.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

* The reference application in this issue is a deliberately minimal smoke project only. The complete supervised `runtime_lab` application is owned by RB-T-P002 and is blocked by this issue.
* Pin exact Rust, LLVM/LLD, C cross-toolchain, musl, OTP, Elixir, QEMU, build-container base image, and host helper versions by digest where possible. “Latest” is forbidden in reproducible paths.
* The environment must expose separate commands for native AArch64 Linux/full-system validation and qemu-user smoke tests; qemu-user cannot satisfy thread, signal, auxv, or startup-contract gates.
* Record target CPU/features and linker flags in the build receipt so they can be reconciled with RB-T-P014.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Pin exact source and binary digests after probes; include QEMU machine types, cross compiler/sysroot, linker, Rust target flags, and offline/sealed rebuild.
