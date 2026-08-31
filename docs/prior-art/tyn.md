# Tyn prior-art audit (RB-T-P017)

## Scope, pin, and evidence labels

This audit reviews Tyn at commit
[`105c4946c756a6f3d23d1c41b9e8139352ddc115`](https://github.com/tyn-os/kernel/commit/105c4946c756a6f3d23d1c41b9e8139352ddc115)
(archive SHA-256
`1e07f608b43bb3455b3d1b32f05e67bef2ed7613fc66466b153d94a5a55f6782`). All Tyn
links below are immutable blobs at that commit.

Evidence is deliberately separated:

- **Inspected** means this audit read the pinned source or inspected the
  committed artifact locally.
- **Author report** means Tyn's author reports a run, rate, diagnosis, or
  external environment in the pinned documentation. It is useful evidence, but
  this project did not independently reproduce it.
- **Project observation** means an observation made in this repository/orb. In
  this audit that is limited to source/artifact inspection: `/dev/kvm` is absent
  and `qemu-system-x86_64` is absent, so no KVM, Nitro, or TCG boot was
  attempted or claimed. In particular, this is **not a KVM reproduction**.

Primary sources are the
[README](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/README.md),
[futex history](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/docs/FUTEX_HISTORY.md),
[technical report](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/docs/TECHNICAL_REPORT.md),
[capability map](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/docs/CAPABILITY_MAP.md),
and
[ERTS build record](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/docs/BUILDING_ERTS.md).

## Inspected system inventory

### Toolchains, ERTS, flags, and ELF

| Item                   | Inspected fact                                                                                                                                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OTP / ERTS             | OTP **27.3.4.2**, ERTS **15.2.7.1**                                                                                                                                                                                                               |
| Elixir                 | **1.18.3-otp-27**                                                                                                                                                                                                                                 |
| ERTS C/C++ environment | Alpine **3.19**, GCC **13.2**, musl **1.2.4**; `-O2`, C++17; fully static                                                                                                                                                                         |
| ERTS configure         | `--enable-jit --without-ssl --disable-dynamic-ssl-lib --without-wx --without-observer --without-debugger --without-et --without-megaco --without-odbc --without-jinterface`; optional `--enable-static-nifs=...`; linker `-static -Wl,-z,muldefs` |
| OTP patches            | Current reproducible build uses **unmodified OTP**, default `ETHR_SPIN_COUNT`, and default `ERTS_CHECK_MONOTONIC_TIME`; old spin-count and monotonic-time patches were removed                                                                    |
| Kernel Rust            | `nightly-2026-06-01`, with `rust-src`, `rustfmt`, `clippy`, LLVM tools                                                                                                                                                                            |
| Kernel target          | custom `x86_64-unknown-none-elf`, `rust-lld -Tlinker.ld`, aborting panics, red zone disabled, soft-float Rust ABI, non-PIE; MMX/AVX/AVX2 disabled                                                                                                 |

Sources:
[Dockerfile](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/beam-build/Dockerfile),
[tool versions](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/.tool-versions),
[Rust toolchain](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/rust-toolchain.toml),
and
[target JSON](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/x86_64-tyn.json).

**Project observation:** `file`/`readelf` on committed `src/beam.smp.elf` found
a stripped, statically linked, non-PIE ELF64 x86-64 `ET_EXEC`, System V ABI,
build-id `2517335af694b032f17eeb4865fe283c90368860`, entry `0x613307`, eight
program headers, no dynamic section/interpreter, four `PT_LOAD` segments (R at
`0x400000`, RX at `0x600000`, R at `0x1000000`, RW at `0x13d5ac8`), `PT_TLS`
(`filesz 0x28`, `memsz 0xa0`), non-executable RW stack, and RELRO. This is the
committed **SMP + BeamAsm JIT** emulator, not the project's non-JIT AArch64
candidate.

The
[loader](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/src/elf.rs)
validates only ELF64/x86-64/`ET_EXEC`, copies and zero-fills `PT_LOAD` segments
into fixed, identity-mapped addresses, and ignores `PT_TLS` as a loader object
(musl initializes TLS from the ELF/program-header startup data). It does not
implement dynamic linking or relocations.

### Boot and execution model

**Inspected:** GRUB Multiboot1 or QEMU `-kernel` enters the Rust kernel; a GRUB
cpio module, when present, is copied above the kernel and its low-memory staging
area is zeroed. Boot initializes a splittable 0–4 GiB identity map, IDT,
heap/DMA, PIT-calibrated TSC, RTC and optional kvmclock, ACPI/APIC and APs,
virtio-net or Nitro ENA, syscall entry, and an RDSEED/RDRAND-backed CSPRNG. It
then relocates the embedded static ERTS and cpio, loads the ELF, builds a
Linux-shaped `argc/argv/envp/auxv` stack, and enters the emulator. The cpio
application image is capped before the JIT mmap region. See
[`main.rs`](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/src/main.rs).

**Documentation skew:** README and some comments still say BEAM and kernel share
**ring 0**, and an older comment says the isolation shim is additive while BEAM
remains ring 0. Current executable source supersedes that prose: `jump_to_user`
uses DPL-3 selectors and `iretq`, cloned threads also return through a ring-3
`iretq`, and syscall/interrupt paths use `swapgs`. Likewise any stale “no-JIT”
prose is superseded by the committed JIT ELF, `--enable-jit`, and JIT
mmap/preemption code. This does **not** establish complete process isolation:
the map remains broadly identity-mapped and the tracked
[BUGS](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/BUGS.md)
describe absent/insufficient guard boundaries and silent corruption classes.

### Host profiles and drivers

**Inspected:** x86-64 q35/KVM uses virtio-net; AWS Nitro uses a from-scratch ENA
driver discovered through PCI port I/O. ACPI/APIC, PIT/TSC/RTC/kvmclock, COM1,
virtio DMA/networking, smoltcp IPv4, DHCP, pipes, timerfd/epoll, and a
serial/TCP eval shell are in scope. Tyn explicitly rejects TCG as a supported
profile because some images deterministically fault there. There is no renderer,
framebuffer/input architecture, AArch64 GIC/generic timer, or QEMU `virt`
platform support.

**Author reports:** stock Phoenix, LiveView, static assets, outbound networking,
basic distribution, and in-guest TLS were exercised on Nitro; current README
reports 20/20 public-AMI launches and about five seconds to HTTP. Historical
futex rates differ below and must not be silently replaced by that headline.
Throughput is intentionally withheld because early SLIRP figures were distorted.

Native components include normal statically built ERTS drivers plus Tyn's static
RustCrypto `:crypto` NIF and `tyn_tls` rustls NIF. Dynamic NIF loading is
unsupported; arbitrary user NIFs require static relinking, and
multiple-static-NIF linkage has had tooling/runtime duplication hazards.
`fork`/`exec` and general child processes are absent, so `System.cmd`, `os_mon`,
and native `inet_gethost` are unavailable/degraded; pure Erlang `[file,dns]`
lookup is selected instead.

### VFS and syscall personality

**Inspected:** the principal VFS is a read-only, relocated `newc` cpio with
bounded parsing, a 256-entry open-file table,
`open/read/pread/lseek/fstat/dup/close`, prefix-derived directories, and
`getdents64`; it is supplemented by volatile `/tmp` and `/dev/shm` tmpfs
(reported 4 MiB cap). There is no persistent filesystem. See
[`vfs.rs`](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/src/vfs.rs).

The
[syscall dispatcher](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/src/syscall.rs)
implements or emulates the ERTS-observed subset: file and directory
metadata/I/O, `brk`, fixed anonymous `mmap`/`munmap`, TLS `arch_prctl`, `clone`,
thread exit/TIDs, futex wait/wake/timeouts, affinity queries,
clocks/time/random, pipes/socketpair, epoll/poll/select/timerfd, vectored I/O,
sendfile, and IPv4 socket operations. Important approximations are contract
hazards, not Linux compatibility: `mprotect`/`madvise`, signal calls,
robust-list registration, `prctl`, affinity set, `tkill`/`tgkill`, and several
others are no-ops; `rseq`, `clone3`, and `memfd_create` return ENOSYS; `fork`
returns a fake PID; `sched_yield` is deliberately a no-op; `nanosleep` merely
yields; unknown futex commands log but return success; epoll has a fixed fake
fd/table and yield-polls; `getrusage` reports uptime as approximate CPU time.
The breadth of names therefore overstates the semantic depth.

### Threads, futexes, and signals

**Inspected:** musl `clone` is supported with FS-base TLS, parent/child TID
writes performed before the child becomes runnable, per-thread kernel/user
stacks, FPU/SSE save/restore, 100 Hz preemption, per-CPU queues, and thread
exit. The scheduler records child-TID pointers but the inspected exit path does
not provide this project's required complete `clear_child_tid`/join proof.
`set_robust_list` is a no-op. Signal registration/masks/alternate stack and
`tkill`/`tgkill` are no-ops; there is no Linux-compatible asynchronous delivery,
interruption/restart, frame, or `rt_sigreturn` semantics.

Futex WAIT checks the value and marks blocked under a hashed bucket lock held
through context switch; WAKE scans blocked threads and keeps address-keyed
pending wakes. Timeouts and a watchdog rescue exist. However, before the
readiness valve arms, WAIT returns after a scheduler yield rather than blocking.
This is intentionally not normal Linux futex behavior.

## Corrected futex/thread-progress history

The
[consolidated history](https://github.com/tyn-os/kernel/blob/105c4946c756a6f3d23d1c41b9e8139352ddc115/docs/FUTEX_HISTORY.md)
must be read chronologically because it retracts several confident intermediate
explanations. Everything in this section is an **author report**, except that
the final valve and 120-second fallback were independently confirmed in current
source.

The public commit chain preserves the important transitions: initial SMP and
atomic futex work
[`c6d0c977`](https://github.com/tyn-os/kernel/commit/c6d0c9773fd9da0917c9f30fd79e45c396499c72),
always-spurious WAIT
[`8dd36a9c`](https://github.com/tyn-os/kernel/commit/8dd36a9c4446a01881800eb78f988085813932e2),
the temporary ERTS yield patch
[`5e600428`](https://github.com/tyn-os/kernel/commit/5e6004283784436c86c4a28d8bb319302a510b83),
the first hybrid valve
[`1fe5d04a`](https://github.com/tyn-os/kernel/commit/1fe5d04a660208c640bcaef26983d1f544b25698),
restoration of unmodified OTP
[`5a6b8050`](https://github.com/tyn-os/kernel/commit/5a6b80505a92c1cd08982067d7e062391234bf32),
the combined TLS fix/valve-disable hygiene regression
[`a9c725d6`](https://github.com/tyn-os/kernel/commit/a9c725d623810f1de96d5c03d96d65dd103eb587),
protocol-safe watchdog and clone publication
[`9402fab6`](https://github.com/tyn-os/kernel/commit/9402fab6e0f1be28c2c9a68d03aeead54dbae544),
pinned ERTS plus the GCC-14 amplifier
[`6c145ffc`](https://github.com/tyn-os/kernel/commit/6c145fffc1703e0097c9edf608dca7cf7770ff53),
the conservative readiness valve
[`1cac02f1`](https://github.com/tyn-os/kernel/commit/1cac02f154532c477020e965ac1881526aa5d65b),
and the consolidated investigation
[`7a6e5e91`](https://github.com/tyn-os/kernel/commit/7a6e5e9184235970c045e6dfcc527041d3d1ae25).
The repository exposes no linked public GitHub issue for this investigation;
document references such as `#72`/`#92` are not treated as public issue
evidence.

1. Historical fixes addressed real independent defects: FS-base/TLS aliasing,
   XMM state loss, non-zeroed mmap memory, DF/RFLAGS corruption, clone
   publication order, watchdog mutation from interrupt context, timeout
   handling, JIT-page preemption classification, and VFS metadata.
2. With real blocking, a rare cold boot failed to reach `phoenix_listening`.
   Reported baselines were 31/32 on c5.metal KVM (both pre-crypto and crypto
   ERTS), 62/64 on Nitro plus 7/8 on another Nitro sweep, and earlier KVM/2-vCPU
   campaigns improving from 53/64 to 59/64 and JIT 60/64. Failed Nitro launches
   were watched for **120 seconds**, ruling out a mere slow five-second rescue.
3. Compiler/codegen changed incidence: pinned GCC 13.2/musl 1.2.4 gave 8/8 under
   TCG `-smp 1`, while GCC 14.2/musl 1.2.5 gave 2/8. Instrumentation itself
   later shifted rates radically; rates from TCG, oversubscribed KVM, and Nitro
   are not interchangeable.
4. Traces first appeared to show stale-rescue livelock: OFF_WAITER schedulers
   and contended mutexes were rescued repeatedly and ran, then re-waited.
   Pending-wake instrumentation showed no wake was issued for most final waits,
   exonerating pending-wake loss.
5. An ERTS probe then suggested a stale POLL-vs-TSE wake-channel choice.
   **Retracted:** correlation used an inferred `event - 0x70` address. A live
   structure walk proved the actual futex was `event + 0x10`; the apparent
   mismatch was two coincident interleaved arrays. Correctly mapped sleepers all
   advertised TSE and had no work/poke.
6. Permanent spin-yield eliminated the OFF_WAITER fingerprint (reported 0/32),
   initially labelled a thread-progress **registration** deadlock.
   **Retracted:** a live `intrnl` read found `managed_count == managed.no`;
   registration had completed. The later source-derived registration barrier
   story in the same history is explicitly superseded by that live refutation.
   What remains supported is narrower: real blocking during a later init wait
   admits a collective work/progress quiescence; the exact lock-owner/dependency
   edge is still unpinned.
7. Open-count, registration-complete, and first-listen triggers all armed too
   early and restored the stall. Permanent spin-yield burns CPU and increases
   unrelated TCG faults, so it was diagnostic, not a fix.
8. Current source ships a conservative workaround: `FUTEX_BLOCKING=false` means
   futex WAIT spin-yields throughout ERTS/application initialization; a stdout
   byte match for exactly **`serial_shell ready`**, emitted after application
   configuration/start, flips to real blocking. If the marker never arrives, the
   watchdog flips after **120 seconds from the first spin-yield**. Reported
   GCC-14/TCG `-smp 1` validation was 30 PASS, 0 futex stalls, 2 unrelated
   outcomes in one instrumented N=32, then 22 PASS, 0 futex stalls, 10 TCG
   faults/other outcomes in stripped N=32. The author explicitly withholds a
   real-hardware reliability claim pending c5.metal/Nitro A/B.

Explicitly ruled out or materially exonerated mechanisms include wrong-address
bucket collisions, wrong-thread or multi-shot pending wakes, handoff/pending
ordering, value-change consumption, CFS policy, an `ethr_event_set` patch,
wake-implies-yield, timer-trampoline red-zone corruption as the boot stall,
non-monotonic time, cpio corruption, omitted caller-saved GPRs, custom
spin-count/time patches, lost IPI/AP timer as root cause (the amplifier
reproduces on one CPU), permanent idle check/sleep loss (periodic timer bounds
it and source fixed the window), epoll missing a wake while parked (it
yield-polls), futex check/block non-atomicity, pending-wake leakage, POLL/TSE
channel mismatch, and the registration barrier. More memory and larger stacks
were also rejected as fixes. The exact post-registration dependency remains
unresolved and probe-sensitive.

**Normative project rule:** Tyn's valve is warning evidence, not a pattern. This
project must **not accept spin, yield, watchdog rescue, boot/readiness strings,
open counts, elapsed-time switches, or spurious-success returns as normal wait
semantics**. Such a change is only a bounded diagnostic or an explicitly
approved central-hypothesis failure; it must never enter `beam-host.yaml`
silently. Normal semantics remain value-checked atomic sleep, wake, timeout,
signal interruption/restart, and thread-exit/join behavior, tested by
`just test-thread-progress-probe` and [RB-T-P207](../plan/tasks/rb-t-p207.md).

## Architecture comparison and claim boundary

| Dimension         | Tyn at the pin                                                                                  | This project                                                                                                                                                |
| ----------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ISA/platform      | x86-64 q35, ACPI/APIC, TSC, port I/O; KVM/Nitro                                                 | AArch64 QEMU `virt`, FDT/GIC/generic timer                                                                                                                  |
| Acceleration      | KVM/Nitro normative; TCG explicitly unsupported                                                 | Linux TCG required semantic lane; native AArch64 KVM when available; Apple Silicon HVF interactive lane ([RB-T-P016](../plan/tasks/rb-t-p016.md))           |
| Runtime           | OTP 27.3.4.2, static musl, SMP, BeamAsm JIT                                                     | pinned current project runtime, static AArch64 musl, **non-JIT**, two normal schedulers/four vCPUs                                                          |
| Isolation         | current source enters ring 3, but broad identity map/guard defects and stale ring-0 docs remain | separate EL0 address spaces, validated user pointers, W^X, kernel at EL1                                                                                    |
| Application shape | one ERTS application/unikernel; networking central                                              | isolated ERTS process plus isolated Rust renderer; bounded typed IPC; kernel owns devices                                                                   |
| Threads/atomics   | x86 TSO, FS base, APIC queues; bespoke futex/watchdog                                           | AArch64 weak ordering and LSE/LL-SC contract must be proved by [RB-T-P200](../plan/tasks/rb-t-p200.md); TLS/auxv by [RB-T-P202](../plan/tasks/rb-t-p202.md) |
| Signals           | mostly no-op stubs; no complete signal model                                                    | real masks, actions, frames, synchronous faults, interruption/restart and return are required host semantics                                                |
| Files/native code | cpio + tiny tmpfs; JIT and static NIFs; no dynamic loading                                      | read-only declared image, no writable/persistent FS in the ERTS slice, non-JIT, no arbitrary NIFs/drivers                                                   |
| UI                | none                                                                                            | kernel-owned virtio GPU/input capabilities and separate renderer with native heartbeat                                                                      |

Tyn therefore supports one important feasibility proposition: a small Rust
kernel can load an upstream, static-musl ERTS and support a substantial
OTP/Elixir workload without reimplementing the VM. It also shows that
syscall-name coverage and one successful boot are inadequate evidence.

It proves **none** of this project's AArch64 exception/TLS/atomics correctness,
weak-memory futex ordering, GIC/timer behavior, QEMU `virt` device model, EL0
address-space isolation, non-JIT runtime closure, signal frames, two-process
renderer fault boundary, Linux/TCG validity, or macOS/HVF correctness. x86
KVM/Nitro success cannot transfer across ISA or accelerator; Tyn's own TCG
failures make such transfer especially indefensible. HVF is not exercised by Tyn
at all.

## Limitation dispositions

Every relevant limitation is assigned exactly one named disposition category.

| Finding                                                                              | Category                    | Project disposition                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Init futex valve, rare progress stall, compiler/instrumentation-sensitive rates      | **new contract/test**       | `just test-thread-progress-probe` must inject lost wake, premature blocking, stalled startup, timeout/signal races, and exit/join failures; full ERTS stress remains [RB-T-P309](../plan/tasks/rb-t-p309.md). No valve workaround is acceptable. |
| Incomplete `clear_child_tid`, robust cleanup, thread exit/join evidence              | **new contract/test**       | Freeze semantics in [RB-T-P008](../plan/tasks/rb-t-p008.md) and exercise them in `just test-thread-progress-probe`; implementation belongs to the M2 thread/futex tasks including [RB-T-P207](../plan/tasks/rb-t-p207.md).                       |
| No-op signal API and absent delivery/frame/restart semantics                         | **already covered**         | Signals are first-class in the architecture and M2/M3 qualifications; Tyn's stubs cannot satisfy the host contract.                                                                                                                              |
| x86 TSO, FS base, APIC/TSC/port-I/O assumptions                                      | **architecture difference** | AArch64 atomics/order are owned by [RB-T-P200](../plan/tasks/rb-t-p200.md); machine/CPU/auxv/HWCAP differences by [RB-T-P014](../plan/tasks/rb-t-p014.md).                                                                                       |
| KVM/Nitro normative profile; TCG faults and MTTCG unfaithfulness                     | **architecture difference** | Separate, non-interchangeable TCG/KVM/HVF profiles and capacity/preflight are owned by [RB-T-P016](../plan/tasks/rb-t-p016.md). A failure on one is retained, not erased by another.                                                             |
| No local `/dev/kvm` or x86 QEMU; Nitro artifacts/runners unavailable                 | **not reproducible**        | This audit claims no boot reproduction. Historical launch/rate/network/TLS claims remain author reports. Provision an appropriate runner rather than substituting this orb.                                                                      |
| Broad identity mapping, guard-page/wild-pointer faults, historical ring-0 claim      | **already covered**         | This project requires isolated EL0 address spaces, user-copy validation, W^X, and fault containment; startup/EL0 work is tracked from [RB-T-P202](../plan/tasks/rb-t-p202.md) onward.                                                            |
| TCG `#PF/#GP/#UD`, memory-size-sensitive boot faults, identity-map ceiling           | **new contract/test**       | Preserve first-failure artifacts and vary RAM/layout in [RB-T-P014](../plan/tasks/rb-t-p014.md) and the M1/M3 campaigns; never relabel as “slow TCG.”                                                                                            |
| JIT preemption, executable mmap, static-NIF complexities                             | **architecture difference** | JIT and arbitrary NIFs/drivers are out of this POC. Non-JIT closure is frozen by [RB-T-P008](../plan/tasks/rb-t-p008.md); later JIT is a separate gate.                                                                                          |
| Read-only cpio, volatile 4 MiB tmpfs, no persistence, tmpfs large-write fault        | **architecture difference** | Persistent/writable storage is out of scope; image access remains declared/read-only. Tyn's tmpfs implementation is not imported.                                                                                                                |
| IPv4 only, ENA/virtio-net, DNS/static-host and distribution limitations              | **architecture difference** | Networking/distribution are outside the current POC; they neither validate nor block renderer IPC.                                                                                                                                               |
| No fork/exec, `System.cmd`, `os_mon`, native resolver                                | **already covered**         | Fork/exec and subprocesses are forbidden contract expansion; release closure must avoid them under [RB-T-P008](../plan/tasks/rb-t-p008.md).                                                                                                      |
| Approximate `getrusage` and broad syscall no-ops/fakes                               | **new contract/test**       | Every admitted syscall needs trace-backed semantics in [RB-T-P008](../plan/tasks/rb-t-p008.md); unsupported calls fail honestly. Success stubs are prohibited unless their exact behavior is the frozen contract.                                |
| Dynamic NIF loading absent; crypto/TLS custom, partial/unreviewed; TLS 1.2/mTLS gaps | **accepted residual risk**  | Crypto/TLS and arbitrary NIFs are out of POC scope. The final claim must say so; Tyn's implementation is not security evidence for this project.                                                                                                 |
| RDRAND/RDSEED-only entropy and boot panic without it                                 | **architecture difference** | AArch64 entropy source and advertised capabilities require their own contract; x86 RNG availability does not transfer.                                                                                                                           |
| Reported Phoenix, distribution, Nitro ENA, TLS, wall-clock and throughput behavior   | **not reproducible**        | Retain as author report only. Capability reports are not imported into this project's acceptance evidence.                                                                                                                                       |
| Mutable Alpine tag and downloaded OTP source in the documented “reproducible” recipe | **new contract/test**       | Tyn's source recipe was inspected, but its inputs are not sealed like [RB-T-P003](../plan/tasks/rb-t-p003.md). Do not claim its committed ERTS is byte-reproduced until immutable OCI/source receipts independently establish that provenance.   |
| Stale packaged beams/config and hand-patched-artifact history                        | **already covered**         | Pinned build receipts and release closure are required by [RB-T-P003](../plan/tasks/rb-t-p003.md), [RB-T-P008](../plan/tasks/rb-t-p008.md), and final evidence indexing in [RB-T-P013](../plan/tasks/rb-t-p013.md).                              |
| No renderer/device-capability/failure-boundary evidence                              | **architecture difference** | Tyn cannot evidence this project's two-process renderer, heartbeat, GPU/input ownership, or BEAM-loss behavior.                                                                                                                                  |

## Audit conclusion

Tyn is the closest public feasibility evidence and a stronger warning than a
template. Its pinned source demonstrates substantial upstream ERTS integration,
but also contains semantic stubs, a readiness-marker futex valve, unresolved
root mechanism, profile-dependent failures, and stale architecture prose. This
project should reuse the lessons—pinned artifacts, exact semantic tests,
first-failure retention, profile separation, and corrected/retracted
explanations—not the workarounds. Gate evidence must continue to treat
SMP/thread progress as a central kill criterion, not an ordinary boot
integration bug.
