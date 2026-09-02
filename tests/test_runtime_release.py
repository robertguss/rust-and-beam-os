import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("runtime_release", ROOT / "scripts/runtime_release.py")
assert SPEC and SPEC.loader
RUNTIME_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME_RELEASE)


class RuntimeReleaseTests(unittest.TestCase):
    def test_launcher_is_exact_direct_target_beam_contract(self):
        launcher = RUNTIME_RELEASE.launcher()
        executable = "/system/beam/runtime_lab/erts-17.0.5/bin/beam.smp"
        self.assertEqual(executable, launcher["process"]["executable"])
        self.assertEqual(executable, launcher["arguments"][0])
        self.assertEqual(RUNTIME_RELEASE.TARGET_BEAM_SHA256, launcher["runtime"]["beam_sha256"])
        self.assertEqual([], launcher["release"]["config_providers"])
        self.assertFalse(launcher["release"]["runtime_config_path"])
        self.assertEqual(
            ["-S", "2:2", "-SDcpu", "1:1", "-SDio", "1", "-A", "1"],
            launcher["arguments"][1:9],
        )

        invalid = copy.deepcopy(launcher)
        invalid["arguments"][0] = "/system/beam/runtime_lab/bin/runtime_lab"
        with self.assertRaisesRegex(RUNTIME_RELEASE.ReleaseError, "executable"):
            RUNTIME_RELEASE.validate_launcher(invalid)

    def test_qemu_argv_is_full_system_offline_with_read_only_release(self):
        argv = RUNTIME_RELEASE.qemu_argv(
            Path("qemu-system-aarch64"),
            Path("vmlinuz"),
            Path("initramfs"),
            Path("paired.squashfs"),
            Path("results.img"),
            Path("serial.log"),
        )
        joined = " ".join(map(str, argv))
        self.assertIn("virt-11.1,gic-version=3,dtb-randomness=off", joined)
        self.assertIn("tcg,thread=multi", joined)
        self.assertIn("file=paired.squashfs,format=raw,if=none,readonly=on,id=release", joined)
        self.assertIn("virtio-blk-device,drive=release", joined)
        self.assertIn("-nodefaults", argv)
        self.assertNotIn("qemu-aarch64", joined)
        self.assertNotIn("-net", joined)

    def test_open_audit_requires_erofs_and_rejects_undeclared_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            traces = Path(temporary)
            (traces / "release.1").write_text(
                "1.0 openat(AT_FDCWD, \"/system/beam/runtime_lab/releases/0.1.0/start.boot\", "
                "O_RDONLY|O_CLOEXEC) = 3 <0.1>\n"
                "1.1 openat(AT_FDCWD, \"/system/beam/runtime_lab/.rb-write-probe\", "
                "O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC, 0666) = -1 EROFS (Read-only file system) <0.1>\n"
            )
            audit = RUNTIME_RELEASE.audit_open_attempts(traces)
            self.assertEqual("pass", audit["status"])
            self.assertEqual(1, audit["release_read_count"])
            self.assertEqual(1, audit["declared_negative_count"])
            self.assertEqual([], audit["undeclared_write_attempts"])

            (traces / "release.2").write_text(
                '1.2 openat(AT_FDCWD, "/tmp/undeclared", O_WRONLY|O_CREAT, 0600) = 4 <0.1>\n'
            )
            with self.assertRaisesRegex(RUNTIME_RELEASE.ReleaseError, "undeclared write"):
                RUNTIME_RELEASE.audit_open_attempts(traces)

    def test_exec_inventory_allows_only_beam_and_upstream_helpers(self):
        root = RUNTIME_RELEASE.RELEASE_ROOT
        with tempfile.TemporaryDirectory() as temporary:
            traces = Path(temporary)
            trace = traces / "release.1"
            trace.write_text(
                f'1.0 execve("{root}/erts-17.0.5/bin/beam.smp", ["beam.smp"], []) = 0 <0.1>\n'
                f'1.1 execve("{root}/erts-17.0.5/bin/erl_child_setup", ["erl_child_setup"], []) = 0 <0.1>\n'
            )
            inventory = RUNTIME_RELEASE.exec_inventory(traces)
            self.assertEqual("manifest-entrypoint", inventory[0]["classification"])
            self.assertEqual("upstream-erts-helper", inventory[1]["classification"])

            trace.write_text(
                trace.read_text()
                + f'1.2 execve("{root}/erts-17.0.5/bin/erlexec", ["erlexec"], []) = 0 <0.1>\n'
            )
            with self.assertRaisesRegex(RUNTIME_RELEASE.ReleaseError, "forbidden executable"):
                RUNTIME_RELEASE.exec_inventory(traces)

    def test_tree_manifest_is_stable_and_content_sensitive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            (root / "lib/application.beam").write_bytes(b"beam")
            (root / "current").symlink_to("lib")
            first = RUNTIME_RELEASE.tree_manifest(root)
            second = RUNTIME_RELEASE.tree_manifest(root)
            self.assertEqual(first, second)
            self.assertEqual(RUNTIME_RELEASE.value_sha256(first), RUNTIME_RELEASE.value_sha256(second))
            (root / "lib/application.beam").write_bytes(b"changed")
            self.assertNotEqual(first, RUNTIME_RELEASE.tree_manifest(root))

    def test_guest_init_launches_beam_without_release_script_or_erlexec(self):
        text = (ROOT / "tests/runtime-release/init.sh").read_text()
        self.assertIn('"$BINDIR/beam.smp" -S 2:2 -SDcpu 1:1 -SDio 1 -A 1 --', text)
        self.assertIn('-boot "$RELEASE_ROOT/releases/0.1.0/start"', text)
        self.assertIn('-args_file "$RELEASE_ROOT/releases/0.1.0/vm.args"', text)
        self.assertNotIn('"$RELEASE_ROOT/bin/runtime_lab"', text)
        self.assertNotIn("erlexec", text)
        self.assertNotIn("qemu-aarch64", text)

if __name__ == "__main__":
    unittest.main()
