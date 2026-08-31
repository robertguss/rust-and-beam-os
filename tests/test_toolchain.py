import copy
import unittest

from scripts import toolchain


class ToolchainContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = toolchain.load_json(toolchain.LOCK_PATH)
        cls.contract = toolchain.load_json(toolchain.CONTRACT_PATH)

    def test_repository_contract_and_generated_report_are_current(self) -> None:
        lock, contract, sources = toolchain.load_and_validate()
        self.assertEqual(len(sources), 20)
        self.assertEqual(
            toolchain.REPORT_PATH.read_text(encoding="utf-8"),
            toolchain.render_report(lock, contract, sources),
        )

    def test_mutable_source_reference_is_rejected(self) -> None:
        lock = copy.deepcopy(self.lock)
        lock["entries"][0]["locator"] = "https://example.invalid/releases/latest/source.tar.xz"
        with self.assertRaisesRegex(toolchain.ToolchainError, "mutable reference"):
            toolchain.validate_lock(lock)

    def test_non_content_addressed_mirror_is_rejected(self) -> None:
        lock = copy.deepcopy(self.lock)
        lock["entries"][0]["mirror_path"] = "downloads/elixir.tar.gz"
        with self.assertRaisesRegex(toolchain.ToolchainError, "content-addressed"):
            toolchain.validate_lock(lock)

    def test_receipt_comparison_ignores_observation_identity_only(self) -> None:
        base = {
            "schema": "rust-beam/toolchain-receipt/v1",
            "contract": self.contract,
            "contract_digest": toolchain.object_digest(self.contract),
            "source_lock": self.lock,
            "source_lock_digest": toolchain.object_digest(self.lock),
            "builder_observation": {"id": "clean-a"},
        }
        second = copy.deepcopy(base)
        second["builder_observation"]["id"] = "clean-b"
        comparison = toolchain.compare_receipts([base, second])
        self.assertEqual(comparison["result"], "match")

        drifted = copy.deepcopy(second)
        drifted["contract"]["targets"]["page_size"] = 16384
        drifted["contract_digest"] = toolchain.object_digest(drifted["contract"])
        with self.assertRaisesRegex(toolchain.ToolchainError, "contract drift"):
            toolchain.compare_receipts([base, drifted])

        source_drifted = copy.deepcopy(second)
        source_drifted["source_lock"]["entries"][0]["version"] = "1.20.3"
        source_drifted["source_lock_digest"] = toolchain.object_digest(
            source_drifted["source_lock"]
        )
        with self.assertRaisesRegex(toolchain.ToolchainError, "source-lock drift"):
            toolchain.compare_receipts([base, source_drifted])


if __name__ == "__main__":
    unittest.main()
