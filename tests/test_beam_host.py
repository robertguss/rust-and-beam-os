import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("beam_host", ROOT / "scripts/beam_host.py")
assert SPEC and SPEC.loader
BEAM_HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BEAM_HOST)


class BeamHostTests(unittest.TestCase):
    def test_revision_zero_classifies_host_and_target_observations(self):
        contract = json.loads((ROOT / "abi/beam-host.yaml").read_text())
        interactions = {item["syscall"]: item for item in contract["interactions"]}
        self.assertEqual(0, contract["revision"])
        self.assertEqual([], contract["unresolved"])
        self.assertNotIn("unexplained", {item["classification"] for item in interactions.values()})
        for path in (
            ROOT / "target/beam-host-reference/aggregate.json",
            ROOT / "target/erts-linux-reference/acceptance/aggregate.json",
        ):
            if path.is_file():
                observed = json.loads(path.read_text())["observed_syscalls"]
                self.assertEqual([], sorted(set(observed) - set(interactions)))

    def test_required_interactions_name_evidence_tests_and_family_contract(self):
        contract = json.loads((ROOT / "abi/beam-host.yaml").read_text())
        for interaction in contract["interactions"]:
            if interaction["classification"] != "required":
                continue
            family = contract["families"][interaction["family"]]
            self.assertTrue(interaction["operations"])
            self.assertTrue(interaction["evidence"])
            self.assertTrue(interaction["tests"])
            for field in ("callers", "semantics", "errors", "blocking"):
                self.assertTrue(family[field])

    def test_trace_summary_normalizes_ephemeral_paths_and_error_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trace = root / "trace"
            trace.mkdir()
            (trace / "raw.100").write_text(
                "1.0 mmap(NULL, 4096, PROT_NONE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = -1 ENOMEM (Cannot allocate memory) <0.1>\n"
                "1.1 read(3, 0x1234, 1) = -1 EFAULT (Bad address) <0.1>\n"
                "1.2 openat(AT_FDCWD, \"/tmp/mix_user_check_123_random\", O_RDONLY) = -1 ENOENT (No such file) <0.1>\n"
                "1.3 --- SIGUSR1 {si_signo=SIGUSR1} ---\n"
            )
            summary = BEAM_HOST.summarize_scenario(trace, root)
        self.assertEqual(["ENOMEM"], summary["errors"]["mmap"])
        self.assertEqual(["EFAULT"], summary["errors"]["read"])
        self.assertIn("/tmp/mix_user_check_$TOKEN", summary["paths"])
        self.assertEqual(["SIGUSR1"], summary["signals"])
        self.assertIn("mmap", summary["families"]["mappings"])

    def test_normalized_replay_ignores_counts_but_preserves_semantics(self):
        scenario = {
            "syscalls": ["futex"],
            "errors": {"futex": ["EAGAIN"]},
            "argument_tokens": {"futex": ["FUTEX_WAIT_PRIVATE"]},
            "signals": [],
            "paths": [],
            "families": {"threads": ["futex"]},
            "syscall_counts": {"futex": 10},
            "trace_files": 2,
        }
        first = BEAM_HOST.normalized_replay({"scenarios": {"workload": scenario}})
        scenario["syscall_counts"]["futex"] = 99
        second = BEAM_HOST.normalized_replay({"scenarios": {"workload": scenario}})
        self.assertEqual(first, second)

    def test_fault_probe_covers_normative_error_and_lifecycle_scenarios(self):
        source = (ROOT / "tests/beam-host/fault_probe.c").read_text()
        for scenario in (
            "allocation_failure",
            "copy_failure",
            "timeout_path",
            "cancellation_path",
            "signal_path",
            "close_failure",
            "thread_exit_path",
        ):
            self.assertIn(scenario, source)
        self.assertIn("EFAULT", source)
        self.assertIn("PTHREAD_CANCELED", source)
        self.assertIn("SA_ONSTACK", source)


if __name__ == "__main__":
    unittest.main()
