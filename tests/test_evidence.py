import json
import tempfile
import unittest
from pathlib import Path

from scripts import evidence


class EvidenceValidationTests(unittest.TestCase):
    def test_repository_fixture_passes(self) -> None:
        root = Path(__file__).parents[1]
        task_ids = evidence._task_ids(root)
        record = evidence.validate_evidence(
            root,
            root / "docs/evidence/fixtures/evidence.json",
            task_ids,
        )
        self.assertEqual(record["id"], "RB-EV-FIXTURE-V1")

    def test_digest_drift_is_rejected(self) -> None:
        root = Path(__file__).parents[1]
        original_path = root / "docs/evidence/fixtures/evidence.json"
        record = json.loads(original_path.read_text(encoding="utf-8"))
        record["inputs"][0]["digest"] = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            path = Path(temporary) / "evidence.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(evidence.EvidenceError, "digest mismatch"):
                evidence.validate_evidence(root, path, evidence._task_ids(root))

    def test_repository_escape_is_rejected(self) -> None:
        root = Path(__file__).parents[1]
        original_path = root / "docs/evidence/fixtures/evidence.json"
        record = json.loads(original_path.read_text(encoding="utf-8"))
        record["inputs"][0]["path"] = "../outside"
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            path = Path(temporary) / "evidence.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(evidence.EvidenceError, "repository-relative"):
                evidence.validate_evidence(root, path, evidence._task_ids(root))


if __name__ == "__main__":
    unittest.main()
