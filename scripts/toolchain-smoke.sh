#!/usr/bin/env bash
set -euo pipefail

if (($# != 2)); then
  echo "usage: toolchain-smoke.sh CACHE WORK" >&2
  exit 2
fi

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cache="$1"
work="$2"
otp_archive="$(python3 "$repo_root/scripts/toolchain.py" path otp-source --cache "$cache")"
elixir_archive="$(python3 "$repo_root/scripts/toolchain.py" path elixir-source --cache "$cache")"

rm -rf "$work/build" "$work/home" "$work/install" "$work/smoke"
mkdir -p "$work/build/otp" "$work/build/elixir" "$work/home" "$work/install"

export HOME="$work/home"
export MIX_HOME="$work/home/.mix"
export HEX_HOME="$work/home/.hex"
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export TZ=UTC
export SOURCE_DATE_EPOCH=1788220800

echo "toolchain smoke: extracting OTP 29.0.5"
tar -xf "$otp_archive" --strip-components=1 -C "$work/build/otp"
cd "$work/build/otp"
echo "toolchain smoke: configuring OTP 29.0.5"
./configure \
  --prefix="$work/install/otp" \
  --without-javac \
  --without-odbc \
  --without-wx
echo "toolchain smoke: building OTP 29.0.5"
make -j"$(getconf _NPROCESSORS_ONLN)"
make install

export PATH="$work/install/otp/bin:$PATH"
otp_version="$(tr -d '\r\n' <"$work/install/otp/lib/erlang/releases/29/OTP_VERSION")"
if [[ "$otp_version" != "29.0.5" ]]; then
  echo "toolchain smoke: expected OTP 29.0.5, found $otp_version" >&2
  exit 1
fi

echo "toolchain smoke: extracting Elixir 1.20.4"
tar -xf "$elixir_archive" --strip-components=1 -C "$work/build/elixir"
cd "$work/build/elixir"
echo "toolchain smoke: building Elixir 1.20.4"
ERL_COMPILER_OPTIONS=deterministic make -j"$(getconf _NPROCESSORS_ONLN)"
export PATH="$work/build/elixir/bin:$PATH"

elixir_version="$(elixir --short-version)"
if [[ "$elixir_version" != "1.20.4" ]]; then
  echo "toolchain smoke: expected Elixir 1.20.4, found $elixir_version" >&2
  exit 1
fi

cp -R "$repo_root/beam/toolchain_smoke" "$work/smoke"
cd "$work/smoke"
echo "toolchain smoke: compiling dependency-free Mix project"
mix compile --warnings-as-errors
mix test
identity="$(mix run -e 'IO.write(ToolchainSmoke.identity_line())')"
expected_identity="otp=29.0.5 elixir=1.20.4"
if [[ "$identity" != "$expected_identity" ]]; then
  echo "toolchain smoke: expected '$expected_identity', found '$identity'" >&2
  exit 1
fi

OTP_VERSION="$otp_version" \
ELIXIR_VERSION="$elixir_version" \
IDENTITY="$identity" \
python3 - "$work/smoke-receipt.json" <<'PY'
import json
import os
import sys

receipt = {
    "schema": "rust-beam/runtime-pair-smoke/v1",
    "result": "pass",
    "network": "disabled",
    "otp": os.environ["OTP_VERSION"],
    "elixir": os.environ["ELIXIR_VERSION"],
    "application": "beam/toolchain_smoke",
    "identity": os.environ["IDENTITY"],
}
with open(sys.argv[1], "w", encoding="utf-8") as output:
    json.dump(receipt, output, indent=2, sort_keys=True)
    output.write("\n")
PY

echo "toolchain smoke: PASS $identity"
