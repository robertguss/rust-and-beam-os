# Dependency and sealed-source policy

## Candidate phase

Until `RB-T-P003` freezes the complete toolchain, every version is a candidate.
Candidate downloads must still use immutable versions where available and verify
publisher checksums or ecosystem lockfile checksums. Cargo commands use
`--locked` once a lockfile exists. New dependencies require a narrow role,
license disposition, feature list, source identity, unsafe-code review, and an
owning task.

## Source lock states

`toolchain/sources.lock.json` is the machine-readable source closure.

- `unsealed`: probes may retrieve declared candidate sources; results cannot
  claim offline reproducibility or Gate-0-frozen closure.
- `sealed`: every input has an immutable locator, local SHA-256, license, and
  repository-relative mirror path. Builds run with network access disabled and
  fail on any source absent from the lock.

Changing a sealed entry creates a new source-lock revision and invalidates all
evidence that consumed the old revision. A build must never silently fall back
from a mirror to the network.

## Checksums and mirrors

SHA-256 covers downloaded bytes and mirrored artifacts. Ecosystem lockfiles are
committed, but their checksums do not replace the source-lock digest for Gate 0.
Mirror paths live under an external content-addressed store or a future declared
repository path; large source archives are not committed ad hoc. The source lock
records the original locator, immutable reference, digest, mirror path, license,
and consumers.

The bootstrap exception is explicit: pinned `rustup-init` binaries are verified
against checked-in SHA-256 values; Rust components are verified by rustup; the
candidate `just` crate is installed from its published locked Cargo graph. This
is repeatable scaffolding, not the sealed P003 build environment.
