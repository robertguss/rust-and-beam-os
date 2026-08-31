#!/usr/bin/env python3
"""Build and validate the repository-native implementation plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


FRONT_MATTER_ORDER = (
    "id",
    "linear_id",
    "linear_url",
    "title",
    "milestone",
    "kind",
    "status",
    "priority",
    "parent",
    "labels",
    "blocked_by",
    "blocks",
)

REQUIRED_FIELDS = {
    "id",
    "title",
    "milestone",
    "kind",
    "status",
    "priority",
    "parent",
    "labels",
    "blocked_by",
    "blocks",
}


@dataclass(frozen=True)
class ValidationResult:
    records: dict[str, dict[str, Any]]
    errors: list[str]


def _render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith(('"', "'")):
        return json.loads(value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def render_markdown(metadata: dict[str, Any], body: str) -> str:
    """Render the constrained YAML front matter used by plan documents."""
    keys = [key for key in FRONT_MATTER_ORDER if key in metadata]
    keys.extend(sorted(set(metadata) - set(keys)))
    lines = ["---"]
    for key in keys:
        value = metadata[key]
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {_render_scalar(item)}" for item in value)
        else:
            lines.append(f"{key}: {_render_scalar(value)}")
    lines.extend(("---", ""))
    return "\n".join(lines) + body


def parse_markdown(content: str) -> tuple[dict[str, Any], str]:
    """Parse plan Markdown without requiring a third-party YAML package."""
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("plan Markdown must start with YAML front matter")

    end = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise ValueError("plan Markdown is missing the closing front matter delimiter")

    metadata: dict[str, Any] = {}
    current_list: str | None = None
    for raw_line in lines[1:end]:
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"list item has no key: {line}")
            metadata[current_list].append(_parse_scalar(line[4:]))
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"unsupported front matter line: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not raw_value.strip():
            metadata[key] = []
            current_list = key
        else:
            metadata[key] = _parse_scalar(raw_value)
            current_list = None

    body = "".join(lines[end + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    return metadata, body


def _plan_files(root: Path) -> Iterable[Path]:
    for directory in (root / "tasks", root / "gates"):
        if directory.exists():
            yield from sorted(directory.glob("*.md"))


def _natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def load_records(root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path in _plan_files(root):
        try:
            metadata, body = parse_markdown(path.read_text())
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue

        missing = sorted(REQUIRED_FIELDS - set(metadata))
        if missing:
            errors.append(f"{path}: missing fields {', '.join(missing)}")
            continue
        task_id = str(metadata["id"])
        if task_id in records:
            errors.append(f"{path}: duplicate task id {task_id}")
            continue
        metadata["path"] = path.relative_to(root).as_posix()
        metadata["body"] = body
        records[task_id] = metadata
    return records, errors


def _find_cycles(records: dict[str, dict[str, Any]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(task_id: str) -> None:
        if task_id in active:
            start = active.index(task_id)
            cycle = active[start:] + [task_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if task_id in visited:
            return
        active.append(task_id)
        for dependency in records[task_id].get("blocked_by", []):
            if dependency in records:
                visit(dependency)
        active.pop()
        visited.add(task_id)

    for task_id in sorted(records, key=_natural_key):
        visit(task_id)
    return cycles


def validate_plan(root: Path) -> ValidationResult:
    records, errors = load_records(root)

    for task_id, record in records.items():
        for field in ("blocked_by", "blocks"):
            if not isinstance(record[field], list):
                errors.append(f"{task_id}: {field} must be a list")
                continue
            for related_id in record[field]:
                if related_id not in records:
                    errors.append(f"{task_id}: {field} references missing task {related_id}")

        parent = record.get("parent")
        if parent is not None and parent not in records:
            errors.append(f"{task_id}: parent references missing task {parent}")

        milestone = str(record.get("milestone", ""))
        kind = record.get("kind")
        status = record.get("status")
        labels = set(record.get("labels", []))
        if kind == "gate" and status != "ready-for-human":
            errors.append(f"{task_id}: gates must have ready-for-human status")
        if kind != "gate" and re.fullmatch(r"M[1-6]", milestone) and status != "gate-blocked":
            errors.append(f"{task_id}: M1-M6 work must remain gate-blocked")
        if kind == "tracking" and ("tracking" not in labels or "ready-for-agent" in labels):
            errors.append(f"{task_id}: tracking issues require tracking and cannot be ready-for-agent")

    for task_id, record in records.items():
        for dependency in record.get("blocked_by", []):
            if dependency in records and task_id not in records[dependency].get("blocks", []):
                errors.append(f"{task_id}: blocked_by {dependency} is not mirrored by its blocks list")
        for downstream in record.get("blocks", []):
            if downstream in records and task_id not in records[downstream].get("blocked_by", []):
                errors.append(f"{task_id}: blocks {downstream} is not mirrored by its blocked_by list")

    for cycle in _find_cycles(records):
        errors.append(f"dependency cycle: {' -> '.join(cycle)}")

    return ValidationResult(records=records, errors=sorted(set(errors)))


def build_index(records: dict[str, dict[str, Any]], exported_at: str) -> dict[str, Any]:
    fields = (
        "id",
        "linear_id",
        "title",
        "milestone",
        "kind",
        "status",
        "priority",
        "parent",
        "blocked_by",
        "blocks",
        "path",
    )
    tasks = [
        {key: record.get(key) for key in fields if key in record}
        for _, record in sorted(records.items(), key=lambda item: _natural_key(item[0]))
    ]
    return {
        "schema_version": 1,
        "exported_at": exported_at,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def _canonical_id(title: str) -> str:
    task_id = title.split(" — ", 1)[0].strip()
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+[a-z]?", task_id):
        raise ValueError(f"cannot derive canonical id from title: {title}")
    return task_id


def _milestone_id(name: str) -> str:
    milestone = name.split(" — ", 1)[0].strip()
    if not re.fullmatch(r"M\d+", milestone):
        raise ValueError(f"cannot derive milestone id from name: {name}")
    return milestone


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _write_generated_markdown(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_body = body.rstrip() + "\n"
    path.write_text(render_markdown(metadata, normalized_body))


def _clear_generated_markdown(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.md"):
        path.unlink()


def _issue_kind(task_id: str, labels: list[str]) -> str:
    if task_id.startswith("GATE-"):
        return "gate"
    if task_id.startswith("AUDIT-"):
        return "audit"
    if "tracking" in labels:
        return "tracking"
    return "implementation"


def _issue_status(labels: list[str]) -> str:
    for status in ("ready-for-agent", "ready-for-human", "gate-blocked", "spec-complete"):
        if status in labels:
            return "gate-blocked" if status == "spec-complete" else status
    return "backlog"


def import_snapshot(snapshot: dict[str, Any], root: Path) -> None:
    """Materialize a normalized repository plan from a complete Linear snapshot."""
    exported_at = str(snapshot["exported_at"])
    project = snapshot["project"]
    issues = snapshot["issues"]

    for directory in (root / "tasks", root / "gates", root / "milestones"):
        _clear_generated_markdown(directory)

    _write_generated_markdown(
        root / "project.md",
        {
            "title": project["name"],
            "kind": "project",
            "linear_url": project.get("url"),
            "exported_at": exported_at,
        },
        project.get("description") or project.get("summary") or "",
    )

    document_paths: dict[str, Path] = {}
    for document in snapshot.get("documents", []):
        title = document["title"]
        if "Architecture" in title:
            destination = root / "architecture.md"
        elif "Readiness" in title or "Remediation" in title:
            destination = root / "readiness-review.md"
        else:
            destination = root / "documents" / f"{_slug(title)}.md"
        document_paths[title] = destination
        _write_generated_markdown(
            destination,
            {
                "title": title,
                "kind": "document",
                "linear_url": document.get("url"),
                "exported_at": exported_at,
            },
            document.get("content", ""),
        )

    for milestone in snapshot.get("milestones", []):
        milestone_id = _milestone_id(milestone["name"])
        _write_generated_markdown(
            root / "milestones" / f"{milestone_id.lower()}.md",
            {
                "id": milestone_id,
                "title": milestone["name"],
                "kind": "milestone",
                "exported_at": exported_at,
            },
            milestone.get("description", ""),
        )

    linear_to_canonical = {issue["id"]: _canonical_id(issue["title"]) for issue in issues}
    for issue in issues:
        task_id = linear_to_canonical[issue["id"]]
        labels = list(issue.get("labels", []))
        kind = _issue_kind(task_id, labels)
        milestone = _milestone_id(issue["milestone"])
        parent_id = issue.get("parent_id")
        metadata = {
            "id": task_id,
            "linear_id": issue["id"],
            "linear_url": issue.get("url"),
            "title": issue["title"].split(" — ", 1)[-1].strip(),
            "milestone": milestone,
            "kind": kind,
            "status": _issue_status(labels),
            "priority": _slug(issue.get("priority", "none")).replace("no-priority", "none"),
            "parent": linear_to_canonical.get(parent_id) if parent_id else None,
            "labels": labels,
            "blocked_by": [linear_to_canonical[item] for item in issue.get("blocked_by", [])],
            "blocks": [linear_to_canonical[item] for item in issue.get("blocks", [])],
        }
        directory = "gates" if kind == "gate" else "tasks"
        _write_generated_markdown(
            root / directory / f"{task_id.lower()}.md",
            metadata,
            issue.get("description", ""),
        )

    result = validate_plan(root)
    if result.errors:
        raise ValueError("snapshot produced an invalid plan:\n" + "\n".join(result.errors))
    index = build_index(result.records, exported_at=exported_at)
    (root / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")


def _command_validate(args: argparse.Namespace) -> int:
    result = validate_plan(args.root)
    if result.errors:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(result.records)} plan records")
    return 0


def _command_build_index(args: argparse.Namespace) -> int:
    result = validate_plan(args.root)
    if result.errors:
        for error in result.errors:
            print(error, file=sys.stderr)
        return 1
    index = build_index(result.records, exported_at=args.exported_at)
    destination = args.root / "index.json"
    destination.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {destination} with {len(result.records)} records")
    return 0


def _command_import_snapshot(args: argparse.Namespace) -> int:
    if str(args.snapshot) == "-":
        snapshot = json.load(sys.stdin)
    else:
        snapshot = json.loads(args.snapshot.read_text())
    import_snapshot(snapshot, args.root)
    print(f"imported {len(snapshot['issues'])} issues into {args.root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate plan task files")
    validate.add_argument("--root", type=Path, default=Path("docs/plan"))
    validate.set_defaults(handler=_command_validate)

    index = subparsers.add_parser("build-index", help="validate and rebuild index.json")
    index.add_argument("--root", type=Path, default=Path("docs/plan"))
    index.add_argument("--exported-at", required=True)
    index.set_defaults(handler=_command_build_index)

    snapshot = subparsers.add_parser("import-snapshot", help="materialize a complete Linear snapshot")
    snapshot.add_argument("snapshot", type=Path, help="snapshot JSON path or - for stdin")
    snapshot.add_argument("--root", type=Path, default=Path("docs/plan"))
    snapshot.set_defaults(handler=_command_import_snapshot)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
