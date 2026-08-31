#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cache="${RB_TOOLCHAIN_CACHE:-$repo_root/target/toolchain-cache}"
receipts="$repo_root/target/toolchain-receipts"
smoke_work="$repo_root/target/toolchain-smoke"
image="docker.io/library/python@sha256:c900d35aba5fe4c1dc1cd358408baae2902ff2a2926a1d15cc5002c6061ddb2e"

find_docker() {
  if docker info >/dev/null 2>&1; then
    docker_command=(docker)
  elif sudo -n docker info >/dev/null 2>&1; then
    docker_command=(sudo -n docker)
  else
    echo "toolchain bootstrap: a running Docker Engine is required for clean-builder evidence" >&2
    echo "toolchain bootstrap: start Docker, then rerun this command" >&2
    exit 2
  fi
}

echo "toolchain bootstrap: mirroring the complete sealed source lock"
python3 "$repo_root/scripts/toolchain.py" fetch --cache "$cache"

find_docker
echo "toolchain bootstrap: pulling pinned multi-architecture builder image"
"${docker_command[@]}" pull "$image"

rm -rf "$receipts" "$smoke_work"
mkdir -p "$receipts" "$smoke_work"

run_receipt() {
  local builder_id="$1"
  local output="$2"
  "${docker_command[@]}" run --rm \
    --network none \
    --read-only \
    --tmpfs /tmp:rw,nosuid,nodev \
    --mount "type=bind,src=$repo_root,dst=/workspace,readonly" \
    --workdir /workspace \
    --env "RB_CONTAINER_IMAGE=$image" \
    --entrypoint python3 \
    "$image" \
    scripts/toolchain.py receipt --builder-id "$builder_id" >"$output"
}

echo "toolchain bootstrap: observing two fresh network-disabled Linux builders"
run_receipt linux-clean-a "$receipts/linux-clean-a.json"
run_receipt linux-clean-b "$receipts/linux-clean-b.json"
python3 "$repo_root/scripts/toolchain.py" compare \
  "$receipts/linux-clean-a.json" \
  "$receipts/linux-clean-b.json" \
  --output "$receipts/comparison.json"

echo "toolchain bootstrap: building OTP/Elixir pair with networking disabled"
"${docker_command[@]}" run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$repo_root,dst=/workspace,readonly" \
  --mount "type=bind,src=$cache,dst=/cache,readonly" \
  --mount "type=bind,src=$smoke_work,dst=/work" \
  --workdir /workspace \
  --entrypoint /bin/bash \
  "$image" \
  /workspace/scripts/toolchain-smoke.sh /cache /work \
  2>&1 | tee "$receipts/runtime-smoke.txt"
cp "$smoke_work/smoke-receipt.json" "$receipts/runtime-smoke.json"

python3 "$repo_root/scripts/toolchain.py" verify \
  --cache "$cache" \
  --require-cache \
  --receipt "$receipts/linux-clean-a.json" \
  --receipt "$receipts/linux-clean-b.json"
echo "toolchain bootstrap: complete"
