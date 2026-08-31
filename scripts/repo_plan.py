#!/usr/bin/env python3
"""Generate and validate deterministic repo-plan/v1 planning records."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Iterable
from urllib.parse import unquote


SCHEMA = "repo-plan/v1"
DEFAULT_TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "repo-plan"
RECORD_DIRECTORIES = ("milestones", "tasks", "gates", "decisions")
REQUIRED_TEMPLATES = {
    "README.md.tmpl",
    "collection.README.md.tmpl",
    "decision.md.tmpl",
    "gate.md.tmpl",
    "milestone.md.tmpl",
    "project.yaml.tmpl",
    "task.md.tmpl",
}
REQUIRED_HEADINGS = {
    "task": (
        "Goal",
        "Context",
        "Deliverables",
        "Acceptance criteria",
        "Verification",
        "Evidence",
        "Out of scope",
    ),
    "epic": (
        "Goal",
        "Context",
        "Deliverables",
        "Acceptance criteria",
        "Verification",
        "Evidence",
        "Out of scope",
    ),
    "milestone": ("Outcome", "Exit criteria"),
    "gate": ("Decision", "Required evidence", "Acceptance criteria", "Decision record", "Out of scope"),
    "decision": ("Decision", "Evidence", "Residual risks", "Approver", "Authorizing commit"),
}
REQUIRED_FIELDS = {
    "task": {
        "schema", "id", "title", "type", "state", "priority", "milestone", "parent",
        "depends_on", "related", "actor", "owner", "defer_until", "evidence",
    },
    "epic": {
        "schema", "id", "title", "type", "state", "priority", "milestone", "parent",
        "depends_on", "related", "actor", "owner", "defer_until", "evidence",
    },
    "milestone": {"schema", "id", "title", "type", "order", "authorized_by"},
    "gate": {
        "schema", "id", "title", "type", "state", "priority", "milestone", "parent",
        "depends_on", "related", "actor", "owner", "defer_until", "evidence",
    },
    "decision": {"schema", "id", "title", "type", "gate", "outcome"},
}
TYPE_CODES = {"task": "T", "epic": "E", "gate": "G", "milestone": "M", "decision": "D"}


@dataclass(frozen=True)
class ValidationResult:
    records: dict[str, dict[str, Any]]
    errors: list[str]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "[]":
        return []
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"'):
        return json.loads(value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_mapping(content: str) -> dict[str, Any]:
    """Parse the constrained top-level YAML subset emitted by repo-plan."""
    metadata: dict[str, Any] = {}
    current_list: str | None = None
    for raw_line in content.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - "):
            if current_list is None:
                raise ValueError(f"list item has no key: {raw_line}")
            metadata[current_list].append(_parse_scalar(raw_line[4:]))
            continue
        if raw_line.startswith((" ", "\t")) or ":" not in raw_line:
            raise ValueError(f"unsupported YAML line: {raw_line}")
        key, raw_value = raw_line.split(":", 1)
        if raw_value.strip():
            metadata[key] = _parse_scalar(raw_value)
            current_list = None
        else:
            metadata[key] = []
            current_list = key
    return metadata


def parse_markdown(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise ValueError("record must start with YAML frontmatter")
    marker = content.find("\n---\n", 4)
    if marker < 0:
        raise ValueError("record is missing the closing frontmatter delimiter")
    metadata = parse_mapping(content[4:marker])
    return metadata, content[marker + 5 :]


def second_level_headings(body: str) -> list[str]:
    return re.findall(r"^## ([^\n]+)$", body, flags=re.MULTILINE)


def _yaml(value: str | None) -> str:
    return "null" if value is None else json.dumps(value, ensure_ascii=False)


def _render(templates: Path, name: str, values: dict[str, Any]) -> str:
    template = Template((templates / name).read_text())
    rendered = template.substitute({key: str(value) for key, value in values.items()})
    return rendered.rstrip() + "\n"


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _record_files(root: Path) -> Iterable[Path]:
    for directory in RECORD_DIRECTORIES:
        yield from sorted((root / directory).glob("*.md"))


def _canonical_digest(root: Path) -> str:
    digest = hashlib.sha256()
    files = [root / "project.yaml", *_record_files(root)]
    for path in sorted(files):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(relative + b"\0" + path.read_bytes() + b"\0")
    return f"sha256:{digest.hexdigest()}"


def _load_records(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _record_files(root):
        if path.name == "README.md":
            continue
        metadata, _ = parse_markdown(path.read_text())
        records.append({**metadata, "path": path.relative_to(root).as_posix()})
    return sorted(records, key=lambda record: str(record["id"]))


def validate_templates(templates: Path = DEFAULT_TEMPLATES) -> list[str]:
    if not templates.exists():
        return [f"template directory is missing: {templates}"]
    present = {path.name for path in templates.glob("*.tmpl")}
    return [f"missing template: {name}" for name in sorted(REQUIRED_TEMPLATES - present)]


def _load_plan(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    errors = validate_templates()
    project_path = root / "project.yaml"
    if not project_path.exists():
        return {}, {}, [*errors, f"missing required file: {project_path}"]
    try:
        project = parse_mapping(project_path.read_text())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {}, {}, [*errors, f"{project_path}: {error}"]

    records: dict[str, dict[str, Any]] = {}
    for path in _record_files(root):
        if path.name == "README.md":
            continue
        try:
            metadata, body = parse_markdown(path.read_text())
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue
        record_id = str(metadata.get("id", ""))
        if not record_id:
            errors.append(f"{path}: missing field: id")
            continue
        if record_id in records:
            errors.append(f"{path}: duplicate id: {record_id}")
            continue
        records[record_id] = {
            **metadata,
            "path": path.relative_to(root).as_posix(),
            "body": body,
        }
    return project, records, errors


def _find_cycles(records: dict[str, dict[str, Any]], field: str) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    active: list[str] = []

    def neighbors(record_id: str) -> list[str]:
        value = records[record_id].get(field)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def visit(record_id: str) -> None:
        if record_id in active:
            start = active.index(record_id)
            cycle = active[start:] + [record_id]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if record_id in visited:
            return
        active.append(record_id)
        for target in neighbors(record_id):
            if target in records:
                visit(target)
        active.pop()
        visited.add(record_id)

    for record_id in sorted(records):
        visit(record_id)
    return cycles


def _validate_headings(record: dict[str, Any], errors: list[str]) -> None:
    required = REQUIRED_HEADINGS.get(str(record.get("type")), ())
    headings = second_level_headings(str(record.get("body", "")))
    for heading in required:
        if heading not in headings:
            errors.append(f"{record['path']}: missing required heading: {heading}")
    positions = [headings.index(heading) for heading in required if heading in headings]
    if positions != sorted(positions):
        errors.append(f"{record['path']}: required headings are out of order")


def _validate_links(root: Path, record: dict[str, Any], errors: list[str]) -> None:
    source = root / str(record["path"])
    pattern = re.compile(r"\[[^\]]*\]\((?:<([^>]+)>|([^\)]+))\)")
    for angle, plain in pattern.findall(str(record.get("body", ""))):
        target = (angle or plain).strip()
        if re.match(r"^(?:https?:|mailto:|#)", target):
            continue
        target_path = unquote(target.split("#", 1)[0])
        if target_path and not (source.parent / target_path).resolve().exists():
            errors.append(f"{record['path']}: broken local link: {target}")


def validate_plan(root: Path) -> ValidationResult:
    project, records, errors = _load_plan(root)
    if project.get("schema") != SCHEMA:
        errors.append(f"project.yaml: schema must be {SCHEMA}")
    prefix = str(project.get("prefix", ""))
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,7}", prefix):
        errors.append("project.yaml: prefix must contain 2-8 uppercase letters or digits and start with a letter")
    if not isinstance(project.get("name"), str) or not project.get("name"):
        errors.append("project.yaml: name must be a non-empty string")
    if set(project) - {"schema", "name", "prefix"}:
        errors.append("project.yaml: unknown fields: " + ", ".join(sorted(set(project) - {"schema", "name", "prefix"})))

    for record_id, record in records.items():
        path = str(record["path"])
        record_type = str(record.get("type", ""))
        if record_type not in REQUIRED_FIELDS:
            errors.append(f"{path}: invalid type: {record_type}")
            continue
        required = REQUIRED_FIELDS[record_type]
        missing = sorted(required - set(record))
        for field in missing:
            errors.append(f"{path}: missing field: {field}")
        known = required | {"path", "body"}
        unknown = sorted(key for key in record if key not in known and not key.startswith("x_"))
        if unknown:
            errors.append(f"{path}: unknown fields: {', '.join(unknown)}")
        if record.get("schema") != SCHEMA:
            errors.append(f"{path}: schema must be {SCHEMA}")

        code = TYPE_CODES[record_type]
        token_length = "{1,12}" if record_type == "milestone" else "{4,12}"
        if not re.fullmatch(rf"{re.escape(prefix)}-{code}-[A-Z0-9]{token_length}", record_id):
            errors.append(f"{path}: invalid id for {record_type}: {record_id}")
        if Path(path).stem != record_id.lower():
            errors.append(f"{path}: filename must be {record_id.lower()}.md")

        expected_directory = "tasks" if record_type in {"task", "epic"} else f"{record_type}s"
        if Path(path).parent.as_posix() != expected_directory:
            errors.append(f"{path}: {record_type} must be stored in {expected_directory}/")
        _validate_headings(record, errors)
        _validate_links(root, record, errors)

        for field in ("depends_on", "related", "evidence"):
            if field in record and not isinstance(record[field], list):
                errors.append(f"{path}: {field} must be a list")
        if record_type in {"task", "epic", "gate"}:
            if record.get("state") not in {"open", "in_progress", "done", "cancelled"}:
                errors.append(f"{path}: invalid state: {record.get('state')}")
            if record.get("priority") not in {"P0", "P1", "P2", "P3", "P4"}:
                errors.append(f"{path}: invalid priority: {record.get('priority')}")
            expected_actor = "human" if record_type == "gate" else "agent"
            if record.get("actor") != expected_actor:
                errors.append(f"{path}: {record_type} actor must be {expected_actor}")
            if record.get("state") == "in_progress" and not record.get("owner"):
                errors.append(f"{path}: in_progress record requires owner")
            if record.get("state") != "in_progress" and record.get("owner") is not None:
                errors.append(f"{path}: owner must be null unless state is in_progress")
            deferred = record.get("defer_until")
            if deferred is not None:
                try:
                    dt.date.fromisoformat(str(deferred))
                except ValueError:
                    errors.append(f"{path}: defer_until must be an ISO date or null")
        if record_type == "milestone" and not isinstance(record.get("order"), int):
            errors.append(f"{path}: order must be an integer")
        if record_type == "decision" and record.get("outcome") not in {"approved", "rejected"}:
            errors.append(f"{path}: outcome must be approved or rejected")

    for record_id, record in records.items():
        path = str(record["path"])
        record_type = record.get("type")
        for field in ("depends_on", "related"):
            value = record.get(field, [])
            if not isinstance(value, list):
                continue
            for target in value:
                if target == record_id:
                    errors.append(f"{path}: {field} cannot reference itself")
                elif target not in records:
                    errors.append(f"{path}: {field} references missing record {target}")
        if record_type in {"task", "epic", "gate"}:
            milestone = record.get("milestone")
            if milestone not in records:
                errors.append(f"{path}: milestone references missing record {milestone}")
            elif records[milestone].get("type") != "milestone":
                errors.append(f"{path}: milestone must reference a milestone")
            parent = record.get("parent")
            if parent is not None:
                if parent not in records:
                    errors.append(f"{path}: parent references missing record {parent}")
                elif records[parent].get("type") != "epic":
                    errors.append(f"{path}: parent must reference an epic")
        if record_type == "milestone":
            gate = record.get("authorized_by")
            if gate is not None:
                if gate not in records:
                    errors.append(f"{path}: authorized_by references missing record {gate}")
                elif records[gate].get("type") != "gate":
                    errors.append(f"{path}: authorized_by must reference a gate")
        if record_type == "decision":
            gate = record.get("gate")
            if gate not in records:
                errors.append(f"{path}: gate references missing record {gate}")
            elif records[gate].get("type") != "gate":
                errors.append(f"{path}: gate must reference a gate")

        dependencies = record.get("depends_on", [])
        if record.get("state") == "done" and isinstance(dependencies, list):
            unfinished = [item for item in dependencies if item in records and records[item].get("state") != "done"]
            if unfinished:
                errors.append(f"{path}: done record has unfinished dependencies: {', '.join(unfinished)}")
        if record_type == "task" and record.get("state") == "done" and not record.get("evidence"):
            errors.append(f"{path}: done task requires evidence")

    children: dict[str, list[dict[str, Any]]] = {}
    for record in records.values():
        if record.get("parent"):
            children.setdefault(str(record["parent"]), []).append(record)
    decisions: dict[str, list[dict[str, Any]]] = {}
    for record in records.values():
        if record.get("type") == "decision":
            decisions.setdefault(str(record.get("gate")), []).append(record)
    for record_id, record in records.items():
        if record.get("type") == "epic" and record.get("state") == "done":
            unfinished = [
                child["id"] for child in children.get(record_id, [])
                if child.get("state") not in {"done", "cancelled"}
            ]
            if unfinished:
                errors.append(f"{record['path']}: done epic has unfinished children: {', '.join(sorted(unfinished))}")
        if record.get("type") == "gate" and record.get("state") == "done":
            if len(decisions.get(record_id, [])) != 1:
                errors.append(f"{record['path']}: done gate requires exactly one decision")

    for field in ("depends_on", "parent"):
        for cycle in _find_cycles(records, field):
            errors.append(f"{field} cycle: {' -> '.join(cycle)}")
    return ValidationResult(records=records, errors=sorted(set(errors)))


def compute_ready(records: dict[str, dict[str, Any]], evaluation_date: str | None) -> list[dict[str, Any]]:
    today = dt.date.fromisoformat(evaluation_date) if evaluation_date else None
    approved_gates = {
        str(record.get("gate"))
        for record in records.values()
        if record.get("type") == "decision" and record.get("outcome") == "approved"
    }
    milestones = {record_id: record for record_id, record in records.items() if record.get("type") == "milestone"}
    reverse: dict[str, set[str]] = {}
    for record_id, record in records.items():
        for dependency in record.get("depends_on", []) if isinstance(record.get("depends_on", []), list) else []:
            reverse.setdefault(str(dependency), set()).add(record_id)

    def downstream_count(record_id: str) -> int:
        seen: set[str] = set()
        pending = list(reverse.get(record_id, set()))
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            pending.extend(reverse.get(target, set()))
        return sum(
            1 for target in seen
            if records[target].get("type") == "task" and records[target].get("state") not in {"done", "cancelled"}
        )

    ready: list[dict[str, Any]] = []
    for record_id, record in records.items():
        if record.get("type") != "task" or record.get("state") != "open" or record.get("actor") != "agent":
            continue
        deferred = record.get("defer_until")
        if deferred is not None and (today is None or dt.date.fromisoformat(str(deferred)) > today):
            continue
        dependencies = record.get("depends_on", [])
        if not isinstance(dependencies, list) or any(
            dependency not in records or records[dependency].get("state") != "done" for dependency in dependencies
        ):
            continue
        milestone = milestones.get(str(record.get("milestone")))
        if milestone is None:
            continue
        gate_id = milestone.get("authorized_by")
        if gate_id is not None:
            gate = records.get(str(gate_id))
            if gate is None or gate.get("state") != "done" or gate_id not in approved_gates:
                continue
        ready.append(
            {
                "id": record_id,
                "path": record["path"],
                "priority": record["priority"],
                "milestone": record["milestone"],
                "milestone_order": milestone["order"],
                "incomplete_downstream": downstream_count(record_id),
                "reason": "open; milestone authorized; all dependencies done",
            }
        )
    ready.sort(
        key=lambda item: (
            int(str(item["priority"])[1:]),
            item["milestone_order"],
            -item["incomplete_downstream"],
            item["id"],
        )
    )
    return ready


def _projection_values(
    root: Path,
    records: dict[str, dict[str, Any]],
    evaluation_date: str | None,
) -> dict[str, dict[str, Any]]:
    source_digest = _canonical_digest(root)
    indexed_records = []
    for record_id in sorted(records):
        record = records[record_id]
        indexed_records.append({key: value for key, value in record.items() if key != "body"})
    index = {"schema": SCHEMA, "source_digest": source_digest, "records": indexed_records}
    edges: list[dict[str, str]] = []
    for record_id, record in records.items():
        for dependency in record.get("depends_on", []):
            edges.append({"type": "depends_on", "from": record_id, "to": dependency})
        for related in record.get("related", []):
            edges.append({"type": "related", "from": record_id, "to": related})
        if record.get("parent") is not None:
            edges.append({"type": "parent", "from": record_id, "to": record["parent"]})
        if record.get("type") == "milestone" and record.get("authorized_by") is not None:
            edges.append({"type": "authorized_by", "from": record_id, "to": record["authorized_by"]})
    graph = {
        "schema": SCHEMA,
        "source_digest": source_digest,
        "nodes": [
            {"id": record_id, "type": records[record_id]["type"]}
            for record_id in sorted(records)
        ],
        "edges": sorted(edges, key=lambda edge: (edge["type"], edge["from"], edge["to"])),
    }
    ready = {
        "schema": SCHEMA,
        "source_digest": source_digest,
        "date": evaluation_date,
        "tasks": compute_ready(records, evaluation_date),
    }
    return {"index.json": index, "graph.json": graph, "ready.json": ready}


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def build_plan(root: Path, evaluation_date: str | None = None) -> None:
    """Validate canonical inputs and write deterministic projections."""
    result = validate_plan(root)
    if result.errors:
        raise ValueError("plan is invalid:\n" + "\n".join(result.errors))
    generated = root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    for name, value in _projection_values(root, result.records, evaluation_date).items():
        (generated / name).write_bytes(_json_bytes(value))


def check_plan(root: Path, evaluation_date: str | None) -> ValidationResult:
    result = validate_plan(root)
    errors = list(result.errors)
    try:
        expected = _projection_values(root, result.records, evaluation_date)
    except (KeyError, TypeError, ValueError):
        expected = {}
    for name, value in expected.items():
        path = root / "generated" / name
        if not path.exists():
            errors.append(f"generated/{name} is missing")
        elif path.read_bytes() != _json_bytes(value):
            errors.append(f"generated/{name} is stale")
    return ValidationResult(records=result.records, errors=sorted(set(errors)))


def create_record(
    *,
    root: Path,
    record_type: str,
    record_id: str,
    title: str,
    templates: Path = DEFAULT_TEMPLATES,
    milestone: str | None = None,
    priority: str = "P2",
    parent: str | None = None,
    order: int = 0,
    authorized_by: str | None = None,
    gate: str | None = None,
    outcome: str = "approved",
) -> Path:
    if not title or "\n" in title:
        raise ValueError("title must be a non-empty single line")
    if record_type in {"task", "epic"}:
        directory, template_name = "tasks", "task.md.tmpl"
    elif record_type in {"milestone", "gate", "decision"}:
        directory = f"{record_type}s"
        template_name = f"{record_type}.md.tmpl"
    else:
        raise ValueError(f"unsupported record type: {record_type}")

    values = {
        "id": record_id,
        "id_yaml": _yaml(record_id),
        "title": title,
        "title_yaml": _yaml(title),
        "type_yaml": _yaml(record_type),
        "milestone_yaml": _yaml(milestone),
        "priority_yaml": _yaml(priority),
        "parent_yaml": _yaml(parent),
        "order": order,
        "authorized_by_yaml": _yaml(authorized_by),
        "gate_yaml": _yaml(gate),
        "outcome_yaml": _yaml(outcome),
    }
    destination = root / directory / f"{record_id.lower()}.md"
    _write_new(destination, _render(templates, template_name, values))
    return destination


def initialize_plan(
    *,
    root: Path,
    name: str,
    prefix: str,
    milestone_id: str,
    milestone_title: str,
    templates: Path = DEFAULT_TEMPLATES,
) -> None:
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"destination is non-empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    _write_new(
        root / "README.md",
        _render(templates, "README.md.tmpl", {"project_name": name}),
    )
    _write_new(
        root / "project.yaml",
        _render(
            templates,
            "project.yaml.tmpl",
            {"project_name_yaml": _yaml(name), "prefix_yaml": _yaml(prefix)},
        ),
    )
    collection_descriptions = {
        "tasks": "Canonical task and epic records. Use the generator to add records.",
        "gates": "Canonical human authorization gates. Agents may prepare but not pass gates.",
        "decisions": "Immutable human decisions that complete gates.",
    }
    for directory, description in collection_descriptions.items():
        _write_new(
            root / directory / "README.md",
            _render(
                templates,
                "collection.README.md.tmpl",
                {"collection_title": directory.title(), "collection_description": description},
            ),
        )
    create_record(
        root=root,
        record_type="milestone",
        record_id=milestone_id,
        title=milestone_title,
        order=0,
        templates=templates,
    )
    build_plan(root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create a complete repo-plan/v1 tree")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--prefix", required=True)
    init.add_argument("--milestone-id", required=True)
    init.add_argument("--milestone-title", required=True)

    new = subparsers.add_parser("new", help="create one canonical record")
    new.add_argument("record_type", choices=("task", "epic", "milestone", "gate", "decision"))
    new.add_argument("--root", type=Path, required=True)
    new.add_argument("--id", required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--milestone")
    new.add_argument("--priority", default="P2")
    new.add_argument("--parent")
    new.add_argument("--order", type=int, default=0)
    new.add_argument("--authorized-by")
    new.add_argument("--gate")
    new.add_argument("--outcome", choices=("approved", "rejected"), default="approved")

    build = subparsers.add_parser("build", help="rebuild deterministic projections")
    build.add_argument("--root", type=Path, required=True)
    build.add_argument("--date")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            initialize_plan(
                root=args.root,
                name=args.name,
                prefix=args.prefix,
                milestone_id=args.milestone_id,
                milestone_title=args.milestone_title,
            )
            print(f"initialized {args.root}")
        elif args.command == "new":
            destination = create_record(
                root=args.root,
                record_type=args.record_type,
                record_id=args.id,
                title=args.title,
                milestone=args.milestone,
                priority=args.priority,
                parent=args.parent,
                order=args.order,
                authorized_by=args.authorized_by,
                gate=args.gate,
                outcome=args.outcome,
            )
            print(destination)
        elif args.command == "build":
            build_plan(args.root, evaluation_date=args.date)
            print(f"rebuilt {args.root / 'generated'}")
    except (FileExistsError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
