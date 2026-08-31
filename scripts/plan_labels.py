#!/usr/bin/env python3
"""Project gate-aware tracker labels from the canonical repository plan."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

MANAGED_LABELS = {
    "cancelled",
    "dependency-blocked",
    "done",
    "gate-blocked",
    "in-progress",
    "ready-for-agent",
    "ready-for-human",
    "scheduled",
    "tracking",
}


class LabelProjectionError(ValueError):
    """Raised when generated plan data cannot produce an unambiguous label."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LabelProjectionError(f"{path}: cannot read JSON: {error}") from error
    if not isinstance(value, dict):
        raise LabelProjectionError(f"{path}: expected an object")
    return value


def _approved_gates(records: dict[str, dict[str, Any]]) -> set[str]:
    approved = {
        record["gate"]
        for record in records.values()
        if record.get("type") == "decision" and record.get("outcome") == "approved"
    }
    return {
        gate_id
        for gate_id in approved
        if records.get(gate_id, {}).get("type") == "gate"
        and records[gate_id].get("state") == "done"
    }


def project(root: Path, today: dt.date | None = None) -> dict[str, Any]:
    index_path = root / "generated/index.json"
    ready_path = root / "generated/ready.json"
    index = _load(index_path)
    ready = _load(ready_path)
    raw_records = index.get("records")
    raw_ready = ready.get("tasks")
    if not isinstance(raw_records, list) or not isinstance(raw_ready, list):
        raise LabelProjectionError("generated plan index or ready projection has invalid arrays")
    if index.get("source_digest") != ready.get("source_digest"):
        raise LabelProjectionError("generated plan index and ready projection have different source digests")
    if today is None:
        today = dt.date.today()

    records: dict[str, dict[str, Any]] = {}
    for record in raw_records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise LabelProjectionError("generated plan contains a record without an ID")
        records[record["id"]] = record
    ready_ids = {
        item["id"]
        for item in raw_ready
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    approved_gates = _approved_gates(records)

    projections: list[dict[str, Any]] = []
    for record_id in sorted(records):
        record = records[record_id]
        if record.get("type") not in {"task", "epic", "gate"}:
            continue
        labels: set[str] = set()
        reasons: list[str] = []
        if record.get("type") == "epic":
            labels.add("tracking")

        state = record.get("state")
        if state == "done":
            labels.add("done")
            reasons.append("canonical state is done")
        elif state == "cancelled":
            labels.add("cancelled")
            reasons.append("canonical state is cancelled")
        elif state == "in_progress":
            labels.add("in-progress")
            reasons.append(f"owned by {record.get('owner')}")
        elif state == "open":
            deferred = record.get("defer_until")
            if isinstance(deferred, str) and dt.date.fromisoformat(deferred) > today:
                labels.add("scheduled")
                reasons.append(f"deferred until {deferred}")
            else:
                milestone = records.get(str(record.get("milestone")), {})
                authorizing_gate = milestone.get("authorized_by")
                if authorizing_gate is not None and authorizing_gate not in approved_gates:
                    labels.add("gate-blocked")
                    reasons.append(f"milestone awaits approved {authorizing_gate}")
                else:
                    incomplete = [
                        dependency
                        for dependency in record.get("depends_on", [])
                        if records.get(dependency, {}).get("state") != "done"
                    ]
                    if incomplete:
                        labels.add("dependency-blocked")
                        reasons.append("incomplete dependencies: " + ", ".join(incomplete))
                    elif record.get("type") == "epic":
                        reasons.append("tracking records are never executable")
                    elif record.get("actor") == "human":
                        labels.add("ready-for-human")
                        reasons.append("authorized with complete dependencies")
                    elif record_id in ready_ids:
                        labels.add("ready-for-agent")
                        reasons.append("present in generated ready projection")
                    else:
                        raise LabelProjectionError(
                            f"{record_id}: open authorized agent task with complete dependencies is absent from ready"
                        )
        else:
            raise LabelProjectionError(f"{record_id}: unsupported state: {state}")

        projections.append(
            {
                "id": record_id,
                "path": record.get("path"),
                "labels": sorted(labels),
                "reason": "; ".join(reasons),
            }
        )

    return {
        "schema": "rust-beam/plan-label-projection/v1",
        "source_digest": index.get("source_digest"),
        "managed_labels": sorted(MANAGED_LABELS),
        "records": projections,
    }


def check(root: Path) -> int:
    try:
        projection = project(root)
    except (LabelProjectionError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    ready = _load(root / "generated/ready.json")
    ready_ids = {item["id"] for item in ready["tasks"]}
    projected_ready = {
        record["id"]
        for record in projection["records"]
        if "ready-for-agent" in record["labels"]
    }
    if ready_ids != projected_ready:
        print("ready-for-agent label projection disagrees with generated ready tasks", file=sys.stderr)
        return 1
    print(f"validated gate-aware labels for {len(projection['records'])} executable records")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "project"))
    parser.add_argument("--root", type=Path, default=Path("docs/plan"))
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve()
    if args.command == "check":
        return check(root)
    try:
        value = project(root)
    except (LabelProjectionError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
