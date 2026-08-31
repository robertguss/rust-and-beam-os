import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import repo_plan
from scripts import plan_tool as legacy_plan_tool


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

    def test_generation_rejects_invalid_identity_and_references_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            invalid_root = Path(temporary) / "invalid"
            with self.assertRaisesRegex(ValueError, "prefix"):
                repo_plan.initialize_plan(
                    root=invalid_root,
                    name="Invalid project",
                    prefix="bad",
                    milestone_id="BAD-M-M0",
                    milestone_title="Foundation",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )
            self.assertFalse(invalid_root.exists())

            root = Path(temporary) / "plan"
            repo_plan.initialize_plan(
                root=root,
                name="Example project",
                prefix="EX",
                milestone_id="EX-M-M0",
                milestone_title="Foundation",
                templates=repo_plan.DEFAULT_TEMPLATES,
            )
            with self.assertRaisesRegex(ValueError, "invalid id"):
                repo_plan.create_record(
                    root=root,
                    record_type="task",
                    record_id="WRONG",
                    title="Invalid identity",
                    milestone="EX-M-M0",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )
            with self.assertRaisesRegex(ValueError, "missing milestone"):
                repo_plan.create_record(
                    root=root,
                    record_type="task",
                    record_id="EX-T-7M3K2Q",
                    title="Missing milestone",
                    milestone="EX-M-NOTFOUND",
                    templates=repo_plan.DEFAULT_TEMPLATES,
                )
            self.assertEqual([], list((root / "tasks").glob("ex-*.md")))

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

    def test_cli_build_check_and_ready_form_an_offline_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"
            common = [sys.executable, str(SCRIPT)]
            init = subprocess.run(
                [
                    *common,
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
                    *common,
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

            stale = subprocess.run(
                [*common, "check", "--root", str(root), "--date", "2026-08-31"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, stale.returncode)
            self.assertIn("is stale", stale.stderr)

            build = subprocess.run(
                [*common, "build", "--root", str(root), "--date", "2026-08-31"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, build.returncode, build.stderr)
            check = subprocess.run(
                [*common, "check", "--root", str(root), "--date", "2026-08-31"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, check.returncode, check.stderr)

            ready = subprocess.run(
                [*common, "ready", "--root", str(root), "--date", "2026-08-31", "--json"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, ready.returncode, ready.stderr)
            self.assertEqual(["EX-T-7M3K2Q"], [item["id"] for item in json.loads(ready.stdout)])


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

    def test_check_detects_scaffold_drift_and_build_restores_templates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            (root / "README.md").write_text("# Hand-edited generated instructions\n")

            stale = "\n".join(repo_plan.check_plan(root, evaluation_date=None).errors)
            self.assertIn("README.md differs from its template", stale)

            repo_plan.build_plan(root)

            self.assertEqual([], repo_plan.check_plan(root, evaluation_date=None).errors)
            self.assertIn("## Agent workflow", (root / "README.md").read_text())

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

    def test_rejects_unknown_fields_self_edges_and_done_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            dependency = self.create_task(root, "EX-T-7M3K2Q")
            task = self.create_task(root, "EX-T-8N4R6W")
            self.set_scalar(task, "state", '"open"', '"done"')
            self.set_list(task, "depends_on", ["EX-T-7M3K2Q", "EX-T-8N4R6W"])
            task.write_text(task.read_text().replace("state: \"done\"\n", "state: \"done\"\nmagic: \"value\"\n", 1))

            joined = "\n".join(repo_plan.validate_plan(root).errors)

            self.assertIn("unknown fields: magic", joined)
            self.assertIn("depends_on cannot reference itself", joined)
            self.assertIn("done record has unfinished dependencies", joined)
            self.assertEqual("open", repo_plan.parse_markdown(dependency.read_text())[0]["state"])

    def test_rejects_done_epic_with_unfinished_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.initialize(temporary)
            epic = self.create_task(root, "EX-E-6Q2V8K", record_type="epic")
            self.create_task(root, "EX-T-7M3K2Q", parent="EX-E-6Q2V8K")
            self.set_scalar(epic, "state", '"open"', '"done"')

            joined = "\n".join(repo_plan.validate_plan(root).errors)

            self.assertIn("done epic has unfinished children", joined)

    def test_rejected_gate_does_not_authorize_its_milestone(self):
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
            repo_plan.create_record(
                root=root,
                record_type="decision",
                record_id="EX-D-6Q2V8K",
                title="Reject M1",
                gate="EX-G-5W8N2R",
                outcome="rejected",
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
            self.create_task(root, "EX-T-7M3K2Q", milestone="EX-M-M1")

            result = repo_plan.validate_plan(root)
            ready = repo_plan.compute_ready(result.records, evaluation_date=None)

            self.assertEqual([], result.errors)
            self.assertEqual([], ready)

    def test_template_manifest_detects_a_missing_template(self):
        with tempfile.TemporaryDirectory() as temporary:
            templates = Path(temporary) / "templates"
            shutil.copytree(repo_plan.DEFAULT_TEMPLATES, templates)
            (templates / "gate.md.tmpl").unlink()

            self.assertEqual(
                ["missing template: gate.md.tmpl"],
                repo_plan.validate_templates(templates),
            )


class LegacyMigrationTests(unittest.TestCase):
    def write_legacy_plan(self, root: Path) -> None:
        root.mkdir(parents=True)
        (root / "README.md").write_text("# Legacy plan\n")
        (root / "project.md").write_text("# Legacy project context\n")
        (root / "state.json").write_text('{"authorized_milestones":["M0"]}\n')
        (root / "index.json").write_text('{"legacy":true}\n')

        milestone = {
            "id": "M0",
            "title": "M0 — Foundation",
            "kind": "milestone",
            "exported_at": "2026-08-31T12:00:00Z",
        }
        milestone_path = root / "milestones" / "m0.md"
        milestone_path.parent.mkdir(parents=True)
        milestone_path.write_text(
            legacy_plan_tool.render_markdown(
                milestone,
                "# M0\n\n## Outcome\n\nFoundation.\n\n## Exit criteria\n\n- Complete.\n",
            )
        )

        first = {
            "id": "P0-01",
            "linear_id": "ROB-1",
            "linear_url": "https://linear.example/ROB-1",
            "title": "First task",
            "milestone": "M0",
            "kind": "implementation",
            "status": "ready-for-agent",
            "priority": "high",
            "parent": None,
            "labels": ["ready-for-agent"],
            "blocked_by": [],
            "blocks": ["P0-02"],
        }
        second = {
            **first,
            "id": "P0-02",
            "linear_id": "ROB-2",
            "title": "Second task",
            "blocked_by": ["P0-01"],
            "blocks": [],
        }
        body = (
            "# Legacy task\n\n"
            "[Project](<../project.md>)\n\n"
            "## Goal\n\nDeliver the result.\n\n"
            "## Locked context\n\nUse the project contract.\n\n"
            "## Dependencies\n\nDepends on P0-01 when named by metadata.\n\n"
            "## What to build\n\nBuild one artifact.\n\n"
            "## Acceptance criteria\n\n- It works.\n\n"
            "## Required tests and evidence\n\nRun the test and record output.\n\n"
            "## Out of scope\n\nUnrelated work.\n\n"
            "## Verification commands\n\n`make test`\n"
        )
        for record in (first, second):
            path = root / "tasks" / f"{record['id'].lower()}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(legacy_plan_tool.render_markdown(record, body))

    def test_migration_is_deterministic_and_produces_a_valid_v1_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            for root in (first, second):
                self.write_legacy_plan(root)
                repo_plan.migrate_legacy(root=root, name="Legacy project", prefix="EX")

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
            self.assertNotIn(Path("state.json"), first_files)
            self.assertNotIn(Path("index.json"), first_files)
            self.assertIn(Path("project.yaml"), first_files)
            self.assertIn(Path("tasks/ex-t-p001.md"), first_files)
            self.assertIn(Path("tasks/ex-t-p002.md"), first_files)

            result = repo_plan.check_plan(first, evaluation_date=None)
            self.assertEqual([], result.errors)
            migrated = result.records["EX-T-P002"]
            self.assertEqual(["EX-T-P001"], migrated["depends_on"])
            self.assertNotIn("blocks", migrated)
            self.assertEqual("P1", migrated["priority"])
            self.assertIn("Depends on EX-T-P001", migrated["body"])
            self.assertNotIn("P0-01", migrated["body"])
            self.assertEqual(repo_plan.REQUIRED_HEADINGS["task"], tuple(
                heading for heading in repo_plan.second_level_headings(migrated["body"])
                if heading in repo_plan.REQUIRED_HEADINGS["task"]
            ))

    def test_cli_exposes_the_transactional_legacy_migration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "plan"
            self.write_legacy_plan(root)

            migrated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "migrate-legacy",
                    "--root",
                    str(root),
                    "--name",
                    "Legacy project",
                    "--prefix",
                    "EX",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, migrated.returncode, migrated.stderr)
            self.assertTrue((root / "project.yaml").exists())


if __name__ == "__main__":
    unittest.main()
