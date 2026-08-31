#!/usr/bin/env python3
"""Validate, mirror, report, and compare the frozen Phase 0 toolchain."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / "toolchain" / "sources.lock.json"
CONTRACT_PATH = REPO_ROOT / "toolchain" / "contract.json"
REPORT_PATH = REPO_ROOT / "toolchain" / "TOOLCHAIN.md"
DEFAULT_CACHE = REPO_ROOT / "target" / "toolchain-cache"
SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
MUTABLE_RE = re.compile(r"(^|[/@:])(latest|main|master|stable)([/@:]|$)", re.IGNORECASE)
COMMAND_SEPARATOR = " \\" + "\n  "
ENTRY_FIELDS = {
    "id",
    "component",
    "version",
    "artifact",
    "kind",
    "hosts",
    "locator",
    "immutable_reference",
    "digest",
    "size",
    "digest_provenance",
    "license",
    "license_locator",
    "mirror_path",
    "consumers",
}
REQUIRED_SOURCE_IDS = {
    "elixir-source",
    "llvm-aarch64",
    "llvm-source",
    "llvm-x86_64",
    "musl-source",
    "otp-source",
    "python-builder-image",
    "qemu-signature",
    "qemu-source",
    "rust-aarch64",
    "rust-channel-manifest",
    "rust-std-aarch64-musl",
    "rust-std-aarch64-none",
    "rust-x86_64",
}


class ToolchainError(Exception):
    """A user-facing toolchain contract failure."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ToolchainError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ToolchainError(f"{path}: top-level value must be an object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def object_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def entry_map(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in lock["entries"]}


def validate_lock(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_top = {
        "schema",
        "revision",
        "state",
        "sealed_at",
        "policy",
        "cache_layout",
        "entries",
    }
    if set(lock) != expected_top:
        raise ToolchainError("source lock has missing or unknown top-level fields")
    if lock["schema"] != "rust-beam/source-lock/v1":
        raise ToolchainError("source lock schema must be rust-beam/source-lock/v1")
    if lock["revision"] != 1 or lock["state"] != "sealed":
        raise ToolchainError("source lock revision 1 must be sealed")
    if lock["cache_layout"] != "sha256/<digest>":
        raise ToolchainError("source lock cache layout changed")
    if not isinstance(lock["entries"], list) or not lock["entries"]:
        raise ToolchainError("source lock must contain entries")

    ids: list[str] = []
    for index, entry in enumerate(lock["entries"]):
        location = f"source lock entry {index}"
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            raise ToolchainError(f"{location} has missing or unknown fields")
        source_id = entry["id"]
        if not isinstance(source_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", source_id):
            raise ToolchainError(f"{location} has invalid id")
        ids.append(source_id)
        digest_match = SHA256_RE.fullmatch(entry["digest"])
        if not digest_match:
            raise ToolchainError(f"{source_id}: digest must be lowercase SHA-256")
        if not isinstance(entry["size"], int) or entry["size"] <= 0:
            raise ToolchainError(f"{source_id}: size must be a positive integer")
        locator = entry["locator"]
        if not isinstance(locator, str) or not locator.startswith(("https://", "docker://")):
            raise ToolchainError(f"{source_id}: locator must use HTTPS or an OCI digest")
        if MUTABLE_RE.search(locator) or MUTABLE_RE.search(entry["immutable_reference"]):
            raise ToolchainError(f"{source_id}: mutable reference is forbidden")
        if entry["kind"] not in {"archive", "binary", "manifest", "oci-index", "signature"}:
            raise ToolchainError(f"{source_id}: unsupported artifact kind")
        if not isinstance(entry["hosts"], list) or not entry["hosts"]:
            raise ToolchainError(f"{source_id}: hosts must be a non-empty list")
        digest_hex = digest_match.group(1)
        expected_mirror = (
            f"oci/sha256/{digest_hex}"
            if entry["kind"] == "oci-index"
            else f"sha256/{digest_hex}"
        )
        if entry["mirror_path"] != expected_mirror:
            raise ToolchainError(f"{source_id}: mirror path is not content-addressed")
        for field in ("component", "version", "artifact", "digest_provenance", "license"):
            if not isinstance(entry[field], str) or not entry[field].strip():
                raise ToolchainError(f"{source_id}: {field} must be non-empty")
        if not entry["license_locator"].startswith("https://"):
            raise ToolchainError(f"{source_id}: license locator must use HTTPS")
        if not isinstance(entry["consumers"], list) or "RB-T-P003" not in entry["consumers"]:
            raise ToolchainError(f"{source_id}: RB-T-P003 must own the pin")

    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ToolchainError("source lock entries must have unique, sorted ids")
    if not REQUIRED_SOURCE_IDS.issubset(ids):
        missing = sorted(REQUIRED_SOURCE_IDS - set(ids))
        raise ToolchainError(f"source lock is missing required pins: {', '.join(missing)}")
    return entry_map(lock)


def validate_contract(
    contract: dict[str, Any], lock: dict[str, Any], sources: dict[str, dict[str, Any]]
) -> None:
    required_top = {
        "schema",
        "revision",
        "status",
        "selected_at",
        "source_lock_revision",
        "source_ids",
        "runtime_pair",
        "rust",
        "cross_toolchain",
        "targets",
        "musl",
        "qemu",
        "builder",
        "runner_profiles",
        "residual_risks",
    }
    if set(contract) != required_top:
        raise ToolchainError("toolchain contract has missing or unknown top-level fields")
    if contract["schema"] != "rust-beam/toolchain-contract/v1":
        raise ToolchainError("unexpected toolchain contract schema")
    if contract["revision"] != 1 or contract["status"] != "p003-frozen-candidate":
        raise ToolchainError("toolchain contract revision/status changed")
    if contract["source_lock_revision"] != lock["revision"]:
        raise ToolchainError("toolchain contract references the wrong source-lock revision")
    source_ids = contract["source_ids"]
    if source_ids != sorted(sources) or len(source_ids) != len(set(source_ids)):
        raise ToolchainError("toolchain contract must consume the complete sorted source lock")

    pair = contract["runtime_pair"]
    if pair["otp"]["version"] != sources[pair["otp"]["source_id"]]["version"]:
        raise ToolchainError("OTP contract does not match its source pin")
    if pair["elixir"]["version"] != sources[pair["elixir"]["source_id"]]["version"]:
        raise ToolchainError("Elixir contract does not match its source pin")
    if pair["elixir"]["supported_otp"] != "27-29":
        raise ToolchainError("Elixir/OTP compatibility range changed without evidence")
    if contract["rust"]["version"] != "1.89.0":
        raise ToolchainError("Rust contract drifted from rust-toolchain.toml")
    if contract["musl"]["version"] != sources[contract["musl"]["source_id"]]["version"]:
        raise ToolchainError("musl contract does not match its source pin")
    if contract["qemu"]["version"] != sources[contract["qemu"]["source_id"]]["version"]:
        raise ToolchainError("QEMU contract does not match its source pin")
    if contract["qemu"]["candidate_machine"] != "virt-11.1":
        raise ToolchainError("QEMU must use the versioned candidate machine")
    if contract["builder"]["image"] != sources[contract["builder"]["image_source_id"]]["locator"].removeprefix("docker://"):
        raise ToolchainError("builder image does not match the OCI source pin")
    if set(contract["builder"]["platforms"]) != {"x86_64", "aarch64"}:
        raise ToolchainError("builder must pin x86_64 and AArch64 child manifests")
    if contract["targets"]["kernel_rust"]["triple"] != "aarch64-unknown-none":
        raise ToolchainError("kernel Rust target changed")
    if contract["targets"]["userspace_rust"]["triple"] != "aarch64-unknown-linux-musl":
        raise ToolchainError("userspace Rust target changed")

    profiles = contract["runner_profiles"]
    expected_profiles = {
        "linux-tcg-full-system",
        "linux-aarch64-kvm-full-system",
        "linux-user-smoke",
        "macos-hvf-full-system",
    }
    if set(profiles) != expected_profiles:
        raise ToolchainError("full-system and qemu-user runner lanes must remain separate")
    for name, profile in profiles.items():
        if not isinstance(profile.get("command"), list) or not profile["command"]:
            raise ToolchainError(f"runner profile {name} has no command")
        command = " ".join(profile["command"])
        if "qemu-system" in command and "virt-11.1" not in command:
            raise ToolchainError(f"runner profile {name} uses a moving machine alias")


def load_and_validate() -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
    lock = load_json(LOCK_PATH)
    sources = validate_lock(lock)
    contract = load_json(CONTRACT_PATH)
    validate_contract(contract, lock, sources)
    return lock, contract, sources


def cache_path(entry: dict[str, Any], cache: Path) -> Path:
    return cache / entry["mirror_path"]


def verify_artifact(path: Path, entry: dict[str, Any]) -> None:
    if not path.is_file():
        raise ToolchainError(f"{entry['id']}: missing cache artifact {path}")
    actual_size = path.stat().st_size
    if actual_size != entry["size"]:
        raise ToolchainError(
            f"{entry['id']}: expected {entry['size']} bytes, found {actual_size}"
        )
    actual_digest = file_digest(path)
    if actual_digest != entry["digest"]:
        raise ToolchainError(
            f"{entry['id']}: expected {entry['digest']}, found {actual_digest}"
        )


def fetch_entry(entry: dict[str, Any], cache: Path) -> None:
    destination = cache_path(entry, cache)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        verify_artifact(destination, entry)
        print(f"toolchain fetch: {entry['id']} already verified")
        return
    partial = destination.with_suffix(".partial")
    print(f"toolchain fetch: {entry['id']} ({entry['size']} bytes)")
    command = [
        "curl",
        "--fail",
        "--location",
        "--proto",
        "=https",
        "--tlsv1.2",
        "--retry",
        "3",
        "--continue-at",
        "-",
        "--output",
        str(partial),
        entry["locator"],
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise ToolchainError(f"{entry['id']}: curl exited {result.returncode}")
    verify_artifact(partial, entry)
    partial.replace(destination)


def render_report(
    lock: dict[str, Any], contract: dict[str, Any], sources: dict[str, dict[str, Any]]
) -> str:
    pair = contract["runtime_pair"]
    target = contract["targets"]
    builder = contract["builder"]
    lines = [
        "# Phase 0 toolchain report",
        "",
        f"Status: **{contract['status']}**, contract revision {contract['revision']}, "
        f"source-lock revision {lock['revision']}.",
        "",
        "This report is generated from `toolchain/contract.json` and",
        "`toolchain/sources.lock.json`. Gate 0 has not authorized kernel work.",
        "",
        "## Selected runtime and compiler set",
        "",
        "| Component | Version | Immutable source | License |",
        "| --- | --- | --- | --- |",
    ]
    report_ids = [
        pair["otp"]["source_id"],
        pair["elixir"]["source_id"],
        "rust-channel-manifest",
        contract["cross_toolchain"]["source_id"],
        contract["musl"]["source_id"],
        contract["qemu"]["source_id"],
        contract["builder"]["image_source_id"],
    ]
    for source_id in report_ids:
        source = sources[source_id]
        lines.append(
            f"| {source['component']} | {source['version']} | `{source['digest']}` | "
            f"{source['license']} |"
        )
    lines += [
        "",
        "Elixir 1.20.4 declares support for OTP 27–29. The sealed, network-disabled",
        "smoke build exercises the selected OTP 29.0.5 pair from source.",
        "",
        "## Target contract",
        "",
        f"- Kernel Rust: `{target['kernel_rust']['triple']}`, CPU "
        f"`{target['kernel_rust']['cpu']}`, {target['kernel_rust']['isa_floor']}.",
        f"- Userspace Rust: `{target['userspace_rust']['triple']}`, "
        f"{target['userspace_rust']['isa_floor']}, static CRT.",
        f"- C/C++ compiler: {contract['cross_toolchain']['compiler']}; linker: "
        f"{contract['cross_toolchain']['linker']}.",
        f"- Userspace C library: musl {contract['musl']['version']} for "
        f"`{contract['musl']['target']}`.",
        "- C++ is admitted only for freestanding probes; no userspace C++ runtime is selected.",
        "- Page size: 4096 bytes; endianness: little.",
        "",
        "Kernel Rust flags: `" + " ".join(target["kernel_rust"]["rustflags"]) + "`",
        "",
        "Userspace C flags: `"
        + " ".join(contract["cross_toolchain"]["userspace_c"]["flags"])
        + "`",
        "",
        "## Builders",
        "",
        f"OCI index: `{builder['image']}`",
        "",
        f"- x86_64 Linux child: `{builder['platforms']['x86_64']}`",
        f"- AArch64 Linux child: `{builder['platforms']['aarch64']}`",
        "",
        "The same contract and source lock are consumed on both hosts. Host-native Rust,",
        "LLVM, and Ninja archives differ by recorded digest; target triples and flags do not.",
        "Two fresh, network-disabled Linux containers compare the architecture-independent",
        "receipt contract byte-for-byte. This is metadata equivalence, not a binary",
        "reproducibility claim.",
        "",
        "## QEMU runner boundaries",
        "",
    ]
    for name, profile in contract["runner_profiles"].items():
        lines += [
            f"### `{name}`",
            "",
            f"Host: {profile['host']}. Claim: {profile['claim']}.",
            "",
            "```sh",
            COMMAND_SEPARATOR.join(profile["command"]),
            "```",
            "",
        ]
    lines += [
        "QEMU 11.1.0 and `virt-11.1` are P003 candidate pins. RB-T-P014 owns the",
        "final executable machine/CPU/GIC/HWCAP/DTB contract. HVF is available only",
        "on macOS and accelerates AArch64 only on Apple Silicon; x86_64 Linux uses TCG.",
        "qemu-user is never accepted as full-system, signal, thread, auxv, or startup proof.",
        "",
        "## Complete source closure",
        "",
        "| ID | Artifact | Hosts | SHA-256 | Provenance |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source_id in sorted(sources):
        source = sources[source_id]
        lines.append(
            f"| `{source_id}` | {source['component']} {source['version']} "
            f"({source['artifact']}) | {', '.join(source['hosts'])} | "
            f"`{source['digest']}` | {source['digest_provenance']} |"
        )
    lines += [
        "",
        "## Residual risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in contract["residual_risks"])
    lines += [
        "",
        "## Reproduce",
        "",
        "```sh",
        "just toolchain-bootstrap",
        "just toolchain-report",
        "just toolchain-verify",
        "```",
        "",
        "`toolchain-bootstrap` is the only networked step. It mirrors every archive by",
        "digest and pulls the OCI image by index digest. Runtime smoke and receipt",
        "comparison then execute with container networking disabled. `toolchain-verify`",
        "performs no network operation.",
        "",
    ]
    return "\n".join(lines)


def command_output(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ToolchainError(f"cannot probe {' '.join(command)}: {error}") from error
    return result.stdout.strip()


def tool_observations() -> dict[str, str]:
    commands = {
        "python3": ["python3", "--version"],
        "cc": ["cc", "--version"],
        "cxx": ["c++", "--version"],
        "ld": ["ld", "--version"],
        "make": ["make", "--version"],
        "autoconf": ["autoconf", "--version"],
        "perl": ["perl", "-e", "print $^V"],
        "git": ["git", "--version"],
        "curl": ["curl", "--version"],
        "pkg-config": ["pkg-config", "--version"],
    }
    return {name: command_output(command).splitlines()[0] for name, command in commands.items()}


def normalized_architecture() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"aarch64", "arm64"}:
        return "aarch64"
    raise ToolchainError(f"unsupported builder architecture: {machine}")


def os_release() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value.strip('"')
    return {"id": result.get("ID", "unknown"), "version_id": result.get("VERSION_ID", "unknown")}


def create_receipt(builder_id: str) -> dict[str, Any]:
    lock, contract, _ = load_and_validate()
    architecture = normalized_architecture()
    observations = tool_observations()
    for name, expected in contract["builder"]["expected_tools"].items():
        if expected not in observations[name]:
            raise ToolchainError(
                f"builder tool {name} expected {expected}, observed {observations[name]}"
            )
    expected_image = contract["builder"]["image"]
    observed_image = os.environ.get("RB_CONTAINER_IMAGE", "")
    if observed_image != expected_image:
        raise ToolchainError(
            f"receipt must run in {expected_image}; RB_CONTAINER_IMAGE was {observed_image!r}"
        )
    return {
        "schema": "rust-beam/toolchain-receipt/v1",
        "contract": contract,
        "contract_digest": object_digest(contract),
        "source_lock": lock,
        "source_lock_digest": object_digest(lock),
        "builder_observation": {
            "id": builder_id,
            "architecture": architecture,
            "os": os_release(),
            "container_index": observed_image,
            "container_platform_digest": contract["builder"]["platforms"][architecture],
            "tools": observations,
        },
    }


def compare_receipts(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    if len(receipts) < 2:
        raise ToolchainError("at least two builder receipts are required")
    for index, receipt in enumerate(receipts):
        if receipt.get("schema") != "rust-beam/toolchain-receipt/v1":
            raise ToolchainError(f"receipt {index} has the wrong schema")
        if receipt.get("contract_digest") != object_digest(receipt.get("contract")):
            raise ToolchainError(f"receipt {index} contract digest does not match")
        if receipt.get("source_lock_digest") != object_digest(receipt.get("source_lock")):
            raise ToolchainError(f"receipt {index} source-lock digest does not match")
    expected_contract = canonical_bytes(receipts[0]["contract"])
    expected_source_lock = canonical_bytes(receipts[0]["source_lock"])
    expected_lock = receipts[0]["source_lock_digest"]
    for index, receipt in enumerate(receipts[1:], 1):
        if canonical_bytes(receipt["contract"]) != expected_contract:
            raise ToolchainError(f"receipt {index} has toolchain contract drift")
        if (
            canonical_bytes(receipt["source_lock"]) != expected_source_lock
            or receipt["source_lock_digest"] != expected_lock
        ):
            raise ToolchainError(f"receipt {index} has source-lock drift")
    return {
        "schema": "rust-beam/toolchain-comparison/v1",
        "result": "match",
        "claim": "architecture-independent toolchain metadata matches; target binaries are not claimed bit-reproducible",
        "contract_digest": receipts[0]["contract_digest"],
        "source_lock_digest": expected_lock,
        "builders": [receipt["builder_observation"] for receipt in receipts],
    }


def write_json(value: Any, output: str | None) -> None:
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)


def cmd_fetch(args: argparse.Namespace) -> None:
    _, _, sources = load_and_validate()
    cache = Path(args.cache).resolve()
    selected = args.source_id or sorted(sources)
    unknown = sorted(set(selected) - set(sources))
    if unknown:
        raise ToolchainError(f"unknown source ids: {', '.join(unknown)}")
    for source_id in selected:
        entry = sources[source_id]
        if entry["kind"] == "oci-index":
            print(f"toolchain fetch: {source_id} is mirrored by OCI digest during bootstrap")
            continue
        fetch_entry(entry, cache)
    print(f"toolchain fetch: verified {len(selected)} source pin(s)")


def cmd_verify(args: argparse.Namespace) -> None:
    lock, contract, sources = load_and_validate()
    expected_report = render_report(lock, contract, sources)
    if not REPORT_PATH.is_file() or REPORT_PATH.read_text(encoding="utf-8") != expected_report:
        raise ToolchainError("toolchain/TOOLCHAIN.md is stale; run toolchain.py report --write")
    cache = Path(args.cache).resolve()
    present = 0
    missing: list[str] = []
    for source_id in sorted(sources):
        entry = sources[source_id]
        if entry["kind"] == "oci-index":
            continue
        path = cache_path(entry, cache)
        if path.exists():
            verify_artifact(path, entry)
            present += 1
        else:
            missing.append(source_id)
    if args.require_cache and missing:
        raise ToolchainError(f"cache is incomplete: {', '.join(missing)}")
    if args.receipt:
        receipts = [load_json(Path(path)) for path in args.receipt]
        compare_receipts(receipts)
    print(
        f"toolchain verify: contract revision {contract['revision']}, "
        f"{len(sources)} pins, {present} cached archive(s) verified"
    )


def cmd_report(args: argparse.Namespace) -> None:
    lock, contract, sources = load_and_validate()
    report = render_report(lock, contract, sources)
    if args.write:
        REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    else:
        sys.stdout.write(report)


def cmd_receipt(args: argparse.Namespace) -> None:
    write_json(create_receipt(args.builder_id), args.output)


def cmd_compare(args: argparse.Namespace) -> None:
    receipts = [load_json(Path(path)) for path in args.receipts]
    write_json(compare_receipts(receipts), args.output)


def cmd_path(args: argparse.Namespace) -> None:
    _, _, sources = load_and_validate()
    try:
        entry = sources[args.source_id]
    except KeyError as error:
        raise ToolchainError(f"unknown source id: {args.source_id}") from error
    print(cache_path(entry, Path(args.cache).resolve()))


def cmd_runner(args: argparse.Namespace) -> None:
    _, contract, _ = load_and_validate()
    try:
        profile = contract["runner_profiles"][args.profile]
    except KeyError as error:
        raise ToolchainError(f"unknown runner profile: {args.profile}") from error
    print(f"# Host: {profile['host']}")
    print(f"# Claim: {profile['claim']}")
    print(COMMAND_SEPARATOR.join(profile["command"]))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="mirror and verify immutable inputs")
    fetch.add_argument("--cache", default=str(DEFAULT_CACHE))
    fetch.add_argument("--source-id", action="append")
    fetch.set_defaults(function=cmd_fetch)

    verify = subparsers.add_parser("verify", help="validate lock, contract, cache, and receipts")
    verify.add_argument("--cache", default=str(DEFAULT_CACHE))
    verify.add_argument("--require-cache", action="store_true")
    verify.add_argument("--receipt", action="append")
    verify.set_defaults(function=cmd_verify)

    report = subparsers.add_parser("report", help="render the human-readable contract")
    report.add_argument("--write", action="store_true")
    report.set_defaults(function=cmd_report)

    receipt = subparsers.add_parser("receipt", help="observe one clean Linux builder")
    receipt.add_argument("--builder-id", required=True)
    receipt.add_argument("--output")
    receipt.set_defaults(function=cmd_receipt)

    compare = subparsers.add_parser("compare", help="compare normalized builder metadata")
    compare.add_argument("receipts", nargs="+")
    compare.add_argument("--output")
    compare.set_defaults(function=cmd_compare)

    path = subparsers.add_parser("path", help="print one content-addressed cache path")
    path.add_argument("source_id")
    path.add_argument("--cache", default=str(DEFAULT_CACHE))
    path.set_defaults(function=cmd_path)

    runner = subparsers.add_parser("runner", help="print a bounded QEMU runner profile")
    runner.add_argument("profile")
    runner.set_defaults(function=cmd_runner)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        args.function(args)
    except ToolchainError as error:
        print(f"toolchain: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
