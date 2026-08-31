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

# Show which implementation commands are intentionally still placeholders.
status:
    cargo xtask status

# Placeholder until its owning plan task is ready.
build-kernel:
    cargo xtask unavailable build-kernel

# Placeholder until its owning plan task is ready.
build-otp:
    cargo xtask unavailable build-otp

# Placeholder until its owning plan task is ready.
build-release:
    cargo xtask unavailable build-release

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
