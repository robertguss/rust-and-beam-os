# ADR 0002: Use a sealed helperless ERTS host adapter

- Status: accepted
- Date: 2026-09-02
- Owners: robertguss
- Plan task: RB-T-P018
- Evidence: docs/evidence/phase-0/RB-T-P018/evidence.json

## Context

The exact P007 OTP 29.0.5 / ERTS 17.0.5 artifact starts `erl_child_setup`
unconditionally and later starts `inet_gethost`. Those helpers require process
creation, execution, session, wait, and descriptor-passing semantics that M2
excludes. Treating the observed calls as required would make the custom kernel a
partial Unix process host before testing the project's core Rust/BEAM
architecture.

Correct `fork` is not “start one known binary.” It snapshots the calling
process's address space and thread-visible state, gives the child a coherent
descriptor table and signal state, and preserves the parent/child return and
failure semantics under concurrency. A helper-specific copied-address-space or
success-emulation path would neither implement `fork` nor honestly test H2.

H1 permits a sealed host-adapter build option but previously lacked an exact
limit. H2 excludes a network data path, while baseline ERTS also creates three
`AF_INET` datagram sockets, binds each to wildcard port zero, queries metadata,
and closes them without connecting or transferring a packet. Both boundaries
need an explicit decision before Gate 0.

## Decision

Select the sealed ERTS Unix OS-glue adapter, alternative B below.

The helperless target profile applies compile-time flag `RB_ERTS_NO_FORKER=1`.
Its complete patch changes 11 non-generated lines in
`erts/emulator/sys/unix/sys_drivers.c` and is pinned by SHA-256
`75961539bb6859da5bcdaefc260fb66377243faa97c7ba1bbe06d5d285ee16ad`. It:

1. skips only the ERTS forker-port startup;
2. keeps `erts_sys_unix_later_init()` unconditional, including signal setup;
3. returns `ENOTSUP` synchronously from external-program `spawn_start` before
   creating pipes or touching a forker port.

The immutable Mix release selects `{lookup, [file]}` both in release
configuration and direct launch arguments. `erl_child_setup` and `inet_gethost`
are omitted from the target release after their omission digests are recorded.
Public hostname lookup is supported only through the configured file policy.
Direct calls to OTP's internal `inet_gethost_native` module are unsupported:
they bypass that policy, and upstream OTP 29 deliberately VM-halts if its port
program cannot be opened. A required OTP application or configured public API
reaching that internal backend forces reconsideration.

For H1, “upstream OTP” means upstream runtime semantics plus this sealed host
adapter, not a byte-identical upstream executable. A permitted adapter must be
compile-time-only, confined to `erts/emulator/sys/unix/` plus immutable release
configuration, change no scheduler, GC, loader, BEAM instruction, Erlang
process, or code-loading semantics, and remain at or below 40 non-generated
changed lines. Crossing any boundary is a Gate 0 repair or pivot, not an
incremental exception.

For H2, the observed UDP sequence is accepted as **metadata-only socket
probing**, not a network data path. The admitted sequence is limited to local
creation of an `AF_INET`/`SOCK_DGRAM` descriptor, wildcard port-zero `bind`,
`getsockname`/`getsockopt`, and `close`. It must have no `connect`, `listen`,
packet send or receive, external endpoint, route, interface, device, interrupt,
or DMA path. P008 must express and test this operation-level restriction. Any
network data path, or a human decision that any `AF_INET` socket violates H2,
falsifies H2.

## Governing invariant

The exact helperless ERTS and Mix release boot and retain normal VM,
application, supervision, workload, `init:stop`, and SIGTERM behavior without
creating an OS process or requiring helper execution. Every external spawn
request fails honestly with `ENOTSUP`; hostname lookup remains file-only; and
target traces contain no process clone, helper `execve`, session creation, child
wait, SCM_RIGHTS transfer, network connection, listener, or packet operation.

## Alternatives considered

### A. Implement helper spawning in the custom kernel

Rejected. A correct implementation expands into general address-space snapshot,
process, signal, descriptor, and child-lifecycle semantics. A bounded path that
works only for these two binaries is artifact-specific success emulation and
would invalidate H2 rather than satisfy it.

### B. Seal helper creation out of ERTS Unix OS glue

Selected because the adapter stays inside the H1 budget, clean rebuilds match,
normal and negative paths remain bounded, and traces prove that helper process
operations disappear rather than merely remain unexercised.

### C. Pivot to a Linux-hosted Rust/BEAM system

Retained as the mandatory fallback. Select this alternative if a required OTP
application needs the forker or native resolver; honest spawn failure
destabilizes an in-contract workload; the adapter escapes its source or line
budget; helper activity remains; or the remaining host contract requires general
process creation, network data, dynamic loading, or broad pseudo-filesystem
emulation.

## Consequences and residual risks

The custom kernel no longer needs `fork`, `vfork`, process-form `clone`,
`execve`, `setsid`, `wait4`, a helper `SIGCHLD` lifecycle, Unix descriptor
passing, or the two helper binaries for this profile. `os:cmd`, `System.cmd`,
external `open_port` spawn forms, and heart's external program are deliberately
unavailable. Erlang process spawning and supervision are unchanged.

File-only hostname behavior is intentionally small: immutable local host entries
can resolve and absent names return `nxdomain`; native NSS/DNS resolution is not
available. The metadata-only UDP probes remain a narrow host-contract cost and
must not be generalized into networking without a later gated decision.

All P018 runtime traces use Linux init and strace as evidence scaffolding. They
prove the artifact's behavior and absence of helper calls but do not prove the
future custom-kernel implementation. Gate 0 and M1 remain unauthorized.

## Verification

```sh
just build-otp-helperless
just inspect-otp-helperless
just test-target-helperless-linux
just test-target-release-helperless-linux
just check
```

The patch, source audit, clean-build comparison, native inventories, syscall
delta, negative-operation matrix, normalized traces, and ten-boot receipts are
stored under `docs/evidence/phase-0/RB-T-P018/`.
