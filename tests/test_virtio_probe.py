import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("virtio_probe", ROOT / "scripts/virtio_probe.py")
assert SPEC and SPEC.loader
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class VirtioProbeTests(unittest.TestCase):
    def test_qemu_source_matches_sealed_lock(self):
        PROBE.verify_qemu_source_lock(ROOT)

    def test_qemu_argv_freezes_acceptance_platform(self):
        argv = PROBE.qemu_argv(
            Path("qemu-system-aarch64"),
            Path("probe.img"),
            Path("serial.jsonl"),
            Path("qmp.sock"),
        )
        joined = " ".join(map(str, argv))
        self.assertIn("virt-11.1,gic-version=3,dtb-randomness=off", joined)
        self.assertIn("cortex-a53", joined)
        self.assertIn("tcg,thread=single", joined)
        self.assertIn("virtio-gpu-pci", joined)
        self.assertIn("virtio-tablet-pci", joined)
        self.assertNotIn("semihosting", joined)
        self.assertEqual(["none"], [argv[index + 1] for index, value in enumerate(argv) if value == "-display"])

    def test_ppm_landmarks_validate_changed_frame(self):
        width, height = 160, 120
        pixels = bytearray(width * height * 3)

        def put(x, y, color):
            offset = (y * width + x) * 3
            pixels[offset:offset + 3] = bytes.fromhex(color)

        put(16, 16, "ff00ff")
        put(width - 16, 16, "00ffff")
        put(16, height - 16, "ffff00")
        put(width - 16, height - 16, "ffffff")
        put(width // 2, height // 2, "30d020")
        put(
            (PROBE.INPUT_X * (width - 1)) // 32_767 + 1,
            (PROBE.INPUT_Y * (height - 1)) // 32_767 + 2,
            "ff2020",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "shot.ppm"
            path.write_bytes(f"P6\n# fixture\n{width} {height}\n255\n".encode() + pixels)
            result = PROBE.validate_landmarks(path)
        self.assertEqual(width, result["width"])
        self.assertEqual(result["expected"], result["observed"])

    def test_serial_summary_requires_contract_milestones(self):
        names = [
            "boot",
            "platform",
            "dma_contract",
            "pci_devices",
            "pci_interrupts",
            "transport_audit",
            "reset_recovery",
            "queue_exhaustion",
            "ready_for_input",
            "ready_for_capture",
        ]
        events = [{"event": name} for name in names if name != "pci_interrupts"]
        events.extend(
            [
                {
                    "event": "pci_interrupts",
                    "route_count": 16,
                    "gpu_pin": 1,
                    "gpu_gic_irq": 36,
                    "gpu_flags": 4,
                    "input_pin": 1,
                    "input_gic_irq": 37,
                    "input_flags": 4,
                },
                {"event": "malformed_command", "response_length": 24, "canaries_ok": True},
                {"event": "frame_presented", "frame": 1},
                {"event": "frame_presented", "frame": 2},
                {
                    "event": "teardown",
                    "bounds_violations": 0,
                    "dma_allocations": 4,
                    "dma_deallocations": 4,
                },
                {
                    "event": "pass",
                    "frames": 2,
                    "input_events": 8,
                    "interrupts_observed": 1,
                    "duplicate_isr_ack_empty": True,
                    "polling_without_cpu_irqs": True,
                    "capture_ack": True,
                },
            ]
        )
        result = PROBE.summarize_serial(events)
        self.assertEqual(2, result["frames"])
        self.assertEqual(0, result["dma_bounds_violations"])

    def test_dependency_and_unsafe_contract_is_pinned(self):
        manifest = (ROOT / "tests/virtio-probe/Cargo.toml").read_text()
        lock = (ROOT / "tests/virtio-probe/Cargo.lock").read_text()
        source = (ROOT / "tests/virtio-probe/src/main.rs").read_text()
        fdt = (ROOT / "tests/virtio-probe/src/fdt.rs").read_text()
        self.assertIn('virtio-drivers = { version = "=0.13.0"', manifest)
        self.assertIn('name = "virtio-drivers"\nversion = "0.13.0"', lock)
        self.assertIn("DTB dma-coherent required", source)
        self.assertIn("ownership and lifetime invariant", source)
        self.assertIn("ECAM interrupt pin plus DTB interrupt-map", source)
        self.assertIn('"interrupt-map"', fdt)

    def test_serial_monitor_rejects_guest_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "serial.jsonl"
            path.write_text(json.dumps({"event": "fail", "stage": "fixture"}) + "\n")
            monitor = PROBE.SerialMonitor(path)
            with self.assertRaisesRegex(PROBE.ProbeError, "guest reported"):
                monitor.refresh()


if __name__ == "__main__":
    unittest.main()
