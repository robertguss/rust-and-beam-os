---
schema: "repo-plan/v1"
id: "RB-T-P007"
title: "Pair a genuine Mix release with the target ERTS"
type: "task"
state: "in_progress"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P005"
  - "RB-T-P002"
  - "RB-T-P006"
related: []
actor: "agent"
owner: "amp:T-01a05fea-257c-73e8-966c-c4b4192e7854"
defer_until: null
evidence: []
x_legacy_id: "P0-07"
x_linear_id: "ROB-692"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-692/p0-07-pair-a-genuine-mix-release-with-the-target-erts"
x_labels:
  - "ready-for-agent"
---

# RB-T-P007: Pair a genuine Mix release with the target ERTS

## Goal

Prove that a real Mix-generated Elixir release can boot with the exact
cross-built target ERTS.

## Context

[Architecture & Validation Plan](../architecture.md)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run
against the pinned project artifacts and preserve the own-kernel hypothesis.
Host-side programs are scaffolding and evidence only; they do not satisfy the
final POC.

Blocked by: RB-T-P002, RB-T-P005, RB-T-P006.

## Deliverables

- Generate the `runtime_lab` release without embedding host ERTS, or point
  `include_erts` at the staged target ERTS if that is the clean supported route.
- Pair the release payload with the exact target runtime and preserve normal OTP
  release structure.
- Create a launcher manifest containing root directory, boot script, code paths,
  config providers, VM flags, environment, and arguments.
- Start `beam.smp` directly without an interactive shell, `erlexec`, general
  guest `exec`, or hand-copying an ad hoc set of `.beam` files.

## Acceptance criteria

- [ ] The target ERTS boots the Mix-generated release on AArch64 Linux.
- [ ] `Application.ensure_all_started/1`, configuration loading, supervision,
      reference workloads, and clean shutdown work normally.
- [ ] The release reports the exact pinned Elixir/OTP versions and artifact
      build ID.
- [ ] The assembly process is reproducible and contains no host-architecture
      ERTS or native dependency.

## Verification

- `just build-release`
- `just pair-release`
- `just test-target-release-linux`

## Evidence

- Build and boot from a clean Linux environment.
- Inspect the release tree and all native artifacts.
- Save launcher manifest, logs, inventory, and hashes.

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

The immutable-image design forbids the default runtime-config path unless a
writable volatile filesystem is deliberately added. For this POC:

- Set the release `runtime_config_path: false` and use build-time `sys.config`,
  `vm.args`, arguments, and environment compiled into the immutable image.
- Do not configure `Config.Provider`/`Config.Reader` runtime providers: Elixir
  documents that providers write their merged result to a mutable configuration
  file and reboot the system.
- Prove the release starts when its entire tree is read-only and when every
  undeclared write attempt fails. Record all attempted opens with flags.
- Package the exact target ERTS explicitly and verify that the release does not
  substitute a host ERTS, host launcher, shell, or `exec` path.
- Inventory scripts in the generated release, but boot `beam.smp` directly from
  the kernel's process manifest; shell scripts are host inspection artifacts
  only.

### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Correct gate. Inventory all native artifacts and prove direct beam launch,
config loading, read-only operation, and clean shutdown.
