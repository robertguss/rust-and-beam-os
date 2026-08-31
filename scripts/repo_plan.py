#!/usr/bin/env python3
"""Generate and validate deterministic repo-plan/v1 planning records."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from string import Template
from typing import Any, Iterable


SCHEMA = "repo-plan/v1"
DEFAULT_TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "repo-plan"
RECORD_DIRECTORIES = ("milestones", "tasks", "gates", "decisions")


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


def build_plan(root: Path, evaluation_date: str | None = None) -> None:
    """Write deterministic projections. Semantic validation is a later slice."""
    records = _load_records(root)
    source_digest = _canonical_digest(root)
    index = {"schema": SCHEMA, "source_digest": source_digest, "records": records}
    graph = {
        "schema": SCHEMA,
        "source_digest": source_digest,
        "nodes": [{"id": record["id"], "type": record["type"]} for record in records],
        "edges": [],
    }
    ready = {"schema": SCHEMA, "source_digest": source_digest, "date": evaluation_date, "tasks": []}
    generated = root / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    for name, value in (("index.json", index), ("graph.json", graph), ("ready.json", ready)):
        (generated / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


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
