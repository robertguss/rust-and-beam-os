#!/usr/bin/env python3
"""Trace the pinned runtime_lab host workload and validate beam-host revision 0."""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("abi/beam-host.yaml")
OUTPUT_ROOT = Path("target/beam-host-reference")
RUNTIME_LAB = Path("beam/runtime_lab")
OTP_ROOT = Path("target/toolchain-smoke/install/otp/lib/erlang")
OTP_BIN = Path("target/toolchain-smoke/install/otp/bin")
ELIXIR_BIN = Path("target/toolchain-smoke/build/elixir/bin")
FAULT_SOURCE = Path("tests/beam-host/fault_probe.c")
TARGET_AGGREGATE = Path("target/erts-linux-reference/acceptance/aggregate.json")
SYSCALL_RE = re.compile(r"^(?:\d+\.\d+\s+)?([A-Za-z_][A-Za-z0-9_]*)\(")
ERROR_RE = re.compile(r"= -1 ([A-Z][A-Z0-9_]+) \(")
SIGNAL_RE = re.compile(r"--- (SIG[A-Z0-9]+)")
PATH_RE = re.compile(r'"(/(?:[^"\\]|\\.)*)"')
TOKEN_RE = re.compile(r"\b(?:AF|AT|CLOCK|CLONE|EPOLL|FUTEX|F_|MADV|MAP|MSG|O|POLL|PROT|PR|RLIMIT|SA|SCHED|SIG|SOCK|SOL|W)[A-Z0-9_]*\b")
FAMILIES = {
    "descriptors": {
        "close",
        "dup",
        "dup2",
        "dup3",
        "fcntl",
        "ioctl",
        "pipe",
        "pipe2",
        "read",
        "readv",
        "write",
        "writev",
    },
    "files": {
        "access",
        "faccessat",
        "faccessat2",
        "fstat",
        "getcwd",
        "getdents64",
        "lseek",
        "newfstatat",
        "open",
        "openat",
        "readlink",
        "readlinkat",
        "stat",
        "statx",
    },
    "mappings": {"brk", "madvise", "mmap", "mprotect", "mremap", "munmap"},
    "polling": {"epoll_create1", "epoll_ctl", "epoll_pwait", "epoll_wait", "poll", "ppoll", "pselect6", "select"},
    "process_queries": {"getegid", "geteuid", "getgid", "getpid", "getppid", "gettid", "prlimit64", "sched_getaffinity", "uname"},
    "signals": {"kill", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "sigaltstack", "tgkill", "tkill"},
    "threads": {"clone", "clone3", "exit", "futex", "rseq", "sched_yield", "set_robust_list", "set_tid_address"},
    "time": {"clock_getres", "clock_gettime", "clock_nanosleep", "gettimeofday", "nanosleep"},
}


class BeamHostError(RuntimeError):
    """Raised when a trace or contract invariant fails."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BeamHostError(f"cannot read {path}: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 1800,
    expected: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    if result.returncode not in expected:
        raise BeamHostError(
            f"command failed ({result.returncode}): {' '.join(argv)}\n{result.stdout[-8000:]}"
        )
    return result


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise BeamHostError(f"required host tool is missing: {name}")
    return path


def runtime_environment(root: Path) -> dict[str, str]:
    home = root / OUTPUT_ROOT / "home"
    home.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.update(
        {
            "ERL_ROOTDIR": str(root / OTP_ROOT),
            "ERL_FLAGS": "+S 2:2 +SDcpu 1:1 +SDio 1 +A 1",
            "HEX_HOME": str(home / ".hex"),
            "HEX_OFFLINE": "1",
            "HOME": str(home),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "MIX_HOME": str(home / ".mix"),
            "TZ": "UTC",
        }
    )
    environment["PATH"] = os.pathsep.join(
        [str(root / OTP_BIN), str(root / ELIXIR_BIN), environment.get("PATH", "")]
    )
    return environment


def ensure_runtime(root: Path) -> dict[str, Any]:
    erl = root / OTP_BIN / "erl"
    elixir = root / ELIXIR_BIN / "elixir"
    if not erl.is_file() or not elixir.is_file():
        run(["./scripts/toolchain-bootstrap.sh"], cwd=root, timeout=7200)
    environment = runtime_environment(root)
    otp = run(
        [str(erl), "-noshell", "-eval", 'io:format("~s/~s", [erlang:system_info(otp_release), erlang:system_info(version)]), halt().'],
        cwd=root,
        env=environment,
        timeout=30,
    ).stdout
    elixir_version = run([str(elixir), "--short-version"], cwd=root, env=environment, timeout=30).stdout.strip()
    if otp != "29/17.0.5" or elixir_version != "1.20.4":
        raise BeamHostError(f"pinned runtime differs: otp/erts={otp!r}, elixir={elixir_version!r}")
    beam = root / OTP_ROOT / "erts-17.0.5/bin/beam.smp"
    return {
        "otp": "29.0.5",
        "erts": "17.0.5",
        "elixir": "1.20.4",
        "beam_path": str(beam.relative_to(root)),
        "beam_sha256": sha256(beam),
    }


def build_fault_probe(root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            require_tool("cc"),
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-pthread",
            str(root / FAULT_SOURCE),
            "-o",
            str(output),
        ],
        cwd=root,
    )


def strace_argv(prefix: Path, command: list[str]) -> list[str]:
    return [
        require_tool("strace"),
        "-ff",
        "-qq",
        "-ttt",
        "-T",
        "-yy",
        "-s",
        "256",
        "-o",
        str(prefix),
        *command,
    ]


def proc_executable(pid: int) -> str | None:
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except OSError:
        return None


def wait_for_beam(beam: Path, previous: set[int], deadline: float) -> int:
    expected = str(beam.resolve())
    while time.monotonic() < deadline:
        for process in Path("/proc").iterdir():
            if not process.name.isdigit():
                continue
            pid = int(process.name)
            if pid not in previous and proc_executable(pid) == expected:
                return pid
        time.sleep(0.02)
    raise BeamHostError("timed out waiting for the pinned beam.smp process")


def wait_for_output(path: Path, marker: str, deadline: float) -> None:
    while time.monotonic() < deadline:
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
            return
        time.sleep(0.02)
    raise BeamHostError(f"timed out waiting for runtime event: {marker}")


def snapshot_beam(pid: int, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True)
    proc = Path(f"/proc/{pid}")
    for name in ("auxv", "cmdline", "environ", "limits", "maps", "mountinfo", "smaps_rollup", "status"):
        source = proc / name
        if source.is_file():
            shutil.copyfile(source, destination / name)
    descriptors: list[str] = []
    for descriptor in sorted((proc / "fd").iterdir(), key=lambda path: int(path.name)):
        try:
            target = os.readlink(descriptor)
        except OSError:
            target = "<unreadable>"
        descriptors.append(f"{descriptor.name} {target}")
    (destination / "descriptors.txt").write_text("\n".join(descriptors) + "\n", encoding="utf-8")
    threads: list[dict[str, Any]] = []
    for task in sorted((proc / "task").iterdir(), key=lambda path: int(path.name)):
        name = (task / "comm").read_text(encoding="utf-8").strip()
        status = (task / "status").read_text(encoding="utf-8")
        state = next(line.split(":", 1)[1].strip() for line in status.splitlines() if line.startswith("State:"))
        threads.append({"name": name, "state": state})
    snapshot = {"descriptor_count": len(descriptors), "thread_count": len(threads), "threads": threads}
    (destination / "snapshot.json").write_text(canonical_json(snapshot), encoding="utf-8")
    return snapshot


def run_boot_shutdown(
    root: Path,
    directory: Path,
    environment: dict[str, str],
    beam: Path,
) -> dict[str, Any]:
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    previous = {
        int(process.name)
        for process in Path("/proc").iterdir()
        if process.name.isdigit() and proc_executable(int(process.name)) == str(beam.resolve())
    }
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            strace_argv(directory / "raw", [str(root / ELIXIR_BIN / "mix"), "run", "--no-halt"]),
            cwd=root / RUNTIME_LAB,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        try:
            pid = wait_for_beam(beam, previous, time.monotonic() + 15)
            wait_for_output(stdout_path, "type=application_started", time.monotonic() + 15)
            snapshot = snapshot_beam(pid, directory / "process")
            os.kill(pid, signal.SIGTERM)
            status = process.wait(timeout=15)
        except BaseException:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
            raise
    stdout_text = stdout_path.read_text(encoding="utf-8")
    if status not in (0, -signal.SIGTERM) or "type=application_started" not in stdout_text or "type=application_stopped" not in stdout_text:
        raise BeamHostError(f"controlled runtime shutdown failed with status {status}")
    return snapshot


def decode_trace_path(encoded: str, root: Path) -> str:
    value = bytes(encoded, "utf-8").decode("unicode_escape").replace("\0", "")
    value = value.replace(str(root), "$REPO")
    value = re.sub(r"/replay-\d+", "/replay-$N", value)
    value = re.sub(r"/proc/\d+", "/proc/$PID", value)
    value = re.sub(r"/port_\d+$", "/port_$PORT", value)
    value = re.sub(r"^/tmp/mix_user_check_[^/]+$", "/tmp/mix_user_check_$TOKEN", value)
    return value


def trace_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.iterdir() if path.name.startswith("raw.") and path.is_file())


def summarize_scenario(directory: Path, root: Path) -> dict[str, Any]:
    syscalls: collections.Counter[str] = collections.Counter()
    errors: dict[str, set[str]] = collections.defaultdict(set)
    tokens: dict[str, set[str]] = collections.defaultdict(set)
    signals: set[str] = set()
    paths: set[str] = set()
    files = trace_files(directory)
    if not files:
        raise BeamHostError(f"no raw strace files in {directory}")
    for path in files:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = SYSCALL_RE.match(line)
            if match:
                syscall = match.group(1)
                syscalls[syscall] += 1
                error = ERROR_RE.search(line)
                if error and syscall != "rt_sigreturn":
                    errors[syscall].add(error.group(1))
                tokens[syscall].update(TOKEN_RE.findall(line))
            signal_match = SIGNAL_RE.search(line)
            if signal_match:
                signals.add(signal_match.group(1))
            for encoded in PATH_RE.findall(line):
                paths.add(decode_trace_path(encoded, root))
    syscall_names = set(syscalls)
    families = {
        family: sorted(syscall_names & members)
        for family, members in FAMILIES.items()
        if syscall_names & members
    }
    return {
        "trace_files": len(files),
        "syscall_counts": dict(sorted(syscalls.items())),
        "syscalls": sorted(syscalls),
        "errors": {name: sorted(values) for name, values in sorted(errors.items())},
        "argument_tokens": {name: sorted(values) for name, values in sorted(tokens.items()) if values},
        "signals": sorted(signals),
        "paths": sorted(paths),
        "families": families,
    }


def normalized_replay(summary: dict[str, Any]) -> dict[str, Any]:
    scenarios: dict[str, Any] = {}
    for name, value in summary["scenarios"].items():
        scenarios[name] = {
            key: value[key]
            for key in ("syscalls", "errors", "argument_tokens", "signals", "paths", "families")
        }
    return {"schema": "rust-beam/beam-host-normalized/v1", "scenarios": scenarios}


def gzip_raw_traces(replay: Path) -> Path:
    destination = replay / "raw-strace.txt.gz"
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as compressed:
            for scenario in ("boot-shutdown", "fault", "workload"):
                for index, path in enumerate(trace_files(replay / scenario), 1):
                    compressed.write(f"[{scenario}/trace-{index:03d}]\n".encode())
                    compressed.write(path.read_bytes())
    return destination


def run_replay(root: Path, output: Path, replay_number: int, environment: dict[str, str], beam: Path, fault: Path) -> dict[str, Any]:
    replay = output / f"replay-{replay_number}"
    replay.mkdir(parents=True)
    runtime_lab = root / RUNTIME_LAB

    workload = replay / "workload"
    workload.mkdir()
    result = run(
        strace_argv(
            workload / "raw",
            [
                str(root / ELIXIR_BIN / "mix"),
                "run",
                "-e",
                "RuntimeLab.Command.main(System.argv())",
                "--",
                "all",
                "--seed",
                "20260901",
            ],
        ),
        cwd=runtime_lab,
        env=environment,
        timeout=120,
    )
    (workload / "output.txt").write_text(result.stdout, encoding="utf-8")
    if "type=command_result" not in result.stdout or "seed=20260901" not in result.stdout:
        raise BeamHostError("runtime_lab workload did not emit its deterministic completion event")

    fault_directory = replay / "fault"
    fault_directory.mkdir()
    fault_result_path = fault_directory / "result.json"
    run(
        strace_argv(fault_directory / "raw", [str(fault), str(fault_result_path)]),
        cwd=root,
        timeout=30,
    )
    fault_result = load_json(fault_result_path)
    if fault_result.get("status") != "pass" or len(fault_result) != 11:
        raise BeamHostError(f"fault probe result differs: {fault_result}")

    boot = replay / "boot-shutdown"
    boot.mkdir()
    snapshot = run_boot_shutdown(root, boot, environment, beam)

    summary = {
        "schema": "rust-beam/beam-host-replay/v1",
        "replay": replay_number,
        "fault_probe": fault_result,
        "boot_snapshot": snapshot,
        "scenarios": {
            name: summarize_scenario(replay / name, root)
            for name in ("boot-shutdown", "fault", "workload")
        },
    }
    (replay / "summary.json").write_text(canonical_json(summary), encoding="utf-8")
    normalized = normalized_replay(summary)
    (replay / "normalized.json").write_text(canonical_json(normalized), encoding="utf-8")
    archive = gzip_raw_traces(replay)
    for scenario in ("boot-shutdown", "fault", "workload"):
        for path in trace_files(replay / scenario):
            path.unlink()
    summary["normalized_sha256"] = sha256(replay / "normalized.json")
    summary["raw_strace_sha256"] = sha256(archive)
    return summary


def git_identity(root: Path) -> dict[str, Any]:
    revision = run(["git", "rev-parse", "HEAD"], cwd=root, timeout=20).stdout.strip()
    dirty = bool(run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, timeout=20).stdout.strip())
    return {"revision": revision, "dirty": dirty}


def trace_reference(root: Path, output: Path) -> Path:
    require_tool("strace")
    runtime = ensure_runtime(root)
    environment = runtime_environment(root)
    run([str(root / ELIXIR_BIN / "mix"), "compile", "--warnings-as-errors"], cwd=root / RUNTIME_LAB, env=environment)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    fault = output / "fault-probe"
    build_fault_probe(root, fault)
    beam = root / runtime["beam_path"]
    replays = [run_replay(root, output, number, environment, beam, fault) for number in (1, 2)]
    first = load_json(output / "replay-1/normalized.json")
    second = load_json(output / "replay-2/normalized.json")
    if first != second:
        raise BeamHostError("normalized host interaction traces differ between replays")
    all_syscalls = sorted(
        {
            syscall
            for replay in replays
            for scenario in replay["scenarios"].values()
            for syscall in scenario["syscalls"]
        }
    )
    aggregate = {
        "schema": "rust-beam/beam-host-trace/v1",
        "status": "pass",
        "runtime": runtime,
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "git": git_identity(root),
        "strace": run(["strace", "--version"], cwd=root, timeout=20).stdout.splitlines()[0],
        "runtime_lab_seed": 20260901,
        "runtime_flags": environment["ERL_FLAGS"],
        "replays": [
            {
                "number": value["replay"],
                "normalized_sha256": value["normalized_sha256"],
                "raw_strace_sha256": value["raw_strace_sha256"],
                "thread_count": value["boot_snapshot"]["thread_count"],
                "descriptor_count": value["boot_snapshot"]["descriptor_count"],
            }
            for value in replays
        ],
        "normalized_equal": True,
        "observed_syscalls": all_syscalls,
        "scenarios": ["boot", "stress", "crash", "shutdown", "allocation", "copy", "timeout", "cancellation", "signal", "close", "thread-start", "thread-exit"],
    }
    aggregate_path = output / "aggregate.json"
    aggregate_path.write_text(canonical_json(aggregate), encoding="utf-8")
    print(
        f"beam-host trace: PASS replays=2 syscalls={len(all_syscalls)} "
        f"threads={aggregate['replays'][0]['thread_count']}"
    )
    return aggregate_path


def source_archive(root: Path, source_id: str) -> Path:
    result = run(
        [sys.executable, "scripts/toolchain.py", "path", source_id, "--cache", "target/toolchain-cache"],
        cwd=root,
        timeout=30,
    )
    path = Path(result.stdout.strip())
    if not path.is_file():
        raise BeamHostError(f"sealed source is missing: {source_id}")
    return path


def verify_source_inventory(root: Path, contract: dict[str, Any]) -> None:
    archives: dict[str, tarfile.TarFile] = {}
    try:
        for item in contract["source_inventory"]:
            source_id = item["source"]
            if source_id not in archives:
                archives[source_id] = tarfile.open(source_archive(root, source_id))
            archive = archives[source_id]
            members = [member for member in archive.getmembers() if member.name.endswith("/" + item["path"])]
            if len(members) != 1:
                raise BeamHostError(f"source inventory path is absent or ambiguous: {source_id}:{item['path']}")
            stream = archive.extractfile(members[0])
            if stream is None:
                raise BeamHostError(f"source inventory path is not a file: {source_id}:{item['path']}")
            text = stream.read().decode("utf-8", errors="replace")
            missing = [symbol for symbol in item["symbols"] if symbol not in text]
            if missing:
                raise BeamHostError(f"source symbols missing from {item['path']}: {missing}")
    finally:
        for archive in archives.values():
            archive.close()


def validate_contract(root: Path) -> None:
    contract = load_json(root / CONTRACT_PATH)
    if contract.get("schema") != "rust-beam/beam-host-contract/v1" or contract.get("revision") != 0:
        raise BeamHostError("beam-host contract schema or revision differs")
    if contract.get("target") != "aarch64-linux-musl" or contract.get("runtime") != {
        "otp": "29.0.5",
        "erts": "17.0.5",
        "libc": "musl-1.2.5",
    }:
        raise BeamHostError("beam-host target runtime differs")
    if contract.get("unresolved") != []:
        raise BeamHostError("beam-host contract contains unresolved interactions")
    interactions = contract.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        raise BeamHostError("beam-host contract interactions are absent")
    families = contract.get("families")
    if not isinstance(families, dict) or not families:
        raise BeamHostError("beam-host contract families are absent")
    allowed = {"required", "optional/disabled", "build-time-only", "unexplained"}
    by_syscall: dict[str, dict[str, Any]] = {}
    required_count = 0
    for item in interactions:
        syscall = item.get("syscall")
        classification = item.get("classification")
        if not isinstance(syscall, str) or syscall in by_syscall or classification not in allowed:
            raise BeamHostError(f"invalid or duplicate contract interaction: {item}")
        by_syscall[syscall] = item
        if classification == "unexplained":
            raise BeamHostError(f"unexplained interaction remains: {syscall}")
        if classification == "required":
            required_count += 1
            family = families.get(item.get("family"))
            if not isinstance(family, dict):
                raise BeamHostError(f"required {syscall} names an unknown family")
            effective = {**family, **item}
            for field in ("callers", "operations", "semantics", "errors", "blocking", "evidence", "tests"):
                if not effective.get(field):
                    raise BeamHostError(f"required {syscall} has no {field}")
    for source in contract["source_inventory"]:
        missing = sorted(set(source["interactions"]) - set(by_syscall))
        if missing:
            raise BeamHostError(f"source inventory interactions are unclassified: {missing}")
    verify_source_inventory(root, contract)

    observed_sets: list[tuple[str, set[str]]] = []
    target = root / TARGET_AGGREGATE
    if target.is_file():
        observed_sets.append(("AArch64-musl full-system", set(load_json(target)["observed_syscalls"])))
    host = root / OUTPUT_ROOT / "aggregate.json"
    if host.is_file():
        observed_sets.append(("x86_64 host reference", set(load_json(host)["observed_syscalls"])))
    for source, observed in observed_sets:
        missing = sorted(observed - set(by_syscall))
        if missing:
            raise BeamHostError(f"{source} syscalls are unclassified: {missing}")
    print(
        f"beam-host contract: PASS revision=0 required={required_count} "
        f"classified={len(interactions)} source_items={len(contract['source_inventory'])}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    trace = subparsers.add_parser("trace", help="capture and compare two host-runtime replays")
    trace.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    subparsers.add_parser("validate", help="validate revision 0 and available observations")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        if arguments.command == "trace":
            output = arguments.output if arguments.output.is_absolute() else root / arguments.output
            trace_reference(root, output)
        else:
            validate_contract(root)
    except (BeamHostError, OSError, subprocess.TimeoutExpired) as error:
        print(f"beam-host: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
