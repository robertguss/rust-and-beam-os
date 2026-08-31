---
schema: "repo-plan/v1"
id: "RB-E-P108"
title: "TRACKING: Complete static ELF staging, executable publication, and EL0 entry"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P108B"
  - "RB-T-P108A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-08"
x_linear_id: "ROB-704"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-704/p1-08-tracking-complete-static-elf-staging-executable-publication-and"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P108: TRACKING: Complete static ELF staging, executable publication, and EL0 entry

## Goal

Prove the complete kernel-to-userspace boundary with a real statically linked native Rust process.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This work targets the project-owned AArch64 kernel on QEMU `virt`. Phase 1 is single-CPU except where a test explicitly prepares an SMP-safe interface. It must use the native project ABI, not the ERTS Linux-compatible personality.

Blocked by: RB-E-P105, RB-T-P107.

## Deliverables

* Implement a static AArch64 ELF loader for the admitted program-header types and relocation-free POC profile.
* Validate offsets, sizes, alignment, address ranges, permissions, entry point, overlap, and integer arithmetic before mapping.
* Create the initial user stack, process metadata, address space, and return-to-EL0 frame.
* Build a tiny native `hello` process that writes through a log handle, reads monotonic time, sleeps, and exits.

## Acceptance criteria

- [ ] The hello process starts at its ELF entry point in EL0 and completes only through native ABI calls.
- [ ] Malformed, overlapping, truncated, writable-executable, kernel-overlapping, and invalid-entry ELF fixtures are rejected.
- [ ] Process exit releases its mappings, frames, and handles without leaks.
- [ ] A crash in the process does not corrupt the kernel or another test process.

## Verification

* `just build-userspace`
* `just test-elf-loader`
* `just run-native-hello`

## Evidence

* Run host ELF parser fuzz/property tests.
* Run guest success, malformed-image, exit, and crash tests.
* Save ELF inventory, process layout, and cleanup counters.

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

* Load the exact ELF class/type actually produced by the native Rust user build and P0 ERTS inspection; reject unsupported `PT_INTERP`, dynamic dependencies, TLS/relocation forms, overlapping segments, integer overflow, misalignment, out-of-file ranges, W+X segments, and entry points outside executable mappings.
* Build the initial AArch64 stack and auxv from a typed structure with ABI alignment, bounded argument/environment strings, `AT_PHDR`/`AT_PHENT`/`AT_PHNUM`, `AT_PAGESZ`, `AT_ENTRY`, `AT_RANDOM`, `AT_HWCAP`, and `AT_HWCAP2` as required by the frozen contract. Do not copy arbitrary host auxv values.
* ELF text is copied into writable+NX staging pages, then published RX only through RB-T-P114's D-cache/I-cache/TLB/barrier path.
* Initial register/SPSR/stack/TLS/FP state must be deterministic and contain no previous-task data. EL0 returns, faults, syscalls, and process exit must preserve kernel integrity.
* Add malformed-ELF corpus generation, boundary truncation at each structure, duplicate/overlapping program headers, relocation/TLS edge cases admitted by the final artifact, stack/auxv fuzzing, and executable-cache canaries.
* The basic loader may land before RB-T-P113/RB-T-P114, but RB-E-P108 is not sufficient evidence for Gate 1 until those obligations pass.
### Implementation-readiness disposition — 2026-08-30

**Action:** RELATION + SPLIT

Split validation/staging from publish/execute. RB-T-P114 must block execution; general hard-float process requires RB-T-P113.
