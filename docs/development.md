# Development bootstrap

Only Phase 0 evidence work is authorized. Do not add kernel implementation until
`RB-G-GATE0` has an approved human decision.

## Linux prerequisites

The bootstrap supports x86_64 and AArch64 Linux. Install these host packages by
the mechanism appropriate to the VM image:

- Bash
- `curl`
- Python 3.11 or newer
- `sha256sum`
- a C compiler and linker
- Git

From a fresh clone, one command installs the candidate Rust/`just` tools and
runs the complete check suite:

```sh
./scripts/bootstrap.sh
```

The script downloads a versioned `rustup-init`, verifies its architecture-
specific SHA-256 from `toolchain/bootstrap-tools.json`, installs the exact
`rust-toolchain.toml` channel, installs the recorded `just` release with its
published locked Cargo graph, and executes `just check`. It does not use `sudo`
or change shell startup files.

In a later shell, expose the installed tools with:

```sh
source "${CARGO_HOME:-$HOME/.cargo}/env"
```

## Visible commands

Run `just --list` to discover entry points. `just check` spells out each Cargo
and Python command in the `justfile`; `just` is an entry-point layer, not a
second build system. Commands owned by later tasks are fail-loud placeholders.
`xtask` will own artifact builds and image assembly as those tasks become ready.

The versions in `toolchain/bootstrap-tools.json` make this scaffold repeatable,
but remain **candidate bootstrap inputs**. `RB-T-P003` owns the complete host
and target toolchain selection, binary/source receipts, and sealed mirror.

## Build identity

Evidence build IDs use:

```text
rb1-<12 lowercase commit hex>-<clean|dirty>-<UTC YYYYMMDDTHHMMSSZ>
```

The full source revision and dirty state are separate required evidence fields.
A dirty build is valid for development evidence but cannot be presented as a
reproducible release or gate artifact.
