---
schema: "repo-plan/v1"
id: "RB-T-P006"
title: "Run the target ERTS artifact on AArch64 Linux"
type: "task"
state: "in_progress"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P005"
related: []
actor: "agent"
owner: "amp:T-01a05912-a43d-754e-84fc-d56536c31a76"
defer_until: null
evidence: []
x_legacy_id: "P0-06"
x_linear_id: "ROB-693"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-693/p0-06-run-the-target-erts-artifact-on-aarch64-linux"
x_labels:
  - "ready-for-agent"
---

# RB-T-P006: Run the target ERTS artifact on AArch64 Linux

## Goal

Separate cross-build defects from custom-kernel defects by proving the target
ERTS on a normal AArch64 Linux reference host.

## Context

[Architecture & Validation Plan](../architecture.md)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run
against the pinned project artifacts and preserve the own-kernel hypothesis.
Host-side programs are scaffolding and evidence only; they do not satisfy the
final POC.

Blocked by: RB-T-P005.

## Deliverables

- Run the exact static target `beam.smp` on AArch64 Linux hardware or a
  full-system AArch64 Linux VM.
- Start with a minimal Erlang evaluation, then run the non-JIT reference
  workloads with the final intended VM flags.
- Record runtime identity, native thread topology, file accesses, mappings,
  signals, syscalls, memory use, and shutdown behavior.
- Package a one-command repeatable reference run for x86_64 remote builders
  using emulation when native AArch64 is unavailable.

## Acceptance criteria

- [ ] `erlang:display(ok), halt().` or its direct equivalent succeeds.
- [ ] Processes, messages, timers, binaries, ETS, and forced GC run using the
      target artifact.
- [ ] The runtime uses the expected non-JIT flavor and final candidate
      scheduler/dirty/async configuration.
- [ ] No dependency on a dynamic linker, application NIF, network service, or
      unrecorded host file exists.

## Verification

- `just run-target-erts-linux`
- `just test-target-erts-linux`

## Evidence

- Run ten clean reference boots.
- Save normalized traces and runtime identity.
- Compare the observed calls with `beam-host.yaml` revision 0.

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

- The authoritative target-Linux run must execute on native AArch64 Linux or a
  full-system AArch64 VM whose machine/CPU/auxv are captured. qemu-user may
  provide fast smoke and differential evidence only; it does not satisfy thread,
  signal, TLS, auxv/HWCAP, startup, timing, or syscall-interruption acceptance.
- Capture `AT_PAGESZ`, `AT_HWCAP`, `AT_HWCAP2`, CPU model/features, cache-line
  information, ELF load addresses, TLS layout, signal frame details, and all
  files/descriptors observed. Feed the normalized values into RB-T-P014.
- Exercise at least single-scheduler and final two-scheduler profiles. A
  successful `main`/identity print is necessary but does not prove scheduler
  progress or correct blocking semantics.
- Any use of host-provided `/proc`, `/sys`, locale, timezone, NSS, DNS, entropy
  devices, executable paths, or dynamically loaded components must be classified
  as required, removable, or forbidden.

### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Authoritative evidence must use native AArch64 or full-system AArch64 Linux.
qemu-user is smoke-only. Repeat startup/thread/signal/shutdown and capture full
artifact closure.
