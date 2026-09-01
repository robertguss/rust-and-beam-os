# RB-T-P005 evidence

The primary and rebuild receipts record two fresh extractions of the pinned OTP
29.0.5 source archive, each built with the official `otp_build configure`,
`boot`, and `release` flow. Both lanes use the sealed LLVM 20.1.8 and musl 1.2.5
sysroot, the same stable work path, and no source patches. The compressed build
logs, generated ERTS target configuration, cross answers, application skip list,
and linker map retain the build details without committing the multi-gigabyte
working trees.

`inspection-receipt.json` and `native-closure.json` cover all 23 native objects
in the installed release, not only `beam.smp`. They show a static AArch64
`ET_EXEC` runtime with no `PT_INTERP`, `PT_DYNAMIC`, `DT_NEEDED`, runtime
relocation sections, shared libraries, executable stack, or `PT_TLS`. All load
segments have 4 KiB alignment and end below 2 GiB. The instruction scanner
checked 723,833 instructions and found no LSE, PAC, or BTI instructions under
the Armv8-A baseline. `beam-headers.txt`, `beam-relocations.txt`, and the
compressed symbol and link-map reports retain independently inspectable detail.

The installed application closure is exactly `compiler`, `erl_interface`,
`erts`, `kernel`, `sasl`, and `stdlib`. The generated driver table inventories
the `inet` and `ram_file` drivers plus the eight core ERTS NIF modules. There
are no statically linked application NIFs or drivers. The string-table runtime
load inventory is deliberately not presented as execution evidence; it records
potential loader and port paths for the target-runtime task to exercise.

`rebuild-comparison.json` proves the governing reproducibility invariant: every
native object has the same relative path, kind, size, and SHA-256 digest in a
second clean lane. Both lanes produced the exact 4,441,424-byte `beam.smp`
digest
`sha256:54ea7bc1953eb19908817ed243f63ddfabb7d8d9eefdb9d88f15ef4fe3577201`. A
plausible failure is an absolute build path, generated timestamp, undeclared
native object, or compiler feature change altering one output; the complete
closure comparison fails on any such path, size, kind, or digest drift.

This is **host** artifact evidence. It proves the upstream cross-build and the
sealed release shape, but it does not prove that ERTS executes correctly on the
custom kernel. RB-T-P006 owns target loading and execution, including the musl
thread-pointer requirement even though these ELFs contain no `PT_TLS` segment.
