---
schema: "repo-plan/v1"
id: "RB-T-P110"
title: "Build the immutable system archive and manifest-driven boot plan"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-E-P108"
  - "RB-T-P104"
  - "RB-T-P101"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-10"
x_linear_id: "ROB-707"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-707/p1-10-build-the-immutable-system-archive-and-manifest-driven-boot-plan"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P110: Build the immutable system archive and manifest-driven boot plan

## Goal

Create a deterministic read-only image path that can later carry renderer and ERTS artifacts without a writable filesystem.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-T-P101, RB-T-P104, RB-E-P108.

## Deliverables

* Define a compact read-only archive format with checked header, path, extent, alignment, hash, and duplicate-entry rules.
* Implement host-side image assembly in `xtask` and read-only guest lookup/read operations.
* Compile `image/system.toml` into a validated boot plan containing process image, ABI personality, handles/fds, memory limits, and arguments.
* Supply the archive as the Phase 0-selected initrd or linked section and keep transport separate from archive semantics.

## Acceptance criteria

- [ ] The kernel launches the native hello process from the archive and compiled boot plan.
- [ ] Two builds from identical inputs produce the same archive digest.
- [ ] Malformed paths, duplicate entries, overlapping extents, bad hashes, truncated data, and oversized files fail safely.
- [ ] The guest cannot mutate archive contents or introduce undeclared processes/handles.

## Verification

* `just image`
* `just inspect-image`
* `just test-image`

## Evidence

* Run archive parser property/fuzz tests and deterministic-build comparison.
* Inspect the boot-plan and image inventory.
* Save the archive-format ADR and build receipt.

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

Freeze archive format, path normalization, duplicate/collision rules, hash coverage, parser limits, capability compilation, and malformed-image behavior.
