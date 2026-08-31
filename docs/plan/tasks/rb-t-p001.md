---
schema: "repo-plan/v1"
id: "RB-T-P001"
title: "Create the repository, evidence model, and reproducible build shell"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on: []
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-01"
x_linear_id: "ROB-684"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-684/p0-01-create-the-repository-evidence-model-and-reproducible-build"
x_labels:
  - "ready-for-agent"
---
# RB-T-P001: Create the repository, evidence model, and reproducible build shell

## Goal

Create the implementation repository structure and a repeatable Linux build shell before any kernel or runtime work begins.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: None — this can start immediately.

## Deliverables

* Create the Cargo workspace and the planned `kernel/`, `userspace/`, `beam/`, `abi/`, `protocol/`, `image/`, `toolchain/`, `xtask/`, `tests/`, `docs/`, and `ai/` trees.
* Add `rust-toolchain.toml`, dependency policy placeholders, a readable `justfile`, and an `xtask` skeleton.
* Add `docs/architecture.md`, `docs/invariants.md`, an ADR template, an evidence-index format, a learning log, and the AI task template.
* Define build IDs and evidence metadata: source revision, dirty state, tool versions, target, command, input hashes, artifact hashes, and result.

## Acceptance criteria

- [ ] A fresh remote Linux VM can bootstrap the repository using one documented command sequence.
- [ ] `just check` succeeds and exposes discoverable placeholder commands without hiding their underlying commands.
- [ ] An evidence fixture validates against the documented schema and points to immutable inputs/artifacts.
- [ ] No kernel implementation beyond a compiling skeleton is introduced.

## Verification

* `just check`
* `just evidence-check`

## Evidence

* Run the bootstrap from a fresh clone in a clean Linux VM.
* Run `just check` and the evidence-schema validation.
* Save the transcript and environment receipt under `docs/evidence/phase-0/`.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Add machine-readable source/claim ledger, sealed dependency/source mirror policy, checksums, and gate-aware label automation.
