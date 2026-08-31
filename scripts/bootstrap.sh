#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="$repo_root/toolchain/bootstrap-tools.json"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "bootstrap: Linux is required; macOS is an execution host, not the build host" >&2
  exit 2
fi

for command in curl python3 sha256sum cc; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "bootstrap: missing prerequisite: $command" >&2
    exit 2
  fi
done

case "$(uname -m)" in
  x86_64) rust_host="x86_64-unknown-linux-gnu" ;;
  aarch64 | arm64) rust_host="aarch64-unknown-linux-gnu" ;;
  *)
    echo "bootstrap: unsupported Linux architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

read_manifest() {
  python3 - "$manifest" "$1" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
for component in sys.argv[2].split("."):
    value = value[component]
print(value)
PY
}

rustup_version="$(read_manifest rustup_init.version)"
rustup_sha256="$(read_manifest "rustup_init.artifacts.${rust_host}.sha256")"
just_version="$(read_manifest just.version)"
rust_channel="$(read_manifest rust.channel)"

export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-$HOME/.rustup}"
export PATH="$CARGO_HOME/bin:$PATH"

if [[ ! -x "$CARGO_HOME/bin/rustup" ]]; then
  temporary="$(mktemp -d)"
  trap 'rm -rf "$temporary"' EXIT
  rustup_init="$temporary/rustup-init"
  rustup_url="https://static.rust-lang.org/rustup/archive/${rustup_version}/${rust_host}/rustup-init"
  echo "bootstrap: downloading pinned rustup-init ${rustup_version} for ${rust_host}"
  curl --fail --location --proto '=https' --tlsv1.2 --silent --show-error \
    "$rustup_url" --output "$rustup_init"
  printf '%s  %s\n' "$rustup_sha256" "$rustup_init" | sha256sum --check --status
  chmod +x "$rustup_init"
  "$rustup_init" -y --no-modify-path --profile minimal --default-toolchain none
fi

rustup set auto-self-update disable
echo "bootstrap: installing Rust ${rust_channel} from rust-toolchain.toml"
rustup toolchain install "$rust_channel" --profile minimal --component clippy --component rustfmt

installed_just=""
if [[ -x "$CARGO_HOME/bin/just" ]]; then
  installed_just="$("$CARGO_HOME/bin/just" --version | awk '{print $2}')"
fi
if [[ "$installed_just" != "$just_version" ]]; then
  echo "bootstrap: installing just ${just_version} with Cargo's locked package graph"
  cargo "+${rust_channel}" install just --version "$just_version" --locked --force
fi

echo "bootstrap: rustc $(rustc --version)"
echo "bootstrap: $(just --version)"
echo "bootstrap: running just check"
cd "$repo_root"
just check

echo "bootstrap: complete"
echo "bootstrap: add $CARGO_HOME/bin to PATH in future shells (or source $CARGO_HOME/env)"
