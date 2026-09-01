import datetime as dt
import unittest
from pathlib import Path

from scripts import plan_labels


class GateAwareLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan_root = Path(__file__).parents[1] / "docs/plan"
        projection = plan_labels.project(cls.plan_root, today=dt.date(2026, 8, 31))
        cls.records = {record["id"]: record for record in projection["records"]}

    def test_ready_task_is_ready_for_agent(self) -> None:
        self.assertTrue(
            any("ready-for-agent" in record["labels"] for record in self.records.values())
        )

    def test_completed_task_is_done(self) -> None:
        self.assertEqual(self.records["RB-T-P001"]["labels"], ["done"])

    def test_future_milestone_is_gate_blocked(self) -> None:
        self.assertIn("gate-blocked", self.records["RB-T-P100"]["labels"])
        self.assertNotIn("ready-for-agent", self.records["RB-T-P100"]["labels"])


if __name__ == "__main__":
    unittest.main()
