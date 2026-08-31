#!/usr/bin/env python3
"""Audit, reproduce, and coverage-check the pinned Tyn prior art."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

COMMIT = "105c4946c756a6f3d23d1c41b9e8139352ddc115"
CATEGORIES = {
    "accepted-residual-risk",
    "already-covered",
    "architecture-difference",
    "new-contract-test",
    "not-reproducible",
}
REQUIRED_FINDINGS = {
    "clear-child-tid-join",
    "crypto-tls-claims",
    "external-capability-rates",
    "fork-exec-subprocesses",
    "identity-map-isolation",
    "init-thread-progress-valve",
    "jit-and-static-nifs",
    "kvm-nitro-evidence-profile",
    "kvm-reproduction-unavailable",
    "mutable-build-base",
    "networking-and-distribution",
    "renderer-boundary-absent",
    "robust-futex-noop",
    "signal-semantics-absent",
    "stale-packaged-artifacts",
    "syscall-success-stubs",
    "tcg-memory-faults",
    "writable-storage",
    "x86-hardware-rng",
    "x86-platform-coupling",
}
REPORT_TERMS = (
    "Inspected",
    "Author report",
    "Project observation",
    "serial_shell ready",
    "120 seconds",
    "Documentation skew",
    "AArch64",
    "QEMU `virt`",
    "non-JIT",
    "two-process",
    "signal",
    "clear_child_tid",
    "not a pattern",
    "proves **none**",
)


class PriorArtError(ValueError):
    """Raised when prior-art evidence is invalid or reproduction fails."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PriorArtError(f"{path}: cannot read JSON: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lock_path(root: Path) -> Path:
    return root / "docs/prior-art/tyn.lock.json"


def coverage_path(root: Path) -> Path:
    return root / "docs/prior-art/tyn-coverage.json"


def load_lock(root: Path) -> dict[str, Any]:
    path = lock_path(root)
    lock = load_json(path)
    expected_fields = {
        "schema",
        "project",
        "repository",
        "commit",
        "retrieved_on",
        "archive",
        "source_files",
        "artifacts",
        "runtime",
        "kernel_build",
        "authoritative_runner",
    }
    if not isinstance(lock, dict) or set(lock) != expected_fields:
        raise PriorArtError(f"{path}: unexpected top-level fields")
    if lock["schema"] != "rust-beam/prior-art-lock/v1" or lock["commit"] != COMMIT:
        raise PriorArtError(f"{path}: unsupported schema or wrong commit")
    archive = lock["archive"]
    if not isinstance(archive, dict) or set(archive) != {"url", "sha256", "size"}:
        raise PriorArtError(f"{path}: malformed archive lock")
    if not re.fullmatch(r"[0-9a-f]{64}", archive["sha256"]):
        raise PriorArtError(f"{path}: malformed archive SHA-256")
    if COMMIT not in archive["url"] or not isinstance(archive["size"], int):
        raise PriorArtError(f"{path}: archive is not pinned by the reviewed commit")
    source_paths: list[str] = []
    for item in lock["source_files"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise PriorArtError(f"{path}: malformed source-file entry")
        pure = PurePosixPath(item["path"])
        if pure.is_absolute() or ".." in pure.parts:
            raise PriorArtError(f"{path}: unsafe source path: {item['path']}")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            raise PriorArtError(f"{path}: malformed source hash: {item['path']}")
        source_paths.append(item["path"])
    if source_paths != sorted(set(source_paths)):
        raise PriorArtError(f"{path}: source files must be unique and sorted")
    return lock


def validate_source_ledger(root: Path, lock: dict[str, Any]) -> None:
    path = root / "docs/evidence/sources.json"
    ledger = load_json(path)
    entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    matches = [entry for entry in entries if entry.get("id") == "RB-SRC-TYN-105C4946"]
    if len(matches) != 1:
        raise PriorArtError(f"{path}: expected exactly one RB-SRC-TYN-105C4946 entry")
    entry = matches[0]
    expected_digest = f"sha256:{lock['archive']['sha256']}"
    if (
        entry.get("immutable_reference") != COMMIT
        or entry.get("digest") != expected_digest
        or entry.get("classification") != "prior-art"
        or "RB-T-P017" not in entry.get("consumers", [])
    ):
        raise PriorArtError(f"{path}: Tyn source entry disagrees with the lock")


def audit(root: Path) -> int:
    lock = load_lock(root)
    report_path = root / "docs/prior-art/tyn.md"
    report = report_path.read_text(encoding="utf-8")
    missing = [term for term in REPORT_TERMS if term not in report]
    if missing:
        raise PriorArtError(f"{report_path}: missing required audit terms: {missing}")
    if report.count(COMMIT) < 2:
        raise PriorArtError(f"{report_path}: sources are not consistently pinned")
    validate_source_ledger(root, lock)

    cache = root / f"target/prior-art/tyn/{COMMIT}.tar.gz"
    if cache.is_file():
        if cache.stat().st_size != lock["archive"]["size"] or sha256(cache) != lock["archive"]["sha256"]:
            raise PriorArtError(f"{cache}: cached archive disagrees with lock")
        cache_status = "verified"
    else:
        cache_status = "not-present (run reproduction to fetch and verify)"
    print(f"Tyn audit: commit={COMMIT} source_files={len(lock['source_files'])} archive={cache_status}")
    print("Tyn audit: inspected facts, author reports, project observations, and claim boundaries are explicit")
    return 0


def known_plan_ids(root: Path) -> set[str]:
    index = load_json(root / "docs/plan/generated/index.json")
    return {record["id"] for record in index["records"]}


def known_just_commands(root: Path) -> set[str]:
    commands: set[str] = set()
    for line in (root / "justfile").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([a-zA-Z0-9_-]+)(?: [^:]*)?:", line)
        if match:
            commands.add(f"just {match.group(1)}")
    return commands


def coverage(root: Path) -> int:
    lock = load_lock(root)
    path = coverage_path(root)
    record = load_json(path)
    if not isinstance(record, dict) or set(record) != {"schema", "task", "source_commit", "findings"}:
        raise PriorArtError(f"{path}: unexpected fields")
    if (
        record["schema"] != "rust-beam/prior-art-coverage/v1"
        or record["task"] != "RB-T-P017"
        or record["source_commit"] != COMMIT
        or not isinstance(record["findings"], list)
    ):
        raise PriorArtError(f"{path}: malformed coverage header")

    source_paths = {item["path"] for item in lock["source_files"]}
    plan_ids = known_plan_ids(root)
    just_commands = known_just_commands(root)
    seen: set[str] = set()
    observed_categories: set[str] = set()
    for finding in record["findings"]:
        if not isinstance(finding, dict) or set(finding) != {
            "id",
            "category",
            "source",
            "disposition",
            "consumers",
        }:
            raise PriorArtError(f"{path}: malformed finding")
        finding_id = finding["id"]
        if finding_id in seen:
            raise PriorArtError(f"{path}: duplicate finding: {finding_id}")
        seen.add(finding_id)
        if finding["category"] not in CATEGORIES:
            raise PriorArtError(f"{path}: unsupported category for {finding_id}")
        observed_categories.add(finding["category"])
        if finding["source"] not in source_paths:
            raise PriorArtError(f"{path}: unlocked source for {finding_id}: {finding['source']}")
        if not isinstance(finding["disposition"], str) or not finding["disposition"]:
            raise PriorArtError(f"{path}: empty disposition for {finding_id}")
        if not isinstance(finding["consumers"], list) or not finding["consumers"]:
            raise PriorArtError(f"{path}: no consumer for {finding_id}")
        for consumer in finding["consumers"]:
            if consumer.startswith("just "):
                if consumer not in just_commands:
                    raise PriorArtError(f"{path}: unknown command consumer: {consumer}")
            elif consumer not in plan_ids:
                raise PriorArtError(f"{path}: unknown plan consumer: {consumer}")
    if seen != REQUIRED_FINDINGS:
        raise PriorArtError(
            f"{path}: finding set differs; missing={sorted(REQUIRED_FINDINGS - seen)}, "
            f"extra={sorted(seen - REQUIRED_FINDINGS)}"
        )
    if observed_categories != CATEGORIES:
        raise PriorArtError(f"{path}: not every disposition category is represented")

    gate = (root / "docs/plan/gates/rb-g-gate0.md").read_text(encoding="utf-8")
    if "scheduler/thread progress requires an unexplained wait-semantics workaround" not in gate:
        raise PriorArtError("RB-G-GATE0 does not retain scheduler/thread progress as a kill criterion")
    print(f"Tyn coverage: {len(seen)} relevant findings, 5 dispositions, no missing consumer")
    print("Gate 0 coverage: ERTS SMP/thread progress remains a first-class kill criterion")
    return 0


def ensure_archive(root: Path, lock: dict[str, Any]) -> Path:
    cache = root / f"target/prior-art/tyn/{COMMIT}.tar.gz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        partial = cache.with_suffix(".partial")
        try:
            with urllib.request.urlopen(lock["archive"]["url"], timeout=60) as response:
                with partial.open("wb") as output:
                    shutil.copyfileobj(response, output)
            partial.replace(cache)
        finally:
            partial.unlink(missing_ok=True)
    if cache.stat().st_size != lock["archive"]["size"] or sha256(cache) != lock["archive"]["sha256"]:
        raise PriorArtError(f"{cache}: archive digest or size mismatch")
    return cache


def extract_archive(archive: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir()
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if not members:
            raise PriorArtError(f"{archive}: empty archive")
        first_parts = {PurePosixPath(member.name).parts[0] for member in members if member.name}
        if len(first_parts) != 1:
            raise PriorArtError(f"{archive}: expected one top-level directory")
        prefix = next(iter(first_parts))
        for member in members:
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or ".." in pure.parts:
                raise PriorArtError(f"{archive}: unsafe member: {member.name}")
            if member.issym() or member.islnk():
                raise PriorArtError(f"{archive}: links are not accepted: {member.name}")
            relative = PurePosixPath(*pure.parts[1:]) if pure.parts and pure.parts[0] == prefix else pure
            if not relative.parts:
                continue
            target = destination / Path(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise PriorArtError(f"{archive}: cannot read member: {member.name}")
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)


def verify_sources(source: Path, lock: dict[str, Any]) -> None:
    for item in lock["source_files"]:
        path = source / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise PriorArtError(f"{path}: source digest mismatch")
    for artifact in lock["artifacts"].values():
        path = source / artifact["path"]
        if (
            not path.is_file()
            or path.stat().st_size != artifact["size"]
            or sha256(path) != artifact["sha256"]
        ):
            raise PriorArtError(f"{path}: artifact digest or size mismatch")


def inspect_elf(source: Path, lock: dict[str, Any]) -> None:
    beam = source / lock["artifacts"]["beam"]["path"]
    result = subprocess.run(
        ["readelf", "-h", "-l", "-d", "-n", str(beam)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    expected = lock["artifacts"]["beam"]["elf"]
    required = (
        "Class:                             ELF64",
        "Data:                              2's complement, little endian",
        "Type:                              EXEC (Executable file)",
        "Machine:                           Advanced Micro Devices X86-64",
        f"Entry point address:               {expected['entry']}",
        f"Number of program headers:         {expected['program_headers']}",
        "There is no dynamic section in this file.",
        f"Build ID: {expected['build_id']}",
    )
    missing = [line for line in required if line not in result.stdout]
    load_count = sum(1 for line in result.stdout.splitlines() if line.lstrip().startswith("LOAD "))
    if result.returncode != 0 or missing or load_count != expected["load_segments"]:
        raise PriorArtError(f"{beam}: ELF contract mismatch; missing={missing}, loads={load_count}")


def build_kernel(root: Path, source: Path, lock: dict[str, Any]) -> tuple[Path, str]:
    target = root / "target/prior-art/tyn/build"
    target.mkdir(parents=True, exist_ok=True)
    build_source = Path("/tmp") / f"rust-beam-p017-tyn-{COMMIT}"
    shutil.rmtree(build_source, ignore_errors=True)
    try:
        shutil.copytree(source, build_source)
        command = lock["kernel_build"]["command"]
        environment = os.environ.copy()
        environment["CARGO_TARGET_DIR"] = str(target)
        result = subprocess.run(
            command,
            cwd=build_source,
            env=environment,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=600,
        )
    finally:
        shutil.rmtree(build_source, ignore_errors=True)
    transcript = root / "target/prior-art/tyn/kernel-build.txt"
    transcript.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        raise PriorArtError(f"Tyn kernel build failed; see {transcript}")
    kernel = target / "x86_64-tyn/release/tyn-kernel"
    if not kernel.is_file():
        raise PriorArtError("Tyn kernel build reported success without its output")
    return kernel, sha256(kernel)


def attempt_kvm_boot(kernel: Path) -> dict[str, Any]:
    reasons: list[str] = []
    if platform.machine() != "x86_64":
        reasons.append(f"host architecture is {platform.machine()}, not x86_64")
    if not Path("/dev/kvm").exists():
        reasons.append("/dev/kvm is absent")
    qemu = shutil.which("qemu-system-x86_64")
    if qemu is None:
        reasons.append("qemu-system-x86_64 is absent")
    if reasons:
        return {"status": "blocked", "reasons": reasons, "tcg_substituted": False}

    command = [
        qemu,
        "-kernel",
        str(kernel),
        "-m",
        "2560M",
        "-machine",
        "q35",
        "-cpu",
        "host",
        "-enable-kvm",
        "-smp",
        "8",
        "-nographic",
        "-no-reboot",
        "-serial",
        "mon:stdio",
        "-device",
        "virtio-net-pci,netdev=net0,disable-legacy=on,disable-modern=off",
        "-netdev",
        "user,id=net0",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        output, _ = process.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    text = output.decode("utf-8", errors="replace")
    ready = "serial_shell ready" in text or "phoenix_listening" in text
    return {
        "status": "pass" if ready else "fail",
        "command": command,
        "ready_marker": ready,
        "output_tail": text[-4000:],
        "tcg_substituted": False,
    }


def reproduce(root: Path) -> int:
    lock = load_lock(root)
    validate_source_ledger(root, lock)
    archive = ensure_archive(root, lock)
    source = root / "target/prior-art/tyn/source"
    extract_archive(archive, source)
    verify_sources(source, lock)
    inspect_elf(source, lock)
    kernel, kernel_hash = build_kernel(root, source, lock)
    boot = attempt_kvm_boot(kernel)
    observation = {
        "schema": "rust-beam/prior-art-observation/v1",
        "commit": COMMIT,
        "host": {"os": platform.platform(), "architecture": platform.machine()},
        "archive_sha256": sha256(archive),
        "source_files_verified": len(lock["source_files"]),
        "committed_beam_sha256": lock["artifacts"]["beam"]["sha256"],
        "kernel_build": {"status": "pass", "sha256": kernel_hash},
        "kvm_boot": boot,
    }
    output = root / "target/prior-art/tyn/current-observation.json"
    output.write_text(json.dumps(observation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(observation, indent=2))
    if boot["status"] == "fail":
        raise PriorArtError("an available KVM profile failed to reach a readiness marker")
    print(f"Tyn reproduction observation written to {output.relative_to(root)}")
    return 0


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("command", choices=("audit", "reproduce", "coverage"))
    argument_parser.add_argument("--root", type=Path, default=Path.cwd())
    return argument_parser


def main() -> int:
    args = parser().parse_args()
    root = args.root.resolve()
    try:
        if args.command == "audit":
            return audit(root)
        if args.command == "coverage":
            return coverage(root)
        return reproduce(root)
    except (OSError, PriorArtError, subprocess.TimeoutExpired) as error:
        print(f"prior-art: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
