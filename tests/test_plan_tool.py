import argparse
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import plan_tool


class FrontMatterTests(unittest.TestCase):
    def test_round_trips_emitted_front_matter(self):
        metadata = {
            "id": "P1-00",
            "linear_id": "ROB-801",
            "title": "Freeze IRQ invariants",
            "milestone": "M1",
            "kind": "implementation",
            "status": "gate-blocked",
            "priority": "high",
            "parent": None,
            "labels": ["spec-complete", "gate-blocked"],
            "blocked_by": [],
            "blocks": ["P1-06"],
        }

        rendered = plan_tool.render_markdown(metadata, "# Goal\n\nDefine the rules.\n")
        parsed, body = plan_tool.parse_markdown(rendered)

        self.assertIn("blocked_by: []", rendered)
        self.assertEqual(metadata, parsed)
        self.assertEqual("# Goal\n\nDefine the rules.\n", body)


class PlanValidationTests(unittest.TestCase):
    def write_record(self, root: Path, metadata: dict) -> None:
        directory = "gates" if metadata["kind"] == "gate" else "tasks"
        path = root / directory / f"{metadata['id'].lower()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plan_tool.render_markdown(metadata, "# Goal\n\nTest body.\n"))

    def record(self, task_id: str, **overrides) -> dict:
        milestone = "M0" if task_id.startswith(("P0", "GATE-0")) else "M1"
        record = {
            "id": task_id,
            "linear_id": f"ROB-{task_id.replace('-', '')}",
            "title": task_id,
            "milestone": milestone,
            "kind": "gate" if task_id.startswith("GATE") else "implementation",
            "status": "ready-for-human" if task_id.startswith("GATE") else "gate-blocked",
            "priority": "high",
            "parent": None,
            "labels": ["ready-for-human"] if task_id.startswith("GATE") else ["spec-complete", "gate-blocked"],
            "blocked_by": [],
            "blocks": [],
        }
        record.update(overrides)
        return record

    def test_accepts_an_acyclic_symmetric_gate_aware_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.record("P1-01", blocks=["P1-02"])
            second = self.record("P1-02", blocked_by=["P1-01"], blocks=["GATE-1"])
            gate = self.record("GATE-1", blocked_by=["P1-02"])
            for record in (first, second, gate):
                self.write_record(root, record)

            result = plan_tool.validate_plan(root)

            self.assertEqual([], result.errors)
            self.assertEqual(3, len(result.records))

    def test_rejects_missing_dependencies_cycles_and_asymmetric_edges(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.record("P1-01", blocked_by=["P1-02"], blocks=["P1-02", "P1-99"])
            second = self.record("P1-02", blocked_by=["P1-01"])
            for record in (first, second):
                self.write_record(root, record)

            result = plan_tool.validate_plan(root)
            joined = "\n".join(result.errors)

            self.assertIn("missing task P1-99", joined)
            self.assertIn("dependency cycle", joined)
            self.assertIn("is not mirrored", joined)

    def test_rejects_future_work_marked_ready_for_agent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            task = self.record(
                "P1-01",
                status="ready-for-agent",
                labels=["ready-for-agent"],
            )
            self.write_record(root, task)

            result = plan_tool.validate_plan(root)

            self.assertTrue(any("M1-M6 work must remain gate-blocked" in error for error in result.errors))

    def test_allows_ready_work_after_the_milestone_is_authorized(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "state.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "authorized_milestones": ["M0", "M1"],
                        "current_gate": "GATE-1",
                    }
                )
            )
            task = self.record(
                "P1-01",
                status="ready-for-agent",
                labels=["ready-for-agent"],
            )
            self.write_record(root, task)

            result = plan_tool.validate_plan(root)

            self.assertEqual([], result.errors)


class IndexTests(unittest.TestCase):
    def test_builds_a_stably_sorted_compact_index(self):
        records = {
            "P1-02": {
                "id": "P1-02",
                "title": "Second",
                "milestone": "M1",
                "kind": "implementation",
                "status": "gate-blocked",
                "priority": "high",
                "parent": None,
                "blocked_by": ["P1-01"],
                "blocks": [],
                "path": "tasks/p1-02.md",
            },
            "P1-01": {
                "id": "P1-01",
                "title": "First",
                "milestone": "M1",
                "kind": "implementation",
                "status": "gate-blocked",
                "priority": "high",
                "parent": None,
                "blocked_by": [],
                "blocks": ["P1-02"],
                "path": "tasks/p1-01.md",
            },
        }

        index = plan_tool.build_index(records, exported_at="2026-08-31T12:00:00Z")

        self.assertEqual(["P1-01", "P1-02"], [task["id"] for task in index["tasks"]])
        self.assertEqual("2026-08-31T12:00:00Z", index["exported_at"])
        self.assertEqual(2, index["task_count"])
        json.dumps(index)


class SnapshotImportTests(unittest.TestCase):
    def test_stdin_import_consumes_one_snapshot_line_without_waiting_for_eof(self):
        snapshot = {
            "exported_at": "2026-08-31T12:00:00Z",
            "project": {
                "name": "Rust + BEAM Mobile OS POC",
                "summary": "Phase 0 only.",
                "description": "# Mission\n",
                "url": "https://linear.example/project",
            },
            "documents": [],
            "milestones": [],
            "issues": [],
        }

        with tempfile.TemporaryDirectory() as temporary:
            args = argparse.Namespace(snapshot=Path("-"), root=Path(temporary) / "plan")
            stream = io.StringIO(json.dumps(snapshot) + "\nthis must remain unread\n")

            with mock.patch("sys.stdin", stream):
                result = plan_tool._command_import_snapshot(args)

            self.assertEqual(0, result)
            self.assertEqual("this must remain unread\n", stream.readline())

    def test_imports_documents_milestones_tasks_gates_and_index(self):
        snapshot = {
            "exported_at": "2026-08-31T12:00:00Z",
            "project": {
                "name": "Rust + BEAM Mobile OS POC",
                "summary": "Phase 0 only.",
                "description": "# Mission\n\nBuild the POC.\n",
                "url": "https://linear.example/project",
            },
            "documents": [
                {
                    "title": "Architecture & Validation Plan",
                    "content": "# Architecture\n\nThe design.\n",
                    "url": "https://linear.example/architecture",
                },
                {
                    "title": "Implementation Readiness Review & Linear Remediation Bundle",
                    "content": "# Readiness\n\nPhase 0 only.\n",
                    "url": "https://linear.example/readiness",
                },
            ],
            "milestones": [
                {
                    "name": "M1 — Bootable Rust Kernel Spine",
                    "description": "# Outcome\n\nA kernel spine.\n",
                }
            ],
            "issues": [
                {
                    "id": "ROB-1",
                    "title": "P1-01 — First task",
                    "description": (
                        "# Goal\n\nFirst.\n\n"
                        "[Architecture](<https://linear.example/architecture>)\n"
                    ),
                    "url": "https://linear.example/ROB-1",
                    "milestone": "M1 — Bootable Rust Kernel Spine",
                    "priority": "High",
                    "labels": ["spec-complete", "gate-blocked"],
                    "parent_id": None,
                    "blocked_by": [],
                    "blocks": ["ROB-2"],
                },
                {
                    "id": "ROB-2",
                    "title": "GATE-1 — Decide whether to continue",
                    "description": (
                        "# Decision\n\nReview the relevant Linear issue using only Linear and evidence.\n\n"
                        "<issue id=\"uuid\" href=\"https://linear.example/old-slug\">ROB-1</issue>\n"
                    ),
                    "url": "https://linear.example/ROB-2",
                    "milestone": "M1 — Bootable Rust Kernel Spine",
                    "priority": "No priority",
                    "labels": ["ready-for-human"],
                    "parent_id": None,
                    "blocked_by": ["ROB-1"],
                    "blocks": [],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"

            plan_tool.import_snapshot(snapshot, root)

            self.assertTrue((root / "project.md").exists())
            self.assertTrue((root / "architecture.md").exists())
            self.assertTrue((root / "readiness-review.md").exists())
            self.assertTrue((root / "milestones" / "m1.md").exists())
            self.assertTrue((root / "tasks" / "p1-01.md").exists())
            self.assertTrue((root / "gates" / "gate-1.md").exists())
            self.assertEqual(2, json.loads((root / "index.json").read_text())["task_count"])
            self.assertEqual([], plan_tool.validate_plan(root).errors)
            task_content = (root / "tasks" / "p1-01.md").read_text()
            gate_content = (root / "gates" / "gate-1.md").read_text()
            self.assertIn("# Goal\n\nFirst.", task_content)
            self.assertIn("[Architecture](<../architecture.md>)", task_content)
            self.assertIn("[P1-01](<../tasks/p1-01.md>)", gate_content)
            self.assertIn("relevant repository task file", gate_content)
            self.assertIn("using only repository plan content and evidence", gate_content)
            self.assertNotIn("linear.example", task_content.split("---", 2)[-1])


if __name__ == "__main__":
    unittest.main()
