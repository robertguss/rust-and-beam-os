#!/usr/bin/env python3
"""Validate dependency-free Rust + BEAM evidence receipts and ledgers."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts import toolchain as toolchain_contract
except ModuleNotFoundError:
    import toolchain as toolchain_contract

EVIDENCE_FIELDS = {
    "schema",
    "id",
    "task",
    "recorded_at",
    "claim",
    "classification",
    "build",
    "command",
    "environment",
    "inputs",
    "artifacts",
    "result",
}
BUILD_FIELDS = {"id", "source_revision", "source_dirty", "target"}
COMMAND_FIELDS = {"argv", "cwd"}
ENVIRONMENT_FIELDS = {"os", "architecture", "tools"}
TOOL_FIELDS = {"name", "version"}
FILE_FIELDS = {"path", "digest"}
RESULT_FIELDS = {"status", "exit_code"}
SOURCE_FIELDS = {
    "id",
    "title",
    "locator",
    "retrieved_on",
    "immutable_reference",
    "digest",
    "classification",
    "claims",
    "consumers",
    "limitations",
}
INDEX_FIELDS = {"id", "task", "record", "claim"}

EVIDENCE_ID = re.compile(r"RB-EV-[A-Z0-9-]+\Z")
TASK_ID = re.compile(r"RB-[A-Z]+-[A-Z0-9]+\Z")
SOURCE_ID = re.compile(r"RB-SRC-[A-Z0-9-]+\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
BUILD_ID = re.compile(r"rb1-[0-9a-f]{12}-(?:clean|dirty)-[0-9]{8}T[0-9]{6}Z\Z")


class EvidenceError(ValueError):
    """Raised when an evidence contract is invalid."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EvidenceError(f"{path}: cannot read JSON: {error}") from error


def _mapping(value: Any, fields: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{where}: expected an object")
    actual = set(value)
    if actual != fields:
        missing = sorted(fields - actual)
        extra = sorted(actual - fields)
        raise EvidenceError(f"{where}: fields differ; missing={missing}, extra={extra}")
    return value


def _nonempty(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{where}: expected a non-empty string")
    return value


def _string_list(value: Any, where: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise EvidenceError(f"{where}: expected a {'possibly empty' if allow_empty else 'non-empty'} array")
    for index, item in enumerate(value):
        _nonempty(item, f"{where}[{index}]")
    return value


def _timestamp(value: Any, where: str) -> None:
    text = _nonempty(value, where)
    if not text.endswith("Z"):
        raise EvidenceError(f"{where}: timestamp must be UTC and end in Z")
    try:
        parsed = dt.datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as error:
        raise EvidenceError(f"{where}: invalid timestamp") from error
    if parsed.utcoffset() != dt.timedelta(0):
        raise EvidenceError(f"{where}: timestamp must be UTC")


def _date(value: Any, where: str) -> None:
    try:
        dt.date.fromisoformat(_nonempty(value, where))
    except ValueError as error:
        raise EvidenceError(f"{where}: invalid date") from error


def _repository_file(root: Path, relative: Any, where: str) -> Path:
    text = _nonempty(relative, where)
    pure = PurePosixPath(text)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise EvidenceError(f"{where}: path must be normalized and repository-relative: {text}")
    path = (root / Path(*pure.parts)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise EvidenceError(f"{where}: path escapes repository: {text}") from error
    if not path.is_file():
        raise EvidenceError(f"{where}: missing regular file: {text}")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _files(root: Path, value: Any, where: str) -> None:
    if not isinstance(value, list) or not value:
        raise EvidenceError(f"{where}: expected at least one file")
    seen: set[str] = set()
    for index, raw in enumerate(value):
        item_where = f"{where}[{index}]"
        item = _mapping(raw, FILE_FIELDS, item_where)
        relative = _nonempty(item["path"], f"{item_where}.path")
        if relative in seen:
            raise EvidenceError(f"{where}: duplicate path: {relative}")
        seen.add(relative)
        expected = _nonempty(item["digest"], f"{item_where}.digest")
        if not DIGEST.fullmatch(expected):
            raise EvidenceError(f"{item_where}.digest: expected sha256:<64 lowercase hex>")
        path = _repository_file(root, relative, f"{item_where}.path")
        actual = sha256(path)
        if actual != expected:
            raise EvidenceError(f"{item_where}: digest mismatch for {relative}: {actual}")


def validate_evidence(root: Path, path: Path, task_ids: set[str]) -> dict[str, Any]:
    record = _mapping(_load_json(path), EVIDENCE_FIELDS, str(path))
    if record["schema"] != "rust-beam/evidence/v1":
        raise EvidenceError(f"{path}.schema: unsupported schema")
    if not isinstance(record["id"], str) or not EVIDENCE_ID.fullmatch(record["id"]):
        raise EvidenceError(f"{path}.id: invalid evidence ID")
    if not isinstance(record["task"], str) or not TASK_ID.fullmatch(record["task"]):
        raise EvidenceError(f"{path}.task: invalid task ID")
    if record["task"] not in task_ids:
        raise EvidenceError(f"{path}.task: unknown plan task: {record['task']}")
    _timestamp(record["recorded_at"], f"{path}.recorded_at")
    _nonempty(record["claim"], f"{path}.claim")
    if record["classification"] not in {"scaffold", "host", "smoke", "target"}:
        raise EvidenceError(f"{path}.classification: unsupported classification")

    build = _mapping(record["build"], BUILD_FIELDS, f"{path}.build")
    if not isinstance(build["id"], str) or not BUILD_ID.fullmatch(build["id"]):
        raise EvidenceError(f"{path}.build.id: invalid build ID")
    if not isinstance(build["source_revision"], str) or not REVISION.fullmatch(build["source_revision"]):
        raise EvidenceError(f"{path}.build.source_revision: expected 40 lowercase hex")
    if not isinstance(build["source_dirty"], bool):
        raise EvidenceError(f"{path}.build.source_dirty: expected boolean")
    if ("-dirty-" in build["id"]) != build["source_dirty"]:
        raise EvidenceError(f"{path}.build: ID dirty marker disagrees with source_dirty")
    if build["id"].split("-")[1] != build["source_revision"][:12]:
        raise EvidenceError(f"{path}.build: ID revision prefix disagrees with source_revision")
    _nonempty(build["target"], f"{path}.build.target")

    command = _mapping(record["command"], COMMAND_FIELDS, f"{path}.command")
    _string_list(command["argv"], f"{path}.command.argv")
    cwd = _nonempty(command["cwd"], f"{path}.command.cwd")
    if cwd != ".":
        _repository_file(root, cwd, f"{path}.command.cwd")

    environment = _mapping(record["environment"], ENVIRONMENT_FIELDS, f"{path}.environment")
    _nonempty(environment["os"], f"{path}.environment.os")
    _nonempty(environment["architecture"], f"{path}.environment.architecture")
    if not isinstance(environment["tools"], list) or not environment["tools"]:
        raise EvidenceError(f"{path}.environment.tools: expected a non-empty array")
    names: set[str] = set()
    for index, raw_tool in enumerate(environment["tools"]):
        tool_where = f"{path}.environment.tools[{index}]"
        tool = _mapping(raw_tool, TOOL_FIELDS, tool_where)
        name = _nonempty(tool["name"], f"{tool_where}.name")
        _nonempty(tool["version"], f"{tool_where}.version")
        if name in names:
            raise EvidenceError(f"{path}.environment.tools: duplicate tool: {name}")
        names.add(name)

    _files(root, record["inputs"], f"{path}.inputs")
    _files(root, record["artifacts"], f"{path}.artifacts")
    result = _mapping(record["result"], RESULT_FIELDS, f"{path}.result")
    if result["status"] not in {"pass", "fail"}:
        raise EvidenceError(f"{path}.result.status: expected pass or fail")
    if not isinstance(result["exit_code"], int) or isinstance(result["exit_code"], bool):
        raise EvidenceError(f"{path}.result.exit_code: expected an integer")
    if not 0 <= result["exit_code"] <= 255:
        raise EvidenceError(f"{path}.result.exit_code: outside 0..255")
    if (result["exit_code"] == 0) != (result["status"] == "pass"):
        raise EvidenceError(f"{path}.result: status and exit_code disagree")
    return record


def _validate_source_ledger(root: Path) -> None:
    path = root / "docs/evidence/sources.json"
    ledger = _mapping(_load_json(path), {"schema", "entries"}, str(path))
    if ledger["schema"] != "rust-beam/source-claims/v1" or not isinstance(ledger["entries"], list):
        raise EvidenceError(f"{path}: unsupported schema or invalid entries")
    seen: set[str] = set()
    for index, raw in enumerate(ledger["entries"]):
        where = f"{path}.entries[{index}]"
        entry = _mapping(raw, SOURCE_FIELDS, where)
        source_id = entry["id"]
        if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
            raise EvidenceError(f"{where}.id: invalid source ID")
        if source_id in seen:
            raise EvidenceError(f"{path}: duplicate source ID: {source_id}")
        seen.add(source_id)
        for field in ("title", "locator"):
            _nonempty(entry[field], f"{where}.{field}")
        _date(entry["retrieved_on"], f"{where}.retrieved_on")
        if entry["immutable_reference"] is not None:
            _nonempty(entry["immutable_reference"], f"{where}.immutable_reference")
        if entry["digest"] is not None and (
            not isinstance(entry["digest"], str) or not DIGEST.fullmatch(entry["digest"])
        ):
            raise EvidenceError(f"{where}.digest: invalid SHA-256")
        if entry["classification"] not in {
            "specification",
            "official-documentation",
            "source",
            "prior-art",
        }:
            raise EvidenceError(f"{where}.classification: unsupported classification")
        _string_list(entry["claims"], f"{where}.claims")
        _string_list(entry["consumers"], f"{where}.consumers")
        if not isinstance(entry["limitations"], str):
            raise EvidenceError(f"{where}.limitations: expected a string")


def _validate_source_lock(root: Path) -> None:
    path = root / "toolchain/sources.lock.json"
    lock = _load_json(path)
    try:
        toolchain_contract.validate_lock(lock)
    except toolchain_contract.ToolchainError as error:
        raise EvidenceError(f"{path}: {error}") from error
    _repository_file(root, lock["policy"], f"{path}.policy")
    _timestamp(lock["sealed_at"], f"{path}.sealed_at")


def _validate_bootstrap_manifest(root: Path) -> None:
    path = root / "toolchain/bootstrap-tools.json"
    manifest = _mapping(_load_json(path), {"schema", "rust", "rustup_init", "just"}, str(path))
    if manifest["schema"] != "rust-beam/bootstrap-tools/v1":
        raise EvidenceError(f"{path}.schema: unsupported schema")
    rust = _mapping(manifest["rust"], {"channel", "source"}, f"{path}.rust")
    toolchain_path = _repository_file(root, rust["source"], f"{path}.rust.source")
    toolchain = tomllib.loads(toolchain_path.read_text(encoding="utf-8"))
    if toolchain.get("toolchain", {}).get("channel") != rust["channel"]:
        raise EvidenceError(f"{path}.rust.channel: disagrees with {rust['source']}")
    rustup = _mapping(manifest["rustup_init"], {"version", "artifacts"}, f"{path}.rustup_init")
    _nonempty(rustup["version"], f"{path}.rustup_init.version")
    if not isinstance(rustup["artifacts"], dict) or set(rustup["artifacts"]) != {
        "aarch64-unknown-linux-gnu",
        "x86_64-unknown-linux-gnu",
    }:
        raise EvidenceError(f"{path}.rustup_init.artifacts: both Linux build hosts are required")
    for host, raw in rustup["artifacts"].items():
        artifact = _mapping(raw, {"sha256"}, f"{path}.rustup_init.artifacts.{host}")
        if not isinstance(artifact["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]):
            raise EvidenceError(f"{path}.rustup_init.artifacts.{host}.sha256: invalid SHA-256")
    just = _mapping(manifest["just"], {"version", "install"}, f"{path}.just")
    version = _nonempty(just["version"], f"{path}.just.version")
    install = _nonempty(just["install"], f"{path}.just.install")
    if f"--version {version}" not in install or "--locked" not in install:
        raise EvidenceError(f"{path}.just.install: must pin the recorded version with --locked")


def _task_ids(root: Path) -> set[str]:
    index_path = root / "docs/plan/generated/index.json"
    index = _load_json(index_path)
    if not isinstance(index, dict) or not isinstance(index.get("records"), list):
        raise EvidenceError(f"{index_path}: invalid generated plan index")
    return {
        record["id"]
        for record in index["records"]
        if isinstance(record, dict) and record.get("type") in {"task", "epic", "gate"}
    }


def _phase_records(root: Path, phase: str | None) -> list[Path]:
    evidence_root = root / "docs/evidence"
    paths = sorted(evidence_root.glob("phase-*/*/evidence.json"))
    if phase is not None:
        prefix = f"phase-{phase}"
        paths = [path for path in paths if path.relative_to(evidence_root).parts[0] == prefix]
    return paths


def _validate_index(root: Path, records: list[tuple[Path, dict[str, Any]]], phase: str | None) -> None:
    path = root / "docs/evidence/index.json"
    index = _mapping(_load_json(path), {"schema", "entries"}, str(path))
    if index["schema"] != "rust-beam/evidence-index/v1" or not isinstance(index["entries"], list):
        raise EvidenceError(f"{path}: unsupported schema or invalid entries")
    entries: dict[str, dict[str, Any]] = {}
    for index_number, raw in enumerate(index["entries"]):
        where = f"{path}.entries[{index_number}]"
        entry = _mapping(raw, INDEX_FIELDS, where)
        evidence_id = _nonempty(entry["id"], f"{where}.id")
        if evidence_id in entries:
            raise EvidenceError(f"{path}: duplicate evidence ID: {evidence_id}")
        _nonempty(entry["task"], f"{where}.task")
        _repository_file(root, entry["record"], f"{where}.record")
        _nonempty(entry["claim"], f"{where}.claim")
        entries[evidence_id] = entry

    expected: set[str] = set()
    for record_path, record in records:
        expected.add(record["id"])
        entry = entries.get(record["id"])
        relative = record_path.relative_to(root).as_posix()
        if entry is None:
            raise EvidenceError(f"{path}: missing entry for {record['id']}")
        if entry != {
            "id": record["id"],
            "task": record["task"],
            "record": relative,
            "claim": record["claim"],
        }:
            raise EvidenceError(f"{path}: entry disagrees with {relative}")

    considered = {
        evidence_id
        for evidence_id, entry in entries.items()
        if phase is None or entry["record"].startswith(f"docs/evidence/phase-{phase}/")
    }
    if considered != expected:
        raise EvidenceError(f"{path}: indexed records differ from phase evidence")


def check(root: Path, phase: str | None = None) -> int:
    errors: list[str] = []
    for schema_path in sorted((root / "docs/evidence/schema").glob("*.json")):
        try:
            _load_json(schema_path)
        except EvidenceError as error:
            errors.append(str(error))
    task_ids: set[str] = set()
    try:
        task_ids = _task_ids(root)
    except EvidenceError as error:
        errors.append(str(error))

    records: list[tuple[Path, dict[str, Any]]] = []
    evidence_paths = [root / "docs/evidence/fixtures/evidence.json", *_phase_records(root, phase)]
    seen_ids: set[str] = set()
    for evidence_path in evidence_paths:
        try:
            record = validate_evidence(root, evidence_path, task_ids)
            if record["id"] in seen_ids:
                raise EvidenceError(f"duplicate evidence ID: {record['id']}")
            seen_ids.add(record["id"])
            if "fixtures" not in evidence_path.parts:
                records.append((evidence_path, record))
        except EvidenceError as error:
            errors.append(str(error))

    for validator in (_validate_source_ledger, _validate_source_lock, _validate_bootstrap_manifest):
        try:
            validator(root)
        except EvidenceError as error:
            errors.append(str(error))
    try:
        _validate_index(root, records, phase)
    except EvidenceError as error:
        errors.append(str(error))

    if errors:
        for error in sorted(errors):
            print(error, file=sys.stderr)
        return 1
    phase_label = f" for phase {phase}" if phase is not None else ""
    print(f"validated {len(evidence_paths)} evidence record(s){phase_label}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check", help="validate evidence and ledgers")
    check_parser.add_argument("--root", type=Path, default=Path.cwd())
    check_parser.add_argument("--phase")
    hash_parser = subparsers.add_parser("hash", help="print evidence SHA-256 values")
    hash_parser.add_argument("--root", type=Path, default=Path.cwd())
    hash_parser.add_argument("paths", nargs="+")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve()
    if args.command == "check":
        return check(root, args.phase)
    for relative in args.paths:
        try:
            path = _repository_file(root, relative, relative)
        except EvidenceError as error:
            print(error, file=sys.stderr)
            return 1
        print(f"{sha256(path)}  {PurePosixPath(relative)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
