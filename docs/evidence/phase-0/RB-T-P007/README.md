# RB-T-P007 evidence

The exact pinned OTP 29.0.5 / ERTS 17.0.5 / Elixir 1.20.4 pair generated a
genuine `runtime_lab` Mix release with `include_erts: false` and
`runtime_config_path: false`. Two fresh builds in distinct work directories
produced the same 362-entry Mix tree. Each was overlaid onto the complete P005
target release without replacing target OTP applications or native objects; the
paired trees and deterministic SquashFS images matched exactly. The paired
native closure contains exactly the 23 P005 AArch64-musl objects, including
`beam.smp` with SHA-256
`54ea7bc1953eb19908817ed243f63ddfabb7d8d9eefdb9d88f15ef4fe3577201`, and contains
no dynamic library, host ELF, or native object hidden in a Mix archive.

Ten fresh authoritative boots passed under QEMU 11.1.0 full-system AArch64 TCG
with `virt-11.1`, Cortex-A53, four vCPUs, 1 GiB RAM, and Alpine 3.22.5 Linux
6.12.94. No qemu-user translation was used. The release was mounted from
SquashFS read-only. Every boot loaded build-time `sys.config`, applied the
non-JIT `-S 2:2 -SDcpu 1:1 -SDio 1 -A 1` profile, started the normal OTP
application and supervision tree, exercised every reference workload and
supervised crash path, reported the exact runtime/artifact identity, and shut
the application and VM down cleanly.

The launcher manifest names `beam.smp` itself as the entrypoint and freezes the
root, boot script, code paths, empty config-provider list, VM flags,
environment, and complete argv. The generated Mix and OTP shell scripts remain
in the full tree and are inventoried, but none is invoked. Each normalized trace
begins with the manifest `beam.smp` argv; no `bin/runtime_lab`, `erl`,
`erlexec`, or shell launcher appears. Upstream ERTS then executes its unchanged
`erl_child_setup` and `inet_gethost` helpers, which are explicitly classified in
every receipt rather than misreported as launcher substitutions.

All 957 `openat` attempts per boot are retained with flags. Each boot recorded
935 release-tree reads and exactly one intentional write-capable release-tree
open, which failed with `EROFS`; there were no undeclared write attempts,
external network connections, or network listeners. The Linux init and strace
harness are evidence scaffolding only, not a substitute for the future custom
kernel process manifest.

The governing invariant is that independently generated Mix payloads can add
only architecture-neutral release content to the exact sealed target runtime,
then boot unchanged from an immutable tree through the direct `beam.smp`
contract. A plausible failure is an accidental host release that passes via its
generated shell script or host `erlexec` while silently substituting native ERTS
content or writing runtime configuration. The two-tree/two-image comparison,
complete inventories, native-closure equality, direct-exec traces, read-only
negative probe, exact runtime identity, and ten clean full-system boots
distinguish this result from that accidental demo.
