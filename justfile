set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available entry points and the commands they execute.
default:
    @just --list

# Install the candidate bootstrap tools and run `just check`.
bootstrap:
    ./scripts/bootstrap.sh

# Run every repository check without hiding the underlying commands.
check:
    cargo fmt --all --check
    cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
    cargo test --locked --workspace
    python3 -m unittest discover -s tests -v
    python3 scripts/repo_plan.py check --root docs/plan
    python3 scripts/evidence.py check --root .
    python3 scripts/plan_labels.py check --root docs/plan

# Validate canonical plan records and generated projections.
plan-check:
    python3 scripts/repo_plan.py check --root docs/plan

# Print the gate-aware label projection suitable for a future tracker sync.
plan-labels:
    python3 scripts/plan_labels.py project --root docs/plan

# Validate evidence records, indexes, source claims, and their SHA-256 links.
evidence-check *args:
    python3 scripts/evidence.py check --root . {{args}}

# Print SHA-256 values for evidence inputs or artifacts.
evidence-hash *paths:
    python3 scripts/evidence.py hash --root . {{paths}}

# Mirror the sealed source lock, compare two clean builders, and prove OTP/Elixir.
toolchain-bootstrap:
    ./scripts/toolchain-bootstrap.sh

# Print the generated human-readable frozen-candidate toolchain report.
toolchain-report:
    python3 scripts/toolchain.py report

# Verify the offline source cache and clean-builder receipts from bootstrap.
toolchain-verify:
    python3 scripts/toolchain.py verify --require-cache \
      --receipt target/toolchain-receipts/linux-clean-a.json \
      --receipt target/toolchain-receipts/linux-clean-b.json

# Print the portable Linux full-system TCG candidate command.
qemu-tcg-command:
    python3 scripts/toolchain.py runner linux-tcg-full-system

# Print the native AArch64 Linux/KVM full-system candidate command.
qemu-kvm-command:
    python3 scripts/toolchain.py runner linux-aarch64-kvm-full-system

# Print the qemu-user smoke command, which is never full-system evidence.
qemu-user-smoke-command:
    python3 scripts/toolchain.py runner linux-user-smoke

# Print the Apple Silicon macOS/HVF full-system candidate command.
qemu-hvf-command:
    python3 scripts/toolchain.py runner macos-hvf-full-system

# Validate the pinned Tyn source audit and claim classifications.
prior-art-tyn-audit:
    python3 scripts/prior_art.py audit --root .

# Fetch, verify, inspect, and build pinned Tyn; boot only on an x86_64 KVM host.
prior-art-tyn-reproduce:
    python3 scripts/prior_art.py reproduce --root .

# Exercise thread/futex/signal/clear-child-TID progress and injected failures.
test-thread-progress-probe:
    python3 scripts/thread_progress.py check --root .

# Boot the bare-metal virtio display/input probe once under pinned QEMU TCG.
run-virtio-probe-tcg:
    python3 scripts/virtio_probe.py run --boots 1 --output target/virtio-probe/run

# Run host contract tests and ten independent QEMU TCG acceptance boots.
test-virtio-probe-tcg:
    python3 -m unittest tests.test_virtio_probe -v
    cargo fmt --manifest-path tests/virtio-probe/Cargo.toml --all --check
    cargo clippy --manifest-path tests/virtio-probe/Cargo.toml --release --locked --offline -- -D warnings
    python3 scripts/virtio_probe.py run --boots 10 --output target/virtio-probe/acceptance

# Boot the exact static target ERTS once in the sealed full-system AArch64 Linux VM.
run-target-erts-linux:
    python3 scripts/erts_linux.py run --boots 1 --output target/erts-linux-reference/run

# Run host contract tests and ten fresh full-system AArch64 Linux TCG boots.
test-target-erts-linux:
    python3 -m unittest tests.test_erts_linux -v
    python3 scripts/erts_linux.py run --boots 10 --output target/erts-linux-reference/acceptance

# Trace two host runtime_lab replays plus the error-path probe and compare them.
trace-reference-runtime:
    python3 scripts/beam_host.py trace

# Validate beam-host revision 0 against source and all available traces.
beam-host-validate:
    python3 -m unittest tests.test_beam_host -v
    python3 scripts/beam_host.py validate

# Prove every relevant Tyn limitation has one owned project disposition.
prior-art-coverage:
    python3 scripts/prior_art.py coverage --root .

# Show which implementation commands are intentionally still placeholders.
status:
    cargo xtask status

# Placeholder until its owning plan task is ready.
build-kernel:
    cargo xtask unavailable build-kernel

# Cross-build a fresh static non-JIT AArch64-musl OTP release.
build-otp:
    python3 scripts/otp_artifact.py build

# Verify the complete native OTP release closure against its sealed ELF policy.
inspect-otp-artifact:
    python3 scripts/otp_artifact.py inspect

# Repeat the clean cross-build and require an exact native-closure match.
verify-otp-rebuild:
    python3 scripts/otp_artifact.py verify-rebuild

# Build a genuine runtime_lab Mix release with the pinned host OTP/Elixir pair.
build-release:
    python3 scripts/runtime_release.py build

# Pair the Mix payload with the exact target ERTS and prove a clean rebuild matches.
pair-release:
    python3 scripts/runtime_release.py pair

# Run unit checks and ten authoritative full-system AArch64 Linux release boots.
test-target-release-linux:
    python3 -m unittest tests.test_runtime_release -v
    python3 scripts/runtime_release.py run --boots 10 --output target/runtime-release/acceptance

# Placeholder until its owning plan task is ready.
image:
    cargo xtask unavailable image

# Placeholder until its owning plan task is ready.
run-headless:
    cargo xtask unavailable run-headless

# Placeholder until its owning plan task is ready.
run-gui:
    cargo xtask unavailable run-gui

# Placeholder until its owning plan task is ready.
test-qemu:
    cargo xtask unavailable test-qemu
