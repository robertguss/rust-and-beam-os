# Dependency and sealed-source policy

## Candidate phase

Source-lock revision 1 and toolchain-contract revision 1 are the P003 frozen
candidate. New dependencies require a narrow role, license disposition, feature
list, source identity, unsafe-code review, and an owning task. Cargo commands
use `--locked`; every non-Cargo toolchain input uses the source lock.

## Source lock states

`toolchain/sources.lock.json` is the machine-readable source closure.

- `unsealed`: probes may retrieve declared candidate sources; results cannot
  claim offline reproducibility or Gate-0-frozen closure.
- `sealed`: every input has an immutable locator, local SHA-256, license, and
  content-addressed mirror path. Retrieval is a separate explicit command;
  builds run with network access disabled and fail on any source absent from the
  lock.

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

The small repository bootstrap remains separate from the target build
environment, but its `rustup-init` and `just` inputs are now also present in
source-lock revision 1. Rust components are pinned by the dated official channel
manifest and exact component digests. The OCI builder is selected by index
digest with x86_64 and AArch64 child manifests recorded in the contract.
