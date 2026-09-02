---
schema: "repo-plan/v1"
id: "RB-T-P018"
title: "Disposition ERTS helper processes"
type: "task"
state: "in_progress"
priority: "P0"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P004"
  - "RB-T-P005"
  - "RB-T-P006"
  - "RB-T-P007"
  - "RB-T-P017"
related: []
actor: "agent"
owner: "amp:T-01a05912-a43d-754e-84fc-d56536c31a76"
defer_until: null
evidence: []
---

# RB-T-P018: Disposition ERTS helper processes

## Goal

Determine whether the exact OTP profile can boot and run without ERTS helper
process creation through a small, sealed Unix OS-glue option. Reject general
`fork`/`exec` support in the custom kernel rather than hiding it in the host
contract.

## Context

[Architecture & Validation Plan](../architecture.md)

The exact P007 artifact unconditionally starts `erl_child_setup` and later
`inet_gethost`, while M2 excludes general process creation. This is a Gate 0
contradiction, not an implementation detail. P018 must either repair it within
the architecture's existing host-adapter diff budget or record that H1/H2 fail.

Blocked by: RB-T-P004, RB-T-P005, RB-T-P006, RB-T-P007, RB-T-P017.

Blocks: RB-T-P008, RB-T-P014, RB-G-GATE0.

## Deliverables

- Add ADR 0002 comparing: A) kernel-supported helper spawning, B) a sealed ERTS
  Unix OS-glue option, and C) a Linux-hosted pivot. Select B only if all
  acceptance criteria below pass; otherwise select C. Record the H1 wording and
  define whether metadata-only UDP socket probes count as networking under H2.
- Add a compile-time option—not an environment or runtime switch—that skips the
  forker-port startup while preserving `erts_sys_unix_later_init`, and makes
  external-program spawn requests fail synchronously with `ENOTSUP` before
  creating pipes or touching a forker port.
- Configure the immutable release for file-only hostname lookup and remove
  `erl_child_setup` and `inet_gethost` from the paired image.
- Produce a sealed, digest-pinned patched artifact and reproducible build
  receipt whose diff is confined to Unix OS glue and immutable release
  configuration.
- Repeat the authoritative full-system AArch64 Linux runtime and Mix-release
  workloads, plus negative tests for every disabled spawn/resolver path.
- Record a source-backed syscall delta and an explicit disposition for the three
  observed `AF_INET` UDP port-zero probes.

## Acceptance criteria

- [ ] Two clean builds produce the same patched native closure and exact
      `beam.smp` digest; the complete patch is saved and explained line by line.
- [ ] The patch changes no scheduler, GC, loader, BEAM instruction, process, or
      code-loading semantics. It remains confined to `erts/emulator/sys/unix/`
      plus release configuration; exceeding 40 non-generated changed lines or
      escaping that boundary forces an explicit Gate 0 repair/pivot decision
      rather than silent scope growth.
- [ ] Ten authoritative full-system AArch64 Linux boots of the exact paired Mix
      release pass startup, IPC-ready idle, reference workloads, supervised
      crashes, shutdown, and the final scheduler profile.
- [ ] Normalized target traces contain zero helper `clone(SIGCHLD)`, helper
      `execve`, `setsid`, `wait4`, SCM_RIGHTS transfer, or `inet_gethost`
      activity. `erl_child_setup` and `inet_gethost` are absent from the image.
- [ ] `init:stop`, SIGTERM, `os:cmd`, external `open_port` spawn forms, `heart`,
      and native hostname lookup each have a declared result and bounded test;
      unsupported operations fail honestly without hanging or destabilizing
      ERTS.
- [ ] Runtime evidence and a source assertion prove `erts_sys_unix_later_init`
      remains active.
- [ ] UDP probes are eliminated or ADR 0002 proves and accepts a metadata-only
      operation with no connect, send, listen, packet, external endpoint, or
      network-device path. If that interpretation is unacceptable, H2 fails.
- [ ] General process creation is removed from the required custom-kernel host
      contract; no bounded `fork`, copied-address-space helper, or
      artifact-specific success emulation is proposed.

## Verification

```sh
just build-otp-helperless
just inspect-otp-helperless
just test-target-helperless-linux
just test-target-release-helperless-linux
just check
```

## Evidence

Store the ADR, exact patch, clean-build comparison, native inventories, ten-boot
receipts, normalized traces, syscall delta, negative-operation matrix, and
verification transcript under `docs/evidence/phase-0/RB-T-P018/`.

## Out of scope

- Implementing `fork`, `vfork`, `exec`, child address-space copying, arbitrary
  external programs, a shell, or a general process lifecycle in the kernel.
- Changing OTP scheduler, GC, loader, BEAM execution, Erlang process, or code
  loading semantics.
- Treating Linux init/strace scaffolding as custom-kernel evidence.
- Adding a network data path, DNS client, dynamic loading, writable storage,
  third-party NIFs, or phone hardware.

## Stop rule

Pivot to a Linux-hosted Rust/BEAM system if the patch cannot stay inside the
declared Unix OS-glue boundary, required OTP applications need a live forker,
honest spawn failure destabilizes the VM, helper execution remains, or the
remaining contract requires process creation, a network data path, dynamic
loading, or broad pseudo-filesystem emulation.

## Learning checkpoint

Explain why correct `fork` requires address-space snapshot semantics, why a
helper-specific approximation would invalidate H2, and how the patched traces
prove absence rather than merely an unexercised helper path.
