import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("otp_artifact", ROOT / "scripts/otp_artifact.py")
assert SPEC and SPEC.loader
OTP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OTP)


def elf_fixture(*, elf_type=2, machine=183, program_type=1, flags=5, alignment=4096):
    ident = b"\x7fELF" + bytes([2, 1, 1, 0]) + bytes(8)
    header = struct.pack(
        "<16sHHIQQQIHHHHHH",
        ident,
        elf_type,
        machine,
        1,
        0x200000,
        64,
        120,
        0,
        64,
        56,
        1,
        64,
        0,
        0,
    )
    program = struct.pack("<IIQQQQQQ", program_type, flags, 0, 0x200000, 0x200000, 120, 120, alignment)
    return header + program


class OtpArtifactTests(unittest.TestCase):
    def test_repository_profile_is_valid(self):
        profile = json.loads((ROOT / "toolchain/otp/aarch64-linux-musl.json").read_text())
        OTP.validate_profile(profile)
        self.assertEqual([], profile["patches"])

    def test_helperless_profile_seals_small_unix_host_adapter(self):
        profile_path = ROOT / "toolchain/otp/aarch64-linux-musl-helperless.json"
        profile = OTP.load_profile(profile_path)
        self.assertEqual(["-DRB_ERTS_NO_FORKER=1"], profile["compiler"]["cflags"][-1:])
        self.assertEqual(1, len(profile["patches"]))

        audit = OTP.audit_patch(profile["patches"][0])
        self.assertEqual(["erts/emulator/sys/unix/sys_drivers.c"], audit["files"])
        self.assertLessEqual(audit["changed_lines"], 40)
        self.assertEqual("unix-host-adapter", audit["classification"])
        self.assertEqual(
            [
                "erts-17.0.5/bin/erl_child_setup",
                "erts-17.0.5/bin/inet_gethost",
            ],
            audit["release_omissions"],
        )

    def test_release_omissions_remove_only_sealed_helpers(self):
        profile = OTP.load_profile(ROOT / "toolchain/otp/aarch64-linux-musl-helperless.json")
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary)
            helper_dir = release / "erts-17.0.5/bin"
            helper_dir.mkdir(parents=True)
            for helper in ("erl_child_setup", "inet_gethost"):
                (helper_dir / helper).write_bytes(helper.encode())

            receipts = OTP.apply_release_omissions(release, profile)

        self.assertEqual(2, len(receipts))
        self.assertEqual(
            ["erts-17.0.5/bin/erl_child_setup", "erts-17.0.5/bin/inet_gethost"],
            [receipt["path"] for receipt in receipts],
        )

    def test_parse_aarch64_static_exec(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "beam.smp"
            path.write_bytes(elf_fixture())
            parsed = OTP.parse_elf(path)
        self.assertEqual("ET_EXEC", parsed["type"])
        self.assertEqual("AArch64", parsed["machine"])
        self.assertEqual("PT_LOAD", parsed["program_headers"][0]["type"])
        self.assertEqual(4096, parsed["program_headers"][0]["align"])

    def test_runtime_validator_rejects_interpreter(self):
        profile = OTP.load_profile()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "beam.smp"
            path.write_bytes(elf_fixture(program_type=3, flags=4, alignment=1))
            parsed = OTP.parse_elf(path)
            with self.assertRaisesRegex(OTP.ArtifactError, "PT_INTERP"):
                OTP.validate_runtime_elf(path, parsed, profile["artifact_contract"])

    def test_lse_mnemonic_policy(self):
        self.assertIsNotNone(OTP.LSE_MNEMONICS.fullmatch("casal"))
        self.assertIsNotNone(OTP.LSE_MNEMONICS.fullmatch("ldaddal"))
        self.assertIsNone(OTP.LSE_MNEMONICS.fullmatch("ldaxr"))

    def test_branch_protection_mnemonic_policy(self):
        self.assertIsNotNone(OTP.BRANCH_PROTECTION_MNEMONICS.fullmatch("bti"))
        self.assertIsNotNone(OTP.BRANCH_PROTECTION_MNEMONICS.fullmatch("paciasp"))
        self.assertIsNotNone(OTP.BRANCH_PROTECTION_MNEMONICS.fullmatch("autiasp"))
        self.assertIsNone(OTP.BRANCH_PROTECTION_MNEMONICS.fullmatch("ldaxr"))

    def test_beam_link_wrapper_tracks_upstream_beam_emu_name(self):
        source = (ROOT / "scripts/otp_artifact.py").read_text()
        self.assertIn("*/beam.emu|beam.emu|*/beam.smp|beam.smp", source)

    def test_generated_builtins_selects_only_target_table(self):
        with tempfile.TemporaryDirectory(prefix="otp-aarch64-") as temporary:
            source = Path(temporary)
            host = source / "erts/emulator/x86_64-pc-linux-gnu/opt/emu/driver_tab.c"
            target = source / "erts/emulator/aarch64-unknown-linux-musl/opt/emu/driver_tab.c"
            host.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            host.write_text("{&host_driver_entry, 0}\n")
            target.write_text("{&inet_driver_entry, 0}\n{&prim_file_nif_init, 0, THE_NON_VALUE, NULL}\n")

            builtins = OTP.generated_builtins(source)

        self.assertEqual("erts/emulator/aarch64-unknown-linux-musl/opt/emu/driver_tab.c", builtins["generated_table"])
        self.assertEqual(["inet"], builtins["builtin_drivers"])
        self.assertEqual(["prim_file"], builtins["builtin_nifs"])


if __name__ == "__main__":
    unittest.main()
