# RB-T-P004 evidence

This evidence combines two deliberately different views of the host contract.
The x86_64 host lane runs the exact dependency-free `runtime_lab` application on
pinned OTP 29.0.5 / ERTS 17.0.5 / Elixir 1.20.4, with the candidate's bounded
two-scheduler topology. It captures boot, process/descriptor snapshots, the full
seed `20260901` stress and supervised-crash workload, and controlled SIGTERM
shutdown. Two fresh replays produced the same normalized syscall, flag, error,
signal, path, and family sets. Both compressed raw `strace -ff` streams and both
normalized interaction sets are retained here; `raw-trace-manifest.json` records
their hashes, sizes, runtime identity, seed, and VM flags. The repeatable runner
regenerates the same structure under `target/beam-host-reference`.

The target lane runs the exact static non-JIT AArch64-musl ERTS artifact under
full-system QEMU/Linux. Ten fresh boots compare every observed syscall with
`abi/beam-host.yaml` revision 0. A static probe built by the same sealed
AArch64-musl cross toolchain deliberately exercises allocation rejection, an
`EFAULT` copy, poll timeout, pthread cancellation, alternate-stack signal
delivery, `EBADF` close, thread start, thread exit/join, and normal shutdown.
This keeps host-glibc-only calls from being mistaken for target requirements.

Revision 0 classifies 53 interactions as required, 17 as optional or disabled,
and 21 as host build-time only. Its 18-item source inventory checks symbols in
the sealed OTP and musl archives and maps every item to a classified interaction
or a build-profile exclusion. There are no unexplained interactions. The
contract remains architecture-provisional and explicitly retains three Gate 0
risks: ERTS helper process creation, three port-zero UDP binds despite no
network traffic or device, and source-visible `madvise`/robust-mutex paths
absent from the bounded target workload.

The governing invariant is that the custom kernel may implement only
interactions attributed to the frozen target closure, with each required
operation preserving Linux's blocking, error, signal, memory, and
thread-lifecycle semantics. A plausible failure is an implementation that
returns successful stubs or wakes a futex waiter without atomically checking the
value; the demo could boot once but deadlock, corrupt a join, or hide `EFAULT`
on another interleaving. The saved source coverage, explicit negative paths,
equal host replays, target signal/TLS probe, and ten independent target boots
distinguish semantic progress from a single accidental boot.
