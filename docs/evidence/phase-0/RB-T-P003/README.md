# RB-T-P003 evidence

`bootstrap-transcript.txt` records the complete `just toolchain-bootstrap` run
from the dirty implementation worktree at commit
`a8272bc3f4975659d53bde1e83fca37fb586f9bc`. It verified all 19 non-OCI artifacts
in the content-addressed cache, pulled the builder by OCI index digest, created
two fresh Linux containers, built OTP 29.0.5 and Elixir 1.20.4 from source, and
ran the dependency-free Mix probe. Container networking was disabled for both
receipt observations and the runtime-pair build.

`linux-clean-a.json` and `linux-clean-b.json` embed the complete sealed source
lock and target contract, including immutable locators, versions, SHA-256
values, licenses, compiler/linker identities, target triples and flags, and OCI
index/child digests. `comparison.json` proves their normalized source-lock and
contract metadata match; builder IDs are deliberately observation-only. Both
containers ran on the available x86_64 Linux host. The contract separately pins
and documents the AArch64 Linux host path; this evidence does not claim an
AArch64-host execution or bit-identical output binaries.

`runtime-smoke.txt` is the full offline OTP/Elixir source-build transcript.
`runtime-smoke.json` records the exact passing identity
`otp=29.0.5 elixir=1.20.4`. `toolchain-report.txt` and `toolchain-verify.txt`
record the other task verification commands.

The governing invariant is that every accepted observation identifies the same
source-lock and contract digests, and each non-OCI artifact must exist at its
digest-derived cache path before compilation. A mutable locator, missing or
changed archive, changed contract, changed OCI digest, or mismatched runtime
identity fails before acceptance. The receipts distinguish this from an
accidental host demo by recording the pinned inputs and normalized comparison;
the runtime transcript distinguishes declared compatibility from a pair that
merely appears in metadata but does not compile and run.
