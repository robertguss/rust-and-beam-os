#!/usr/bin/env python3
"""Build and verify the sealed helperless ERTS runtime_lab profile."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from scripts import erts_linux, otp_artifact, runtime_release
except ModuleNotFoundError:
    import erts_linux  # type: ignore[no-redef]
    import otp_artifact  # type: ignore[no-redef]
    import runtime_release  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "target/runtime-release-helperless"
OTP_WORK_ROOT = ROOT / "target/otp-helperless"
PROFILE_PATH = ROOT / "toolchain/otp/aarch64-linux-musl-helperless.json"
BEAM_SHA256 = "2236a94efdea84687c7139f4fa021c4381aa5d00969976bfc330049554711c22"
ARTIFACT_BUILD_ID = f"otp-29.0.5-erts-17.0.5-helperless-beam-sha256-{BEAM_SHA256}"
PROCESS_CALL_RE = re.compile(r"(?:^|\s)(fork|vfork|setsid|wait4|socketpair)\(")
HELPER_EXEC_RE = re.compile(r'(?:^|\s)execve\("[^"]*/(?:erl_child_setup|inet_gethost)"')


class HelperlessError(RuntimeError):
    """Raised when helperless runtime evidence violates the sealed profile."""


def configure_runtime_release() -> None:
    runtime_release.WORK_ROOT = WORK_ROOT
    runtime_release.TARGET_RELEASE = OTP_WORK_ROOT / "primary/release"
    runtime_release.TARGET_BEAM = runtime_release.TARGET_RELEASE / "erts-17.0.5/bin/beam.smp"
    runtime_release.TARGET_NATIVE_CLOSURE_PATH = OTP_WORK_ROOT / "primary/inspection/native-closure.json"
    runtime_release.LAUNCHER_PATH = ROOT / "image/runtime-lab-helperless-launcher.json"
    runtime_release.INIT_PATH = ROOT / "tests/runtime-release/helperless-init.sh"
    runtime_release.OTP_PROFILE_PATH = PROFILE_PATH
    runtime_release.OTP_ARTIFACT_ARGS = [
        "--profile",
        str(PROFILE_PATH.relative_to(ROOT)),
        "--work-root",
        str(OTP_WORK_ROOT.relative_to(ROOT)),
    ]
    runtime_release.TARGET_BEAM_SHA256 = BEAM_SHA256
    runtime_release.ARTIFACT_BUILD_ID = ARTIFACT_BUILD_ID
    runtime_release.PROBE_EVAL = "'Elixir.RuntimeLab.HelperlessProbe':run()."
    runtime_release.RELEASE_BUILD_ENV = {"RB_HELPERLESS_RELEASE": "1"}
    runtime_release.ALLOWED_RUNTIME_HELPERS = {}


def configure_erts_linux() -> None:
    erts_linux.WORK_ROOT = Path("target/erts-linux-helperless")
    erts_linux.BEAM_PATH = Path("target/otp-helperless/primary/release/erts-17.0.5/bin/beam.smp")
    erts_linux.RELEASE_PATH = Path("target/otp-helperless/primary/release")
    erts_linux.NATIVE_CLOSURE_PATH = Path("target/otp-helperless/primary/inspection/native-closure.json")
    erts_linux.OTP_PROFILE_PATH = Path("toolchain/otp/aarch64-linux-musl-helperless.json")
    erts_linux.OTP_ARTIFACT_ARGS = runtime_release.OTP_ARTIFACT_ARGS
    erts_linux.ERTS_BEAM_SHA256_OVERRIDE = BEAM_SHA256
    erts_linux.ERTS_INETRC_CONTENT = "%% Helperless direct ERTS profile.\n{lookup, [file]}.\n"
    erts_linux.DECLARED_RUNTIME_PATHS = {"/etc/rb-helperless-inetrc"}


def helperless_process_audit(trace_dir: Path) -> dict[str, Any]:
    violations = []
    clone_processes = []
    for trace_file in sorted(path for path in trace_dir.iterdir() if path.is_file()):
        for line in trace_file.read_text(encoding="utf-8", errors="replace").splitlines():
            normalized = erts_linux.normalize_trace_line(line)
            if PROCESS_CALL_RE.search(line) or "SCM_RIGHTS" in line:
                violations.append(normalized)
            if "clone(" in line and "SIGCHLD" in line and "CLONE_THREAD" not in line:
                clone_processes.append(normalized)
            if HELPER_EXEC_RE.search(line):
                violations.append(normalized)
    violations.extend(clone_processes)
    if violations:
        raise HelperlessError(f"helper process syscall observed: {violations[0]}")
    return {
        "status": "pass",
        "fork": 0,
        "vfork": 0,
        "clone_process": 0,
        "setsid": 0,
        "wait4": 0,
        "socketpair": 0,
        "scm_rights": 0,
    }


def validate_helperless_boot(boot_dir: Path) -> dict[str, Any]:
    serial = (boot_dir / "serial.log").read_text(encoding="utf-8", errors="replace")
    required = (
        "profile=helperless",
        "type=helperless_result",
        "file_lookup=true",
        "status=pass",
        "name: :os_cmd",
        "name: :system_cmd",
        "name: :port_spawn",
        "name: :port_spawn_executable",
        "name: :heart",
        "name: :public_missing_host",
        "{:return, {:error, :nxdomain}}",
        "liveness_after_rejections=true",
        "RB_RELEASE_GUEST event=sigterm-ready",
        "RB_RELEASE_GUEST event=sigterm-exit status=0",
    )
    missing = [marker for marker in required if marker not in serial]
    if missing:
        raise HelperlessError(f"helperless serial milestones differ: missing={missing}")

    pair = WORK_ROOT / "paired/erts-17.0.5/bin"
    present_helpers = [name for name in ("erl_child_setup", "inet_gethost") if (pair / name).exists()]
    if present_helpers:
        raise HelperlessError(f"paired release contains forbidden helpers: {present_helpers}")

    receipt_path = boot_dir / "receipt.json"
    receipt = runtime_release.load_json(receipt_path)
    process_audit = helperless_process_audit(boot_dir / "results/traces")
    if any(entry["classification"] != "manifest-entrypoint" for entry in receipt["executable_inventory"]):
        raise HelperlessError("helperless trace contains a non-entrypoint executable")
    helperless = {
        "status": "pass",
        "helpers_absent": ["erl_child_setup", "inet_gethost"],
        "negative_operations_bounded": 6,
        "file_lookup": "localhost -> 127.0.0.1",
        "sigterm_exit": 0,
        "process_syscalls": process_audit,
        "udp_interpretation": "metadata-only when no connect, send, or listener is observed",
    }
    receipt["helperless"] = helperless
    receipt_path.write_text(runtime_release.canonical_json(receipt), encoding="utf-8")
    return helperless


def validate_adapter_source() -> dict[str, Any]:
    profile = otp_artifact.load_profile(PROFILE_PATH)
    audit = otp_artifact.audit_patch(profile["patches"][0])
    source = OTP_WORK_ROOT / "primary/src/erts/emulator/sys/unix/sys_drivers.c"
    text = source.read_text(encoding="utf-8")
    if "erts_sys_unix_later_init();" not in text or "#ifdef RB_ERTS_NO_FORKER" not in text:
        raise HelperlessError("sealed source does not retain Unix later-init behind the adapter")
    receipt = runtime_release.load_json(OTP_WORK_ROOT / "primary/build-receipt.json")
    omissions = receipt.get("source_start", {}).get("release_omissions", [])
    if [entry.get("path") for entry in omissions] != profile["patches"][0]["release_omissions"]:
        raise HelperlessError("build receipt does not prove both sealed helper omissions")
    return {
        "patch_digest": audit["actual_digest"],
        "patch_changed_lines": audit["changed_lines"],
        "changed_files": audit["files"],
        "unix_later_init_retained": True,
        "release_omissions": omissions,
    }


def run_boots(boots: int, output: Path) -> Path:
    aggregate_path = runtime_release.run_boots(boots, output)
    helperless_boots = [validate_helperless_boot(output / f"boot-{boot:02d}") for boot in range(1, boots + 1)]
    aggregate = runtime_release.load_json(aggregate_path)
    aggregate["helperless"] = {
        "status": "pass",
        "boots": helperless_boots,
        "adapter": validate_adapter_source(),
    }
    aggregate_path.write_text(runtime_release.canonical_json(aggregate), encoding="utf-8")
    print(f"runtime-release-helperless: {boots}/{boots} helperless boots passed")
    return aggregate_path


def run_erts_boots(boots: int, output: Path) -> Path:
    runtime_release.ensure_target_release()
    aggregate_path = erts_linux.run_boots(ROOT, boots, output)
    audits = []
    for boot in range(1, boots + 1):
        boot_dir = output / f"boot-{boot:02d}"
        audit = helperless_process_audit(boot_dir / "results/traces")
        receipt_path = boot_dir / "receipt.json"
        receipt = runtime_release.load_json(receipt_path)
        receipt["helperless_process_syscalls"] = audit
        receipt_path.write_text(runtime_release.canonical_json(receipt), encoding="utf-8")
        audits.append(audit)
    aggregate = runtime_release.load_json(aggregate_path)
    aggregate["helperless"] = {"status": "pass", "process_syscalls": audits}
    aggregate_path.write_text(runtime_release.canonical_json(aggregate), encoding="utf-8")
    print(f"runtime-release-helperless: {boots}/{boots} direct ERTS boots passed")
    return aggregate_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="build a fresh helperless Mix release")
    subparsers.add_parser("pair", help="pair and compare helperless release assemblies")
    runtime_parser = subparsers.add_parser("runtime", help="boot the helperless ERTS workloads")
    runtime_parser.add_argument("--boots", type=int, default=1)
    runtime_parser.add_argument("--output", type=Path, default=ROOT / "target/erts-linux-helperless/latest")
    run_parser = subparsers.add_parser("run", help="boot the helperless release under full-system QEMU")
    run_parser.add_argument("--boots", type=int, default=1)
    run_parser.add_argument("--output", type=Path, default=WORK_ROOT / "latest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_runtime_release()
    configure_erts_linux()
    try:
        if args.command == "build":
            runtime_release.build_mix_lane("primary")
        elif args.command == "pair":
            runtime_release.pair_all()
        elif args.command == "runtime":
            if not 1 <= args.boots <= 20:
                raise HelperlessError("--boots must be between 1 and 20")
            output = args.output if args.output.is_absolute() else ROOT / args.output
            run_erts_boots(args.boots, output)
        elif args.command == "run":
            if not 1 <= args.boots <= 20:
                raise HelperlessError("--boots must be between 1 and 20")
            output = args.output if args.output.is_absolute() else ROOT / args.output
            run_boots(args.boots, output)
        else:
            raise AssertionError(args.command)
    except (
        HelperlessError,
        runtime_release.ReleaseError,
        otp_artifact.ArtifactError,
        erts_linux.ReferenceError,
        OSError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"runtime-release-helperless: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
