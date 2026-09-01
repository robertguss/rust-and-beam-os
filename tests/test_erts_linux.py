import gzip
import importlib.util
import stat
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("erts_linux", ROOT / "scripts/erts_linux.py")
assert SPEC and SPEC.loader
ERTS_LINUX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ERTS_LINUX)


def newc_archive(entries):
    output = bytearray()
    for inode, name, mode, content in entries + [(0, "TRAILER!!!", stat.S_IFREG, b"")]:
        encoded_name = name.encode() + b"\0"
        fields = (
            inode,
            mode,
            0,
            0,
            1,
            0,
            len(content),
            0,
            0,
            0,
            0,
            len(encoded_name),
            0,
        )
        output.extend(b"070701" + b"".join(f"{field:08X}".encode() for field in fields))
        output.extend(encoded_name)
        output.extend(b"\0" * (-len(output) % 4))
        output.extend(content)
        output.extend(b"\0" * (-len(output) % 4))
    output.extend(b"\0" * (-len(output) % 512))
    return bytes(output)


class ErtsLinuxTests(unittest.TestCase):
    def test_profile_freezes_full_system_platform_and_erts(self):
        profile = ERTS_LINUX.load_profile(ROOT)
        self.assertEqual("virt-11.1", profile["qemu"]["machine"])
        self.assertEqual("cortex-a53", profile["qemu"]["cpu"])
        self.assertEqual(4, profile["qemu"]["vcpus"])
        self.assertEqual(
            ["-S", "2:2", "-SDcpu", "1:1", "-SDio", "1", "-A", "1"],
            profile["erts"]["candidate_flags"],
        )
        self.assertEqual(sorted(profile["sources"]), list(profile["sources"]))
        self.assertIn("alpine-aarch64-libdw", profile["sources"])

    def test_qemu_argv_is_full_system_offline_and_ephemeral(self):
        argv = ERTS_LINUX.qemu_argv(
            Path("qemu-system-aarch64"),
            Path("vmlinuz"),
            Path("initramfs"),
            Path("results.img"),
            Path("serial.log"),
        )
        joined = " ".join(map(str, argv))
        self.assertIn("virt-11.1,gic-version=3,dtb-randomness=off", joined)
        self.assertIn("tcg,thread=multi", joined)
        self.assertIn("console=ttyAMA0 rdinit=/init", joined)
        self.assertIn("virtio-blk-device", joined)
        self.assertIn("-nodefaults", argv)
        self.assertNotIn("-net", joined)
        self.assertNotIn("qemu-aarch64", joined)

    def test_concatenated_alpine_newc_archives_are_extracted(self):
        first = newc_archive([(1, "bin/busybox", stat.S_IFREG | 0o755, b"busybox")])
        second = newc_archive([(1, "etc/identity", stat.S_IFREG | 0o644, b"alpine\n")])
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            source = temporary_path / "initramfs.gz"
            destination = temporary_path / "root"
            destination.mkdir()
            source.write_bytes(gzip.compress(first + second, mtime=0))
            ERTS_LINUX.extract_concatenated_newc(source, destination)
            self.assertEqual(b"busybox", (destination / "bin/busybox").read_bytes())
            self.assertTrue((destination / "bin/busybox").stat().st_mode & stat.S_IXUSR)
            self.assertEqual("alpine\n", (destination / "etc/identity").read_text())

    def test_trace_summary_normalizes_addresses_and_records_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            traces = root / "traces"
            traces.mkdir()
            (traces / "candidate.12").write_text(
                "1788233619.1 mmap(NULL, 4096, 3, 34, -1, 0) = 0xabcdef <0.1>\n"
                "1788233619.2 openat(-100, \"/otp/releases/29/start.boot\", 0) = 3 <0.1>\n"
                "1788233619.3 --- SIGCHLD {si_signo=SIGCHLD} ---\n"
            )
            normalized = root / "normalized.gz"
            summary = ERTS_LINUX.trace_summary(traces, normalized)
            text = gzip.decompress(normalized.read_bytes()).decode()
        self.assertEqual({"mmap": 1, "openat": 1}, summary["syscalls"])
        self.assertEqual({"SIGCHLD": 1}, summary["signals"])
        self.assertEqual(["/otp/releases/29/start.boot"], summary["paths"])
        self.assertNotIn("1788233619", text)
        self.assertIn("0xADDR", text)

    def test_network_summary_allows_port_zero_without_hiding_services(self):
        with tempfile.TemporaryDirectory() as temporary:
            traces = Path(temporary)
            (traces / "trace.1").write_text(
                "1.0 bind(11<UDP:[1]>, {sa_family=AF_INET, sin_port=htons(0)}, 16) = 0 <0.1>\n"
                "1.1 connect(12, {sa_family=AF_INET, sin_port=htons(53)}, 16) = -1 ENETUNREACH <0.1>\n"
            )
            self.assertEqual(
                {"external_connections": 0, "service_listeners": 0, "ephemeral_udp_binds": 1},
                ERTS_LINUX.network_summary(traces),
            )
            (traces / "trace.2").write_text(
                "2.0 bind(13, {sa_family=AF_INET6, sin6_port=htons(4000)}, 28) = 0 <0.1>\n"
            )
            self.assertEqual(1, ERTS_LINUX.network_summary(traces)["service_listeners"])

    def test_file_accesses_are_classified_without_host_leakage(self):
        classes = ERTS_LINUX.file_access_summary(
            [
                "/otp/releases/29/start.boot",
                "/proc/self/mountinfo",
                "/sys/devices/system/cpu",
                "/tmp/home/.erlang",
                "/work/results/workload-candidate.json",
                "/unexpected/host/file",
            ]
        )
        self.assertEqual(["/tmp/home/.erlang"], classes["optional_absent"])
        self.assertEqual(["/work/results/workload-candidate.json"], classes["removable_harness"])
        self.assertIn("/otp/releases/29/start.boot", classes["required_runtime"])
        self.assertEqual(["/unexpected/host/file"], classes["forbidden"])

    def test_aarch64_auxv_and_workload_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "auxv"
            path.write_bytes(struct.pack("<QQQQQQ", 6, 4096, 16, 2303, 0, 0))
            self.assertEqual(
                {"AT_PAGESZ": 4096, "AT_HWCAP": 2303, "AT_NULL": 0},
                ERTS_LINUX.parse_auxv(path),
            )
        workload = {
            "schema": "rust-beam/erts-workload/v1",
            "profile": "candidate",
            "otp_release": "29",
            "erts_version": "17.0.5",
            "emu_flavor": "emu",
            "schedulers": 2,
            "schedulers_online": 2,
            "dirty_cpu_schedulers": 1,
            "dirty_cpu_schedulers_online": 1,
            "dirty_io_schedulers": 1,
            "async_threads": 1,
            "binary_bytes": 262144,
            "process_message": True,
            "timer": True,
            "ets": True,
            "forced_gc": True,
        }
        ERTS_LINUX.validate_workload("candidate", workload)
        workload["emu_flavor"] = "jit"
        with self.assertRaisesRegex(ERTS_LINUX.ReferenceError, "workload result differs"):
            ERTS_LINUX.validate_workload("candidate", workload)

    def test_guest_launch_contains_both_frozen_scheduler_profiles(self):
        init = (ROOT / "tests/erts-linux/init.sh").read_text()
        self.assertIn("run_profile single -S 1:1 -SDcpu 1:1 -SDio 1 -A 1", init)
        self.assertIn("run_profile candidate -S 2:2 -SDcpu 1:1 -SDio 1 -A 1", init)
        self.assertIn("-boot /otp/releases/29/start", init)
        self.assertNotIn("qemu-aarch64", init)


if __name__ == "__main__":
    unittest.main()
