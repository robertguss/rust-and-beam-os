#!/usr/bin/env python3
"""Build QEMU and run the RB-T-P011 bare-metal display/input probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

QEMU_VERSION = "11.1.0"
QEMU_DIGEST = "6ee1d1a61f68212476b27108c26da5f449dc09b626d42f8279ba0dc2e08fa858"
QEMU_SIZE = 141_831_772
QEMU_URL = "https://download.qemu.org/qemu-11.1.0.tar.xz"
MACHINE = "virt-11.1"
INPUT_X = 24_575
INPUT_Y = 16_384
QEMU_CONFIGURE = (
    "--target-list=aarch64-softmmu",
    "--without-default-features",
    "--enable-system",
    "--enable-tcg",
    "--enable-pixman",
    "--enable-fdt=system",
    "--disable-debug-info",
    "--disable-werror",
    "--disable-containers",
    "--prefix=/qemu-probe",
    "-Dwrap_mode=nodownload",
)


class ProbeError(RuntimeError):
    """Raised when a build or acceptance invariant fails."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 1800,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise ProbeError(f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}")
    return result


def qemu_paths(root: Path) -> tuple[Path, Path, Path]:
    base = root / "target/qemu-11.1.0"
    return base / "src", base / "build", base / "build/qemu-system-aarch64"


def verify_qemu(root: Path, binary: Path) -> bool:
    if not binary.is_file() or not os.access(binary, os.X_OK):
        return False
    version = run([str(binary), "--version"], cwd=root, timeout=20).stdout.splitlines()[0]
    machines = run([str(binary), "-machine", "help"], cwd=root, timeout=20).stdout
    return f"version {QEMU_VERSION}" in version and MACHINE in machines


def qemu_provenance(root: Path, binary: Path) -> dict[str, Any]:
    version = run([str(binary), "--version"], cwd=root, timeout=20).stdout.splitlines()[0]
    return {
        "schema": "rust-beam/virtio-probe-qemu/v1",
        "source": {
            "url": QEMU_URL,
            "size": QEMU_SIZE,
            "sha256": QEMU_DIGEST,
        },
        "configure_argv": list(QEMU_CONFIGURE),
        "qemu_version": version,
        "qemu_binary_sha256": sha256(binary),
        "machine": MACHINE,
    }


def prepared_qemu_matches(root: Path, binary: Path, receipt: Path) -> bool:
    if not verify_qemu(root, binary) or not receipt.is_file():
        return False
    try:
        recorded = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return recorded == qemu_provenance(root, binary)


def verify_qemu_source_lock(root: Path) -> None:
    lock_path = root / "toolchain/sources.lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        entry = next(item for item in lock["entries"] if item["id"] == "qemu-source")
    except (OSError, json.JSONDecodeError, KeyError, StopIteration, TypeError) as error:
        raise ProbeError("sealed source lock has no readable qemu-source entry") from error
    expected = {
        "version": QEMU_VERSION,
        "locator": QEMU_URL,
        "digest": f"sha256:{QEMU_DIGEST}",
        "size": QEMU_SIZE,
        "mirror_path": f"sha256/{QEMU_DIGEST}",
    }
    observed = {key: entry.get(key) for key in expected}
    if observed != expected:
        raise ProbeError(f"qemu-source disagrees with the probe constants: {observed}")


def prepare_qemu(root: Path) -> Path:
    verify_qemu_source_lock(root)
    source, build, binary = qemu_paths(root)
    receipt = source.parent / "provenance.json"
    archive = root / f"target/toolchain-cache/sha256/{QEMU_DIGEST}"
    if not archive.is_file():
        archive.parent.mkdir(parents=True, exist_ok=True)
        temporary = archive.with_name(f".{archive.name}.tmp")
        temporary.unlink(missing_ok=True)
        run(
            [
                "curl",
                "--fail",
                "--location",
                "--proto",
                "=https",
                "--tlsv1.2",
                "--silent",
                "--show-error",
                QEMU_URL,
                "--output",
                str(temporary),
            ],
            cwd=root,
        )
        if temporary.stat().st_size != QEMU_SIZE or sha256(temporary) != QEMU_DIGEST:
            temporary.unlink(missing_ok=True)
            raise ProbeError("downloaded QEMU source disagrees with the sealed source lock")
        temporary.replace(archive)
    if archive.stat().st_size != QEMU_SIZE or sha256(archive) != QEMU_DIGEST:
        raise ProbeError("sealed QEMU source disagrees with toolchain/sources.lock.json")
    if prepared_qemu_matches(root, binary, receipt):
        print(f"virtio-probe: using prepared {binary.relative_to(root)}")
        return binary

    base = source.parent
    shutil.rmtree(base, ignore_errors=True)
    source.mkdir(parents=True)
    build.mkdir(parents=True)
    run(
        ["tar", "-xf", str(archive), "-C", str(source), "--strip-components=1"],
        cwd=root,
    )
    configure = [str(source / "configure"), *QEMU_CONFIGURE]
    run(configure, cwd=build)
    run(["ninja", "qemu-system-aarch64"], cwd=build)
    if not verify_qemu(root, binary):
        raise ProbeError("prepared QEMU lacks the pinned versioned Arm machine")
    receipt.write_text(json.dumps(qemu_provenance(root, binary), indent=2, sort_keys=True) + "\n")
    print(f"virtio-probe: prepared {binary.relative_to(root)}")
    return binary


def build_probe(root: Path) -> Path:
    crate = root / "tests/virtio-probe"
    run(["cargo", "build", "--release", "--locked", "--offline"], cwd=crate)
    elf = crate / "target/aarch64-unknown-none/release/virtio-probe"
    image = elf.with_suffix(".img")
    rustc = run(["rustc", "-vV"], cwd=root, timeout=20).stdout
    host = next(line.split(": ", 1)[1] for line in rustc.splitlines() if line.startswith("host: "))
    sysroot = Path(run(["rustc", "--print", "sysroot"], cwd=root, timeout=20).stdout.strip())
    objcopy = sysroot / f"lib/rustlib/{host}/bin/rust-objcopy"
    if not objcopy.is_file():
        raise ProbeError("rust-objcopy is missing from the pinned Rust toolchain")
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(sysroot / "lib") + (
        f":{env['LD_LIBRARY_PATH']}" if env.get("LD_LIBRARY_PATH") else ""
    )
    run([str(objcopy), "-O", "binary", str(elf), str(image)], cwd=root, env=env)
    if image.read_bytes()[56:60] != b"ARMd":
        raise ProbeError("probe image lacks the Arm64 boot header")
    return image


def qemu_argv(qemu: Path, image: Path, serial: Path, qmp: Path) -> list[str]:
    return [
        str(qemu),
        "-machine",
        f"{MACHINE},gic-version=3,dtb-randomness=off",
        "-cpu",
        "cortex-a53",
        "-accel",
        "tcg,thread=single",
        "-smp",
        "1",
        "-m",
        "512M",
        "-nodefaults",
        "-no-reboot",
        "-no-shutdown",
        "-display",
        "none",
        "-serial",
        f"file:{serial}",
        "-qmp",
        f"unix:{qmp},server=on,wait=off",
        "-kernel",
        str(image),
        "-device",
        "virtio-gpu-pci,id=gpu0,bus=pcie.0,addr=1,xres=640,yres=480",
        "-device",
        "virtio-tablet-pci,id=pointer0,bus=pcie.0,addr=2",
    ]


class QmpClient:
    def __init__(self, path: Path, log_path: Path, timeout: float = 15.0):
        deadline = time.monotonic() + timeout
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        while True:
            try:
                self.socket.connect(str(path))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if time.monotonic() >= deadline:
                    raise ProbeError("QMP socket did not become ready")
                time.sleep(0.02)
        self.socket.settimeout(timeout)
        self.stream = self.socket.makefile("rwb", buffering=0)
        self.log = log_path.open("w", encoding="utf-8")
        self.next_id = 1
        greeting = self._receive()
        if "QMP" not in greeting:
            raise ProbeError("invalid QMP greeting")
        self.command("qmp_capabilities")

    def close(self) -> None:
        self.stream.close()
        self.socket.close()
        self.log.close()

    def _record(self, direction: str, message: dict[str, Any]) -> None:
        self.log.write(json.dumps({"direction": direction, "message": message}, sort_keys=True) + "\n")
        self.log.flush()

    def _receive(self) -> dict[str, Any]:
        line = self.stream.readline()
        if not line:
            raise ProbeError("QMP disconnected")
        message = json.loads(line)
        self._record("receive", message)
        return message

    def command(self, execute: str, arguments: dict[str, Any] | None = None) -> Any:
        request: dict[str, Any] = {"execute": execute, "id": self.next_id}
        self.next_id += 1
        if arguments is not None:
            request["arguments"] = arguments
        self._record("send", request)
        self.stream.write((json.dumps(request, separators=(",", ":")) + "\r\n").encode())
        while True:
            response = self._receive()
            if response.get("id") != request["id"]:
                continue
            if "error" in response:
                raise ProbeError(f"QMP {execute} failed: {response['error']}")
            return response.get("return")


class SerialMonitor:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = ""
        self.events: list[dict[str, Any]] = []

    def refresh(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as stream:
            stream.seek(self.offset)
            data = stream.read()
            self.offset = stream.tell()
        self.pending += data
        lines = self.pending.split("\n")
        self.pending = lines.pop()
        for raw in lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as error:
                raise ProbeError(f"non-JSON guest serial line: {raw}") from error
            self.events.append(event)
            if event.get("event") in {"fail", "panic"}:
                raise ProbeError(f"guest reported {event}")

    def wait(self, name: str, *, timeout: float = 30.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.refresh()
            for event in self.events:
                if event.get("event") == name:
                    return event
            time.sleep(0.01)
        raise ProbeError(f"timed out waiting for serial event {name}")


def parse_ppm(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    index = 0

    def token() -> bytes:
        nonlocal index
        while index < len(data):
            if data[index:index + 1] == b"#":
                index = data.index(b"\n", index) + 1
            elif data[index:index + 1].isspace():
                index += 1
            else:
                break
        start = index
        while index < len(data) and not data[index:index + 1].isspace():
            index += 1
        return data[start:index]

    if token() != b"P6":
        raise ProbeError("screenshot is not binary PPM")
    width = int(token())
    height = int(token())
    if int(token()) != 255:
        raise ProbeError("screenshot has unsupported PPM depth")
    separator = data[index:index + 1]
    if not separator.isspace():
        raise ProbeError("screenshot has no PPM pixel separator")
    index += 1
    if separator == b"\r" and data[index:index + 1] == b"\n":
        index += 1
    pixels = data[index:]
    if len(pixels) != width * height * 3:
        raise ProbeError("screenshot pixel length is inconsistent")
    return width, height, pixels


def validate_landmarks(path: Path) -> dict[str, Any]:
    width, height, pixels = parse_ppm(path)

    def pixel(x: int, y: int) -> str:
        offset = (y * width + x) * 3
        return pixels[offset:offset + 3].hex()

    observed = {
        "top_left": pixel(16, 16),
        "top_right": pixel(width - 16, 16),
        "bottom_left": pixel(16, height - 16),
        "bottom_right": pixel(width - 16, height - 16),
        "changed_center": pixel(width // 2, height // 2),
        "pointer_red": pixel(
            (INPUT_X * (width - 1)) // 32_767 + 1,
            (INPUT_Y * (height - 1)) // 32_767 + 2,
        ),
    }
    expected = {
        "top_left": "ff00ff",
        "top_right": "00ffff",
        "bottom_left": "ffff00",
        "bottom_right": "ffffff",
        "changed_center": "30d020",
        "pointer_red": "ff2020",
    }
    if observed != expected:
        raise ProbeError(f"screenshot landmarks disagree: expected={expected}, observed={observed}")
    return {"width": width, "height": height, "expected": expected, "observed": observed}


def summarize_serial(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        by_name.setdefault(str(event.get("event")), []).append(event)
    required = {
        "boot",
        "platform",
        "dma_contract",
        "pci_devices",
        "pci_interrupts",
        "transport_audit",
        "reset_recovery",
        "queue_exhaustion",
        "malformed_command",
        "frame_presented",
        "ready_for_input",
        "ready_for_capture",
        "teardown",
        "pass",
    }
    missing = sorted(required - by_name.keys())
    if missing:
        raise ProbeError(f"serial milestones missing: {missing}")
    passed = by_name["pass"][-1]
    malformed = by_name["malformed_command"][-1]
    teardown = by_name["teardown"][-1]
    pci_interrupts = by_name["pci_interrupts"][-1]
    frames = by_name["frame_presented"]
    if (
        passed.get("frames") != 2
        or passed.get("input_events", 0) < 6
        or passed.get("interrupts_observed", 0) < 1
        or not passed.get("duplicate_isr_ack_empty")
        or not passed.get("polling_without_cpu_irqs")
        or not passed.get("capture_ack")
        or malformed.get("response_length", 33) > 32
        or not malformed.get("canaries_ok")
        or teardown.get("bounds_violations") != 0
        or teardown.get("dma_allocations") != teardown.get("dma_deallocations")
        or pci_interrupts.get("route_count", 0) < 2
        or pci_interrupts.get("gpu_pin") not in range(1, 5)
        or pci_interrupts.get("input_pin") not in range(1, 5)
        or pci_interrupts.get("gpu_gic_irq", 0) < 32
        or pci_interrupts.get("input_gic_irq", 0) < 32
        or [frame.get("frame") for frame in frames] != [1, 2]
    ):
        raise ProbeError("serial counters do not satisfy the probe contract")
    return {
        "event_count": len(events),
        "input_events": passed["input_events"],
        "frames": passed["frames"],
        "interrupts_observed": passed["interrupts_observed"],
        "duplicate_isr_ack_empty": passed["duplicate_isr_ack_empty"],
        "dma_bounds_violations": teardown["bounds_violations"],
        "malformed_response_length": malformed["response_length"],
        "gpu_interrupt": {
            "pin": pci_interrupts["gpu_pin"],
            "gic_irq": pci_interrupts["gpu_gic_irq"],
            "flags": pci_interrupts["gpu_flags"],
        },
        "input_interrupt": {
            "pin": pci_interrupts["input_pin"],
            "gic_irq": pci_interrupts["input_gic_irq"],
            "flags": pci_interrupts["input_flags"],
        },
        "event_names": sorted(by_name),
    }


def input_events(*, capture_ack: bool = False) -> list[dict[str, Any]]:
    if capture_ack:
        return [
            {"type": "btn", "data": {"down": True, "button": "right"}},
            {"type": "btn", "data": {"down": False, "button": "right"}},
        ]
    return [
        {"type": "abs", "data": {"axis": "x", "value": INPUT_X}},
        {"type": "abs", "data": {"axis": "y", "value": INPUT_Y}},
        {"type": "btn", "data": {"down": True, "button": "left"}},
        {"type": "btn", "data": {"down": False, "button": "left"}},
    ]


def run_boot(root: Path, qemu: Path, image: Path, output: Path, boot: int) -> dict[str, Any]:
    boot_dir = output / f"boot-{boot:02d}"
    boot_dir.mkdir(parents=True, exist_ok=True)
    serial_path = boot_dir / "serial.jsonl"
    qmp_path = boot_dir / "qmp.sock"
    qmp_log = boot_dir / "qmp.jsonl"
    qemu_log = boot_dir / "qemu.log"
    screenshot = boot_dir / "screenshot.ppm"
    dtb = boot_dir / "machine.dtb"
    qmp_path.unlink(missing_ok=True)
    argv = qemu_argv(qemu, image, serial_path, qmp_path)
    started = time.monotonic()
    with qemu_log.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(argv, cwd=root, stdin=subprocess.DEVNULL, stdout=stderr, stderr=subprocess.STDOUT)
    qmp: QmpClient | None = None
    try:
        qmp = QmpClient(qmp_path, qmp_log)
        monitor = SerialMonitor(serial_path)
        monitor.wait("ready_for_input", timeout=45)
        commands = qmp.command("query-commands")
        command_names = {command["name"] for command in commands}
        metadata: dict[str, Any] = {}
        for command in ("query-version", "query-status", "query-cpus-fast", "query-mice"):
            if command in command_names:
                metadata[command] = qmp.command(command)
        if "x-query-virtio" in command_names:
            metadata["x-query-virtio"] = qmp.command("x-query-virtio")
        qmp.command("input-send-event", {"events": input_events()})
        monitor.wait("ready_for_capture", timeout=30)
        if "dumpdtb" in command_names:
            qmp.command("dumpdtb", {"filename": str(dtb)})
        else:
            raise ProbeError("pinned QEMU does not expose QMP dumpdtb")
        qmp.command("screendump", {"filename": str(screenshot)})
        landmarks = validate_landmarks(screenshot)
        qmp.command("input-send-event", {"events": input_events(capture_ack=True)})
        monitor.wait("pass", timeout=20)
        monitor.refresh()
        serial_summary = summarize_serial(monitor.events)
        qmp.command("quit")
        process.wait(timeout=10)
        if process.returncode != 0:
            raise ProbeError(f"QEMU exited with {process.returncode}")
    finally:
        if qmp is not None:
            qmp.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        qmp_path.unlink(missing_ok=True)

    receipt = {
        "schema": "rust-beam/virtio-probe-boot/v1",
        "status": "pass",
        "boot": boot,
        "duration_seconds": round(time.monotonic() - started, 3),
        "qemu_argv": argv,
        "qemu_sha256": sha256(qemu),
        "probe_sha256": sha256(image),
        "machine": MACHINE,
        "cpu": "cortex-a53",
        "gic": "3",
        "accelerator": "tcg,thread=single",
        "memory": "512M",
        "devices": [
            "virtio-gpu-pci,id=gpu0,bus=pcie.0,addr=1,xres=640,yres=480",
            "virtio-tablet-pci,id=pointer0,bus=pcie.0,addr=2",
        ],
        "semihosting": False,
        "host_framebuffer_bridge": False,
        "qmp_metadata": metadata,
        "serial": serial_summary,
        "serial_sha256": sha256(serial_path),
        "qmp_log_sha256": sha256(qmp_log),
        "qemu_log_sha256": sha256(qemu_log),
        "screenshot": landmarks,
        "screenshot_sha256": sha256(screenshot),
        "dtb_sha256": sha256(dtb),
    }
    (boot_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        f"virtio-probe: boot {boot}/{output.name} pass "
        f"frames={serial_summary['frames']} inputs={serial_summary['input_events']}"
    )
    return receipt


def run_boots(root: Path, boots: int, output: Path) -> Path:
    qemu = prepare_qemu(root)
    image = build_probe(root)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = [run_boot(root, qemu, image, output, boot) for boot in range(1, boots + 1)]
    qemu_version = run([str(qemu), "--version"], cwd=root, timeout=20).stdout.splitlines()[0]
    aggregate = {
        "schema": "rust-beam/virtio-probe-run/v1",
        "status": "pass",
        "boots_requested": boots,
        "boots_passed": len(receipts),
        "qemu_version": qemu_version,
        "qemu_source_sha256": QEMU_DIGEST,
        "qemu_binary_sha256": sha256(qemu),
        "qemu_provenance_sha256": sha256(qemu.parent.parent / "provenance.json"),
        "probe_image_sha256": sha256(image),
        "rust_target": "aarch64-unknown-none",
        "virtio_drivers": "0.13.0",
        "machine": MACHINE,
        "durations_seconds": [receipt["duration_seconds"] for receipt in receipts],
        "receipt_paths": [f"boot-{boot:02d}/receipt.json" for boot in range(1, boots + 1)],
        "all_frames": [receipt["serial"]["frames"] for receipt in receipts],
        "all_input_events": [receipt["serial"]["input_events"] for receipt in receipts],
        "all_dma_bounds_violations": [receipt["serial"]["dma_bounds_violations"] for receipt in receipts],
        "host": {"os": platform.system(), "architecture": platform.machine()},
    }
    aggregate_path = output / "aggregate.json"
    aggregate_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n")
    print(f"virtio-probe: {boots}/{boots} TCG boots passed; receipt={aggregate_path.relative_to(root)}")
    return aggregate_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "run"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--boots", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "prepare":
            print(prepare_qemu(root).relative_to(root))
        elif args.command == "build":
            print(build_probe(root).relative_to(root))
        else:
            if not 1 <= args.boots <= 100:
                raise ProbeError("--boots must be between 1 and 100")
            output = args.output or root / "target/virtio-probe/latest"
            if not output.is_absolute():
                output = root / output
            run_boots(root, args.boots, output)
    except (ProbeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"virtio-probe: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
