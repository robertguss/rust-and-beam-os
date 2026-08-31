---
schema: "repo-plan/v1"
id: "RB-M-M2"
title: "Musl & BEAM Host Contract"
type: "milestone"
order: 2
authorized_by: "RB-G-GATE1"
x_legacy_id: "M2"
---
## Outcome

Implement the exact Linux-shaped userspace contract needed by static musl and the pinned ERTS workload without turning the OS into general Linux.

## Scope

* Static-musl process startup, auxv, arguments, environment, TLS, and errno.
* Read-only VFS and admitted file/path/metadata operations.
* Anonymous virtual memory, `brk`, `mmap`, `mprotect`, and `munmap`.
* Native threads, `clone`, TLS, child-TID semantics, joins, and exits.
* Futex, signal, pipe, nonblocking descriptor, polling, time, randomness, and SMP semantics.
* Executable `beam-host.yaml` contract and focused C conformance programs.
* Unknown-syscall rejection and structured tracing.

## Exit criteria

* Every admitted contract entry has positive, negative, error, and concurrency evidence where applicable.
* The complete musl conformance subset passes for one hour under contention on four vCPUs.
* No unknown syscall is observed.
* Race-sensitive tests pass across deterministic randomized preemption seeds.
* RB-G-GATE2 confirms that the contract is bounded, understandable, and not recreating broad Linux behavior.

## Implementation-readiness status — 2026-08-30

**Gate-blocked; not authorized.** The exact pinned musl/ERTS source and traces are the oracle. Atomics/SMP/shootdowns, thread start/exit/join, signals, stream/open-file-description/poll lifecycle, monotonic/realtime time, and production entropy are coupled bounded protocols implemented through their direct child issues. Robust-list scope is conditional on the frozen contract.
