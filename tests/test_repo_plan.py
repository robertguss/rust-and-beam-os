import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import repo_plan


SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "repo_plan.py"


class DeterministicGenerationTests(unittest.TestCase):
    def test_init_creates_a_complete_byte_identical_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"

            for root in (first, second):
                repo_plan.initialize_plan(
                    root=root,
                    name="Example project",
                    prefix="EX",
                    milestone_id="EX-M-M0",
                    milestone_title="Foundation",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )

            first_files = {
                path.relative_to(first): path.read_bytes()
                for path in first.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second): path.read_bytes()
                for path in second.rglob("*")
                if path.is_file()
            }

            self.assertEqual(first_files, second_files)
            self.assertEqual(
                {
                    Path("README.md"),
                    Path("project.yaml"),
                    Path("milestones/ex-m-m0.md"),
                    Path("tasks/README.md"),
                    Path("gates/README.md"),
                    Path("decisions/README.md"),
                    Path("generated/index.json"),
                    Path("generated/graph.json"),
                    Path("generated/ready.json"),
                },
                set(first_files),
            )
            self.assertEqual(
                'schema: "repo-plan/v1"\nname: "Example project"\nprefix: "EX"\n',
                (first / "project.yaml").read_text(),
            )

    def test_new_task_renders_the_versioned_template_exactly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"
            repo_plan.initialize_plan(
                root=root,
                name="Example project",
                prefix="EX",
                milestone_id="EX-M-M0",
                milestone_title="Foundation",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )

            destination = repo_plan.create_record(
                root=root,
                record_type="task",
                record_id="EX-T-7M3K2Q",
                title="Reproduce the reference runtime",
                milestone="EX-M-M0",
                priority="P1",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )

            metadata, body = repo_plan.parse_markdown(destination.read_text())
            self.assertEqual("repo-plan/v1", metadata["schema"])
            self.assertEqual("EX-T-7M3K2Q", metadata["id"])
            self.assertEqual([], metadata["depends_on"])
            self.assertEqual([], metadata["evidence"])
            self.assertEqual(
                [
                    "Goal",
                    "Context",
                    "Deliverables",
                    "Acceptance criteria",
                    "Verification",
                    "Evidence",
                    "Out of scope",
                ],
                repo_plan.second_level_headings(body),
            )
            self.assertTrue(destination.read_bytes().endswith(b"\n"))

    def test_generation_refuses_to_overwrite_canonical_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"
            repo_plan.initialize_plan(
                root=root,
                name="Example project",
                prefix="EX",
                milestone_id="EX-M-M0",
                milestone_title="Foundation",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )

            with self.assertRaisesRegex(FileExistsError, "non-empty"):
                repo_plan.initialize_plan(
                    root=root,
                    name="Replacement",
                    prefix="EX",
                    milestone_id="EX-M-M0",
                    milestone_title="Foundation",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )

            repo_plan.create_record(
                root=root,
                record_type="task",
                record_id="EX-T-7M3K2Q",
                title="First title",
                milestone="EX-M-M0",
                priority="P1",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )
            with self.assertRaises(FileExistsError):
                repo_plan.create_record(
                    root=root,
                    record_type="task",
                    record_id="EX-T-7M3K2Q",
                    title="Replacement title",
                    milestone="EX-M-M0",
                    priority="P1",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )

    def test_cli_initializes_and_adds_a_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"
            init = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "init",
                    "--root",
                    str(root),
                    "--name",
                    "Example project",
                    "--prefix",
                    "EX",
                    "--milestone-id",
                    "EX-M-M0",
                    "--milestone-title",
                    "Foundation",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, init.returncode, init.stderr)

            create = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "new",
                    "task",
                    "--root",
                    str(root),
                    "--id",
                    "EX-T-7M3K2Q",
                    "--title",
                    "Reproduce runtime",
                    "--milestone",
                    "EX-M-M0",
                    "--priority",
                    "P1",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, create.returncode, create.stderr)
            self.assertTrue((root / "tasks" / "ex-t-7m3k2q.md").exists())


class ValidationTests(unittest.TestCase):
    def initialize(self, temporary: str) -> Path:
        root = Path(temporary) / "plan"
        repo_plan.initialize_plan(
            root=root,
            name="Example project",
            prefix="EX",
            milestone_id="EX-M-M0",
            milestone_title="Foundation",
            templates=repo_plan.DEFAULT_TEMPLATES,
        )
        return root

    def create_task(
        self,
        root: Path,
        record_id: str,
        *,
        title: str | None = None,
        milestone: str = "EX-M-M0",
        priority: str = "P2",
        record_type: str = "task",
        parent: str | None = None,
    ) -> Path:
        return repo_plan.create_record(
            root=root,
            record_type=record_type,
            record_id=record_id,
            title=title or record_id,
            milestone=milestone,
            priority=priority,
            parent=parent,
            templates=repo_plan.DEFAULT_TEMPLATES,
        )

    def set_scalar(self, path: Path, key: str, old: str, new: str) -> None:
        content = path.read_text()
        needle = f"{key}: {old}\n"
        self.assertIn(needle, content)
        path.write_text(content.replace(needle, f"{key}: {new}\n", 1))

    def set_list(self, path: Path, key: str, values: list[str]) -> None:
        content = path.read_text()
        needle = f"{key}: []\n"
        self.assertIn(needle, content)
        rendered = f"{key}:\n" + "".join(f'  - "{value}"\n' for value in values)
        path.write_text(content.replace(needle, rendered, 1))

    def test_initialized_plan_is_valid_and_generated_views_are_current(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)

            result = repo_plan.check_plan(root, evaluation_date=None)

            self.assertEqual([], result.errors)
            self.assertEqual(1, len(result.records))

    def test_reports_missing_sections_references_links_and_stale_views(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            task = self.create_task(root, "EX-T-7M3K2Q")
            self.set_list(task, "depends_on", ["EX-T-MISSING"])
            task.write_text(
                task.read_text()
                .replace("## Verification\n", "## Missing verification\n")
                .replace(
                    "Link only the context needed to execute this record.",
                    "Read [missing context](../missing-context.md).",
                )
            )

            result = repo_plan.check_plan(root, evaluation_date=None)
            joined = "\n".join(result.errors)

            self.assertIn("missing required heading: Verification", joined)
            self.assertIn("depends_on references missing record EX-T-MISSING", joined)
            self.assertIn("broken local link", joined)
            self.assertIn("generated/index.json is stale", joined)

    def test_rejects_blocking_and_parent_cycles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            first = self.create_task(root, "EX-T-7M3K2Q")
            second = self.create_task(root, "EX-T-8N4R6W")
            first_epic = self.create_task(root, "EX-E-6Q2V8K", record_type="epic")
            second_epic = self.create_task(root, "EX-E-9P4C7M", record_type="epic")
            self.set_list(first, "depends_on", ["EX-T-8N4R6W"])
            self.set_list(second, "depends_on", ["EX-T-7M3K2Q"])
            self.set_scalar(first_epic, "parent", "null", '"EX-E-9P4C7M"')
            self.set_scalar(second_epic, "parent", "null", '"EX-E-6Q2V8K"')

            joined = "\n".join(repo_plan.check_plan(root, evaluation_date=None).errors)

            self.assertIn("depends_on cycle", joined)
            self.assertIn("parent cycle", joined)

    def test_ready_work_is_authorized_dependency_free_and_explainably_sorted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            unlocker = self.create_task(root, "EX-T-7M3K2Q", priority="P2")
            blocked = self.create_task(root, "EX-T-8N4R6W", priority="P1")
            independent = self.create_task(root, "EX-T-9P4C7M", priority="P2")
            self.set_list(blocked, "depends_on", ["EX-T-7M3K2Q"])
            gate = repo_plan.create_record(
                root=root,
                record_type="gate",
                record_id="EX-G-5W8N2R",
                title="Authorize M1",
                milestone="EX-M-M0",
                priority="P0",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )
            repo_plan.create_record(
                root=root,
                record_type="milestone",
                record_id="EX-M-M1",
                title="Implementation",
                order=1,
                authorized_by="EX-G-5W8N2R",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )
            self.create_task(root, "EX-T-4F6H8J", milestone="EX-M-M1", priority="P0")

            result = repo_plan.validate_plan(root)
            ready = repo_plan.compute_ready(result.records, evaluation_date="2026-08-31")

            self.assertEqual([], result.errors)
            self.assertEqual(["EX-T-7M3K2Q", "EX-T-9P4C7M"], [item["id"] for item in ready])
            self.assertEqual(1, ready[0]["incomplete_downstream"])
            self.assertEqual(0, ready[1]["incomplete_downstream"])
            self.assertNotIn("EX-T-8N4R6W", [item["id"] for item in ready])
            self.assertNotIn("EX-T-4F6H8J", [item["id"] for item in ready])
            self.assertEqual("open", repo_plan.parse_markdown(gate.read_text())[0]["state"])

    def test_done_tasks_require_evidence_and_in_progress_tasks_require_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            done = self.create_task(root, "EX-T-7M3K2Q")
            active = self.create_task(root, "EX-T-8N4R6W")
            self.set_scalar(done, "state", '"open"', '"done"')
            self.set_scalar(active, "state", '"open"', '"in_progress"')

            joined = "\n".join(repo_plan.validate_plan(root).errors)

            self.assertIn("done task requires evidence", joined)
            self.assertIn("in_progress record requires owner", joined)

    def test_done_gate_requires_exactly_one_decision(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            gate = repo_plan.create_record(
                root=root,
                record_type="gate",
                record_id="EX-G-5W8N2R",
                title="Authorize M1",
                milestone="EX-M-M0",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )
            self.set_scalar(gate, "state", '"open"', '"done"')

            missing = "\n".join(repo_plan.validate_plan(root).errors)
            self.assertIn("done gate requires exactly one decision", missing)

            repo_plan.create_record(
                root=root,
                record_type="decision",
                record_id="EX-D-6Q2V8K",
                title="Authorize M1",
                gate="EX-G-5W8N2R",
                outcome="approved",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )

            self.assertEqual([], repo_plan.validate_plan(root).errors)


if __name__ == "__main__":
    unittest.main()
