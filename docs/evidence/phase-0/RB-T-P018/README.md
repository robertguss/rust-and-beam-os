# RB-T-P018 evidence

The P007 OTP 29.0.5 / ERTS 17.0.5 artifact required two native helper processes:
`erl_child_setup` was started unconditionally during VM startup and
`inet_gethost` was later executed for native hostname resolution. Correctly
supporting those helpers would require general process creation, address-space
snapshot, execution, descriptor passing, session, signal, and child-lifecycle
semantics that M2 explicitly excludes.

ADR 0002 therefore selects a sealed compile-time Unix OS-glue adapter rather
than adding bounded `fork`/`exec` emulation to the custom kernel. The complete
patch changes 11 non-generated lines in only
`erts/emulator/sys/unix/sys_drivers.c`, has SHA-256
`75961539bb6859da5bcdaefc260fb66377243faa97c7ba1bbe06d5d285ee16ad`, and is
enabled by `RB_ERTS_NO_FORKER=1`. It skips the forker-port startup, leaves
`erts_sys_unix_later_init()` unconditional, and rejects external spawn from
`spawn_start` with `ENOTSUP` before creating pipes or touching a forker port.
The two helper binaries are digest-recorded and omitted from the release.

## Reproducibility and artifact boundary

Two fresh builds produced byte-identical 21-object native closures and the same
static AArch64-musl `beam.smp`, SHA-256
`2236a94efdea84687c7139f4fa021c4381aa5d00969976bfc330049554711c22`. Compared
with P005/P007, the native closure removes exactly the two helper binaries. The
adapter changes no scheduler, GC, loader, BEAM instruction, Erlang process, or
code-loading source.

Two genuine Elixir 1.20.4 Mix releases produced equal 365-entry trees. Pairing
each with the helperless OTP closure produced equal complete trees and equal
deterministic SquashFS images. The immutable release configures
`{lookup, [file]}` and directly launches the exact `beam.smp`; neither an OTP
launcher nor a shell is used.

## Full-system results

Ten fresh direct-ERTS boots and ten fresh paired Mix-release boots passed under
full-system QEMU 11.1.0 AArch64 TCG with the pinned Alpine 3.22.5 Linux 6.12.94
kernel. Every direct boot passed the minimal, single-scheduler, final
two-scheduler, workload, fault/lifecycle, and clean-shutdown checks. Every Mix
boot passed exact OTP/ERTS/Elixir identity, application startup, supervision,
all reference workloads, a read-only release probe, `init:stop`, and SIGTERM.

Normalized direct traces have one stable 44-syscall set, down from the
baseline 53. They remove exactly `chdir`, `dup`, `dup3`, `kill`, `recvmsg`,
`sendmsg`, `setsid`, `socketpair`, and `wait4`, and add no syscall. Mix traces
contain 41 syscalls. Across all 20 boots there is no process-form clone, helper
`execve`, `setsid`, `wait4`, SCM_RIGHTS transfer, external connection, network
listener, or helper binary in the release.

The negative matrix bounds `os:cmd`, `System.cmd`, both external `Port.open`
spawn forms, `heart`, and a missing public hostname lookup. Spawn forms fail
honestly with `ENOTSUP`, heart returns `:ignore`, and the configured public
resolver returns `{:error, :nxdomain}` while the VM remains live. `localhost`
resolves from the immutable host file. Direct use of OTP's undocumented
`inet_gethost_native` backend is outside this configured policy and is recorded
as unsupported because upstream OTP deliberately halts if its required port
program cannot open.

The three direct-ERTS and one Mix-release `AF_INET` UDP port-zero binds per boot
perform only descriptor creation, wildcard bind, metadata query, and close.
There is no connect, listen, packet transfer, external endpoint, interface,
device, interrupt, or DMA path. ADR 0002 accepts only this metadata-only subset
under H2; P008 must express it at operation/path/error level.

## Interpretation

The governing invariant is that the exact helperless ERTS and genuine Mix
release retain normal VM and application behavior while requiring one native
process and no helper execution. The source assertion that
`erts_sys_unix_later_init()` remains active, installed signal handlers, and
clean SIGTERM behavior distinguish the selected adapter from accidentally
skipping all late Unix initialization. The explicit negative calls and syscall
audit prove absence rather than merely leaving helper paths unexercised.

Linux init and strace remain evidence scaffolding, not custom-kernel execution.
This result repairs the contradiction identified by the critical review and
unblocks P008; it does not authorize Gate 0 or M1. A required application that
needs native helper spawning/resolution, an adapter that exceeds its sealed
boundary, or a remaining requirement for process creation or network data must
trigger the documented Linux-hosted fallback.
