# Phase 0 toolchain report

Status: **p003-frozen-candidate**, contract revision 1, source-lock revision 1.

This report is generated from `toolchain/contract.json` and
`toolchain/sources.lock.json`. Gate 0 has not authorized kernel work.

## Selected runtime and compiler set

| Component | Version | Immutable source | License |
| --- | --- | --- | --- |
| Erlang/OTP | 29.0.5 | `sha256:86f6f40d4638852b0383235b02a70d8450184e441e83a06a108bf8e5bf1b2e04` | Apache-2.0 |
| Elixir | 1.20.4 | `sha256:6a2451e8655554edbbcec952f545ac2f8f25778b3883166c7cc724d6cf31d298` | Apache-2.0 |
| Rust/Cargo | 1.89.0 | `sha256:fbd1662e100e7b305908ece23b441cb7534eadfa6336c5f173ff08d1cec174a1` | MIT OR Apache-2.0 |
| LLVM/Clang/LLD | 20.1.8 | `sha256:6898f963c8e938981e6c4a302e83ec5beb4630147c7311183cf61069af16333d` | Apache-2.0 WITH LLVM-exception |
| musl | 1.2.5 | `sha256:a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4` | MIT |
| QEMU | 11.1.0 | `sha256:6ee1d1a61f68212476b27108c26da5f449dc09b626d42f8279ba0dc2e08fa858` | GPL-2.0-only (distribution aggregate; subcomponents vary) |
| Linux builder OCI image | python:3.13.7-bookworm | `sha256:c900d35aba5fe4c1dc1cd358408baae2902ff2a2926a1d15cc5002c6061ddb2e` | NOASSERTION (aggregate image; retain Debian package copyright metadata) |

Elixir 1.20.4 declares support for OTP 27–29. The sealed, network-disabled
smoke build exercises the selected OTP 29.0.5 pair from source.

## Target contract

- Kernel Rust: `aarch64-unknown-none`, CPU `cortex-a53`, Armv8-A with FP/AdvSIMD.
- Userspace Rust: `aarch64-unknown-linux-musl`, Armv8-A, static CRT.
- C/C++ compiler: LLVM/Clang 20.1.8; linker: LLD 20.1.8.
- Userspace C library: musl 1.2.5 for `aarch64-linux-musl`.
- C++ is admitted only for freestanding probes; no userspace C++ runtime is selected.
- Page size: 4096 bytes; endianness: little.

Kernel Rust flags: `-Ctarget-cpu=cortex-a53 -Cpanic=abort -Clinker=rust-lld`

Userspace C flags: `--target=aarch64-linux-musl -march=armv8-a -static -fuse-ld=lld`

## Builders

OCI index: `docker.io/library/python@sha256:c900d35aba5fe4c1dc1cd358408baae2902ff2a2926a1d15cc5002c6061ddb2e`

- x86_64 Linux child: `sha256:dff7bf7639ce459600e6e042228480eb9b6c627ce590e282c9b1d7c03fcad30b`
- AArch64 Linux child: `sha256:68331cab69c9b5e5ecd0d1d7f59bfcc5179bb790454169661a8beb4f436a45e6`

The same contract and source lock are consumed on both hosts. Host-native Rust,
LLVM, and Ninja archives differ by recorded digest; target triples and flags do not.
Two fresh, network-disabled Linux containers compare the architecture-independent
receipt contract byte-for-byte. This is metadata equivalence, not a binary
reproducibility claim.

## QEMU runner boundaries

### `linux-tcg-full-system`

Host: Linux x86_64 or AArch64. Claim: portable full-system correctness smoke.

```sh
qemu-system-aarch64 \
  -machine \
  virt-11.1,gic-version=3 \
  -cpu \
  cortex-a53 \
  -accel \
  tcg,thread=multi \
  -smp \
  4 \
  -m \
  1024 \
  -nodefaults \
  -no-reboot \
  -nographic \
  -serial \
  mon:stdio \
  -kernel \
  <kernel.elf>
```

### `linux-aarch64-kvm-full-system`

Host: native AArch64 Linux with KVM. Claim: native-architecture full-system lane; separately qualified from TCG.

```sh
qemu-system-aarch64 \
  -machine \
  virt-11.1,gic-version=3 \
  -cpu \
  host \
  -accel \
  kvm \
  -smp \
  4 \
  -m \
  1024 \
  -nodefaults \
  -no-reboot \
  -nographic \
  -serial \
  mon:stdio \
  -kernel \
  <kernel.elf>
```

### `linux-user-smoke`

Host: Linux with qemu-user. Claim: static AArch64-musl executable smoke only; never full-system evidence.

```sh
qemu-aarch64 \
  <static-aarch64-musl-binary>
```

### `macos-hvf-full-system`

Host: Apple Silicon macOS only. Claim: interactive accelerated compatibility lane; not metadata-equivalent to TCG.

```sh
qemu-system-aarch64 \
  -machine \
  virt-11.1,gic-version=3 \
  -cpu \
  host \
  -accel \
  hvf \
  -smp \
  4 \
  -m \
  1024 \
  -nodefaults \
  -no-reboot \
  -nographic \
  -serial \
  mon:stdio \
  -kernel \
  <kernel.elf>
```

QEMU 11.1.0 and `virt-11.1` are P003 candidate pins. RB-T-P014 owns the
final executable machine/CPU/GIC/HWCAP/DTB contract. HVF is available only
on macOS and accelerates AArch64 only on Apple Silicon; x86_64 Linux uses TCG.
qemu-user is never accepted as full-system, signal, thread, auxv, or startup proof.

## Complete source closure

| ID | Artifact | Hosts | SHA-256 | Provenance |
| --- | --- | --- | --- | --- |
| `elixir-source` | Elixir 1.20.4 (source) | all | `sha256:6a2451e8655554edbbcec952f545ac2f8f25778b3883166c7cc724d6cf31d298` | locally-computed-from-immutable-upstream-artifact |
| `just-source` | just 1.42.4 (crate-source) | all | `sha256:d26a2ff78b980d1de1078473e13dbd5fe72a1837a42e68d5c7327426f1254d34` | locally-computed-from-versioned-upstream-artifact |
| `llvm-aarch64` | LLVM/Clang/LLD 20.1.8 (aarch64-linux-binary) | aarch64-unknown-linux-gnu | `sha256:b855cc17d935fdd83da82206b7a7cfc680095efd1e9e8182c4a05e761958bef8` | official-github-release-asset-digest |
| `llvm-source` | LLVM/Clang/LLD 20.1.8 (source) | all | `sha256:6898f963c8e938981e6c4a302e83ec5beb4630147c7311183cf61069af16333d` | official-github-release-asset-digest |
| `llvm-x86_64` | LLVM/Clang/LLD 20.1.8 (x86_64-linux-binary) | x86_64-unknown-linux-gnu | `sha256:1ead36b3dfcb774b57be530df42bec70ab2d239fbce9889447c7a29a4ddc1ae6` | official-github-release-asset-digest |
| `meson-source` | Meson 1.9.0 (source) | all | `sha256:cd27277649b5ed50d19875031de516e270b22e890d9db65ed9af57d18ebc498d` | official-github-release-asset-digest-and-local-match |
| `musl-source` | musl 1.2.5 (source) | all | `sha256:a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4` | locally-computed-from-versioned-upstream-artifact |
| `ninja-aarch64` | Ninja 1.13.1 (aarch64-linux-binary) | aarch64-unknown-linux-gnu | `sha256:740f1b9f9d8ae68438240a6a2f3f7a27fc8b1946d2024a6a6b25857ee877987b` | official-github-release-asset-digest-and-local-match |
| `ninja-x86_64` | Ninja 1.13.1 (x86_64-linux-binary) | x86_64-unknown-linux-gnu | `sha256:0830252db77884957a1a4b87b05a1e2d9b5f658b8367f82999a941884cbe0238` | official-github-release-asset-digest-and-local-match |
| `otp-source` | Erlang/OTP 29.0.5 (source) | all | `sha256:86f6f40d4638852b0383235b02a70d8450184e441e83a06a108bf8e5bf1b2e04` | official-github-release-asset-digest |
| `python-builder-image` | Linux builder OCI image python:3.13.7-bookworm (multi-architecture-oci-index) | x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu | `sha256:c900d35aba5fe4c1dc1cd358408baae2902ff2a2926a1d15cc5002c6061ddb2e` | official-oci-registry-content-digest-and-local-match |
| `qemu-signature` | QEMU 11.1.0 (source-signature) | all | `sha256:fba624880262f196e4b4e38acf6bd28e47ba8fc2b0522e279a687565d11aae1f` | locally-computed-from-versioned-upstream-artifact |
| `qemu-source` | QEMU 11.1.0 (source) | all | `sha256:6ee1d1a61f68212476b27108c26da5f449dc09b626d42f8279ba0dc2e08fa858` | locally-computed-from-versioned-upstream-artifact |
| `rust-aarch64` | Rust/Cargo 1.89.0 (aarch64-linux-host) | aarch64-unknown-linux-gnu | `sha256:ae6f35b027cb32339fa4ac94dab37a21194e9a5c680491d01e54aa61e9da4de7` | official-rust-channel-manifest |
| `rust-channel-manifest` | Rust/Cargo 1.89.0 (channel-manifest) | all | `sha256:fbd1662e100e7b305908ece23b441cb7534eadfa6336c5f173ff08d1cec174a1` | official-sha256-sidecar-and-local-match |
| `rust-std-aarch64-musl` | Rust standard library 1.89.0 (aarch64-unknown-linux-musl) | all | `sha256:611633874e2000fd84807be65d82a6dfb7735c728969f5c8f62cad66702e6681` | official-rust-channel-manifest |
| `rust-std-aarch64-none` | Rust standard library 1.89.0 (aarch64-unknown-none) | all | `sha256:40a6eb6a55ebc5309dbc9c128134e1c209abf1b0a7e882cd014873fb062b94b5` | official-rust-channel-manifest |
| `rust-x86_64` | Rust/Cargo 1.89.0 (x86_64-linux-host) | x86_64-unknown-linux-gnu | `sha256:c4f2796b10ee886001f0799bc40caea38746403a33c379d77878c4f4683f9b51` | official-rust-channel-manifest |
| `rustup-aarch64` | rustup-init 1.28.2 (aarch64-linux-binary) | aarch64-unknown-linux-gnu | `sha256:e3853c5a252fca15252d07cb23a1bdd9377a8c6f3efa01531109281ae47f841c` | locally-computed-from-versioned-upstream-artifact |
| `rustup-x86_64` | rustup-init 1.28.2 (x86_64-linux-binary) | x86_64-unknown-linux-gnu | `sha256:20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c` | locally-computed-from-versioned-upstream-artifact |

## Residual risks

- RB-T-P014 must freeze the final QEMU machine, CPU, GIC, HWCAP, DTB, and TCG/HVF semantic delta after executable probes.
- The aarch64-unknown-none target enables FP/AdvSIMD and therefore creates a later kernel context-management obligation.
- The C++ selection is freestanding only; no userspace C++ standard library is admitted.
- Matching normalized metadata does not claim bit-reproducible compiler or target binaries.

## Reproduce

```sh
just toolchain-bootstrap
just toolchain-report
just toolchain-verify
```

`toolchain-bootstrap` is the only networked step. It mirrors every archive by
digest and pulls the OCI image by index digest. Runtime smoke and receipt
comparison then execute with container networking disabled. `toolchain-verify`
performs no network operation.
