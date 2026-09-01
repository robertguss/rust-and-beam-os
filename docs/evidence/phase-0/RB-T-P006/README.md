# RB-T-P006 evidence

The exact static non-JIT AArch64-musl OTP 29.0.5 / ERTS 17.0.5 artifact ran
inside a purpose-built initramfs in a full-system AArch64 Linux VM. The
authoritative lane uses pinned QEMU 11.1.0 TCG with the `virt-11.1` machine,
Cortex-A53 CPU, four vCPUs, 1 GiB RAM, an Alpine 3.22.5 Linux 6.12.94 kernel,
and no qemu-user translation. The one-command runner first evaluates the minimal
Erlang probe, then runs both a single-scheduler profile and the final
two-scheduler profile.

Ten fresh acceptance boots passed. Every candidate run had 10 native threads and
exercised processes/messages, timers, a 256 KiB binary, ETS, and forced GC with
`+S 2:2 +SDcpu 1:1 +SDio 1 +A 1`. The ELF has no dynamic interpreter, the
application has no NIF, mappings contain no shared objects, and every boot shut
down cleanly. All runs observed the same 53-syscall set, and every syscall maps
to `abi/beam-host.yaml` revision 0. No external connection, network service
listener, or network device appeared. The three port-zero UDP binds performed by
ERTS bootstrap are explicitly recorded rather than hidden.

Each boot receipt retains the QEMU argv and binary/kernel/initramfs hashes;
AArch64 auxv/HWCAP, page and cache-line sizes; TLS offsets and thread pointers;
signal-frame and alternate-stack facts; thread topology and masks; descriptors;
memory; mappings; all opened paths and their required/removable/forbidden
classification; syscall/signal summaries; workload results; and shutdown status.
The compressed normalized trace and serial log for all ten boots are retained
beside the receipts; normalized mapping facts are embedded in each receipt.
`boot-matrix.json` provides a compact hash and invariant index over those
artifacts.

The governing invariant is that the same sealed static artifact must make
forward scheduler and workload progress under native AArch64 Linux semantics
without acquiring an undeclared runtime dependency. A plausible failure is a
qemu-user-only result that passes basic evaluation while masking TLS, signal
frame, auxv, futex-interruption, or thread-exit behavior. Full-system execution,
the deliberate fault/lifecycle probe, two scheduler profiles, per-boot topology
and trace capture, contract comparison, and ten independent clean shutdowns
distinguish this result from that accidental demo.
