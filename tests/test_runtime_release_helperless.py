import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "runtime_release_helperless", ROOT / "scripts/runtime_release_helperless.py"
)
assert SPEC and SPEC.loader
HELPERLESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPERLESS)


class RuntimeReleaseHelperlessTests(unittest.TestCase):
    def test_launcher_seals_helperless_entrypoint_and_identity(self):
        HELPERLESS.configure_runtime_release()
        launcher = HELPERLESS.runtime_release.launcher()
        self.assertEqual(HELPERLESS.BEAM_SHA256, launcher["runtime"]["beam_sha256"])
        self.assertEqual(HELPERLESS.ARTIFACT_BUILD_ID, launcher["runtime"]["artifact_build_id"])
        self.assertEqual(
            "'Elixir.RuntimeLab.HelperlessProbe':run().",
            launcher["arguments"][-4],
        )
        self.assertEqual({}, HELPERLESS.runtime_release.ALLOWED_RUNTIME_HELPERS)

    def test_process_audit_allows_threads_and_rejects_process_clone(self):
        with tempfile.TemporaryDirectory() as temporary:
            traces = Path(temporary)
            trace = traces / "release.1"
            trace.write_text(
                "1.0 clone(child_stack=0x1, flags=CLONE_VM|CLONE_THREAD|CLONE_SETTLS) = 2 <0.1>\n"
            )
            self.assertEqual("pass", HELPERLESS.helperless_process_audit(traces)["status"])

            trace.write_text(
                "1.0 clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|SIGCHLD) = 2 <0.1>\n"
            )
            with self.assertRaisesRegex(HELPERLESS.HelperlessError, "process syscall"):
                HELPERLESS.helperless_process_audit(traces)

    def test_guest_covers_absence_negative_operations_and_sigterm(self):
        init = (ROOT / "tests/runtime-release/helperless-init.sh").read_text()
        probe = (ROOT / "beam/runtime_lab/lib/runtime_lab/helperless_probe.ex").read_text()
        self.assertIn("[ ! -e \"$BINDIR/$helper\" ]", init)
        self.assertIn("event=sigterm-exit", init)
        for operation in ("os_cmd", "system_cmd", "port_spawn", "heart", "public_missing_host"):
            self.assertIn(operation, probe)
        self.assertIn("{:error, :nxdomain}", probe)


if __name__ == "__main__":
    unittest.main()
