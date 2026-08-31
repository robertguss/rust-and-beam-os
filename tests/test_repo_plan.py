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


if __name__ == "__main__":
    unittest.main()
