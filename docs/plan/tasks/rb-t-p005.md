---
schema: "repo-plan/v1"
id: "RB-T-P005"
title: "Cross-build static non-JIT AArch64-musl upstream ERTS"
type: "task"
state: "in_progress"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P003"
related: []
actor: "agent"
owner: "amp:T-01a05912-a43d-754e-84fc-d56536c31a76"
defer_until: null
evidence: []
x_legacy_id: "P0-05"
x_linear_id: "ROB-688"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-688/p0-05-cross-build-static-non-jit-aarch64-musl-upstream-erts"
x_labels:
  - "ready-for-agent"
---

# RB-T-P005: Cross-build static non-JIT AArch64-musl upstream ERTS

## Goal

Produce the exact upstream ERTS artifact the custom OS is intended to host.

## Context

[Architecture & Validation Plan](../architecture.md)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run
against the pinned project artifacts and preserve the own-kernel hypothesis.
Host-side programs are scaffolding and evidence only; they do not satisfy the
final POC.

Blocked by: RB-T-P003.

## Deliverables

- Use the official OTP cross-compilation flow with the pinned AArch64-musl
  toolchain.
- Disable JIT and kernel poll for the first profile; exclude `wx`, Java, ODBC,
  crypto/SSL, SSH, and other applications not required by `runtime_lab`.
- Build a static `beam.smp` with no dynamic interpreter and no semantic changes
  to scheduler, GC, loader, or BEAM execution.
- Capture the complete configure environment, cross answers, commands, generated
  configuration, source hash, patch set, ELF metadata, symbols, size, and linked
  objects.

## Acceptance criteria

- [ ] The artifact is AArch64, static, and has no unresolved dynamic
      interpreter/dependencies.
- [ ] The build starts from the pinned upstream tag and a clean builder.
- [ ] Any source patch is confined to build detection or an OS adapter,
      explained line-by-line, and included in the upstream-diff budget.
- [ ] Re-running the build produces an equivalent artifact or a documented
      reproducibility defect that blocks the gate.

## Verification

- `just build-otp`
- `just inspect-otp-artifact`
- `just verify-otp-rebuild`

## Evidence

- Inspect the ELF headers and dependency metadata.
- Rebuild from a clean environment.
- Archive the build receipt, logs, artifact hash, and patch audit.

## Out of scope

- Do not implement a Linux or Android guest.
- Do not add networking, writable persistent storage, dynamic linking,
  third-party NIFs, or phone hardware.
- Do not weaken an acceptance test merely to make the spike pass.

## Additional context

### Completion rule

Do not mark this issue Done until every acceptance item has a linked test,
trace, build receipt, ADR, or other durable evidence. If an assumption fails,
stop and create or update the relevant decision record instead of silently
changing scope.

### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and
how the saved evidence distinguishes success from an accidental demo.

### Readiness-audit correction — 2026-08-30

The target artifact gate is stricter than “the file links statically”:

- Prove with `readelf`/`llvm-readobj` that the final `beam.smp` has no
  `PT_INTERP`, no unresolved `DT_NEEDED`, and no undeclared dynamic loader path.
  Record whether it is `ET_EXEC` or static PIE/`ET_DYN`; the ELF loader must
  implement the artifact actually produced rather than assume one.
- Inventory every built-in driver, statically linked NIF/native library,
  excluded OTP application, and configure option. The enforceable policy is **no
  unapproved dynamically loaded native libraries, no third-party/application
  NIFs, and no dynamic drivers**—not the inaccurate claim that upstream ERTS
  contains zero native implementation.
- Reconcile compiler `-march`/`-mcpu`, LSE/outline-atomics behavior, TLS model,
  page-size assumptions, and auxv/HWCAP expectations with RB-T-P014.
- Save symbol/version/relocation/program-header reports and fail the build on
  artifact-shape drift.

### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

The appended audit correction is strong. Extend closure inspection across the
complete release tree and runtime load attempts.

### Normative readiness correction — 2026-08-30

Extend artifact-closure inspection across the entire Mix release tree, not only
`beam.smp`: inventory every native object, `.so`, built-in driver, statically
linked component, and runtime load attempt; seal the exact ELF type,
relocations, TLS model, CPU features, page size, and HWCAP assumptions.
