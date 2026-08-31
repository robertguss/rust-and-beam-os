# ADR 0001: Freeze the Phase 0 host and target toolchain candidate

- Status: accepted
- Date: 2026-08-31
- Owners: robertguss
- Plan task: RB-T-P003
- Evidence: docs/evidence/phase-0/RB-T-P003/evidence.json

## Context

Every later ERTS, musl, ELF, and QEMU observation is meaningful only if it uses
one identifiable toolchain. Moving release channels, container tags, QEMU's
unversioned `virt` alias, and host package resolution could otherwise produce
two successful but semantically different experiments.

P003 selects build inputs. It does not authorize kernel work and does not take
ownership of the final QEMU platform contract from RB-T-P014.

## Decision

Freeze source-lock revision 1 and toolchain-contract revision 1:

- OTP 29.0.5 with Elixir 1.20.4, built from source and exercised by the
  dependency-free `beam/toolchain_smoke` Mix project;
- Rust/Cargo 1.89.0 with `aarch64-unknown-none` and `aarch64-unknown-linux-musl`
  standard-library artifacts;
- LLVM/Clang/LLD 20.1.8 for AArch64 freestanding C/C++ and static-musl C;
- musl 1.2.5;
- QEMU 11.1.0 with the `virt-11.1` candidate machine and separate TCG, native
  AArch64 KVM, qemu-user, and Apple Silicon HVF command profiles;
- Ninja 1.13.1, Meson 1.9.0, and a Python 3.13.7/Bookworm OCI builder pinned by
  multi-architecture index and per-platform child digests.

The architecture floor is little-endian Armv8-A. Kernel Rust and freestanding
C/C++ use Cortex-A53 as the semantic CPU baseline. C++ has no admitted userspace
runtime. Full-system QEMU and qemu-user claims remain categorically separate.

## Governing invariant

Every accepted Phase 0 build or trace identifies the exact source-lock and
toolchain-contract digests. A declared input is either present at its
content-addressed mirror path and matches its SHA-256, or the build fails before
compilation. No command resolves `latest`, a moving branch, or bare QEMU `virt`.

## Alternatives considered

- OTP 28 or Elixir 1.19: compatible fallbacks, but unnecessary after the exact
  OTP 29.0.5/Elixir 1.20.4 pair built and ran successfully.
- Host distribution packages: rejected as the target compiler/runtime source
  because repository snapshots and package selection would remain implicit.
- GNU cross compiler as a second target stack: deferred because Clang/LLD covers
  the admitted C/C++ surfaces with fewer independently versioned inputs.
- A C++ userspace standard library: rejected until a downstream workload proves
  it is required.
- Bare `virt`, `-cpu max`, or treating qemu-user as target proof: rejected
  because each weakens the future platform and kernel contracts.

## Consequences and residual risks

The two Linux host architectures consume different native Rust, LLVM, Ninja, and
OCI child artifacts but compare one normalized target contract. Metadata
equivalence does not claim bit-reproducible output binaries.

The Rust bare-metal target enables FP/AdvSIMD, creating an explicit later
context-management obligation. RB-T-P014 must still probe and freeze machine,
CPU, GIC, HWCAP, DTB, and TCG/HVF differences. Apple Silicon/HVF execution is
documented here but requires its designated Mac evidence in downstream tasks.

## Verification

```sh
just toolchain-bootstrap
just toolchain-report
just toolchain-verify
just check
```

The bootstrap performs the only networked retrieval, then runs two fresh builder
receipts and the OTP/Elixir smoke build with container networking disabled.
Durable transcripts and normalized receipts live under
`docs/evidence/phase-0/RB-T-P003/`.
