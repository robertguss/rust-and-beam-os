#!/usr/bin/env python3
"""Run the sealed static AArch64 ERTS artifact in a full-system Linux TCG guest."""

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
import stat
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


PROFILE_PATH = Path("toolchain/erts-linux/aarch64-tcg.json")
OTP_PROFILE_PATH = Path("toolchain/otp/aarch64-linux-musl.json")
WORK_ROOT = Path("target/erts-linux-reference")
CACHE_ROOT = Path("target/toolchain-cache/sha256")
BEAM_PATH = Path("target/otp-aarch64/primary/release/erts-17.0.5/bin/beam.smp")
RELEASE_PATH = Path("target/otp-aarch64/primary/release")
QEMU_PATH = Path("target/qemu-11.1.0/build/qemu-system-aarch64")
SOURCE_FILES = (
    Path("tests/beam-host/fault_probe.c"),
    Path("tests/erts-linux/init.sh"),
    Path("tests/erts-linux/platform_probe.c"),
    Path("tests/erts-linux/rb_erts_workload.erl"),
)
SYSCALL_RE = re.compile(r"^(?:\d+\.\d+\s+)?([A-Za-z_][A-Za-z0-9_]*)\(")
PATH_RE = re.compile(r'"(/(?:[^"\\]|\\.)*)"')
ADDRESS_RE = re.compile(r"0x[0-9a-fA-F]+")
TIMESTAMP_RE = re.compile(r"^\d+\.\d+\s+")
SIGNAL_RE = re.compile(r"--- (SIG[A-Z0-9]+)")
AUXV_NAMES = {
    0: "AT_NULL",
    3: "AT_PHDR",
    4: "AT_PHENT",
    5: "AT_PHNUM",
    6: "AT_PAGESZ",
    7: "AT_BASE",
    8: "AT_FLAGS",
    9: "AT_ENTRY",
    11: "AT_UID",
    12: "AT_EUID",
    13: "AT_GID",
    14: "AT_EGID",
    16: "AT_HWCAP",
    17: "AT_CLKTCK",
    23: "AT_SECURE",
    25: "AT_RANDOM",
    26: "AT_HWCAP2",
    31: "AT_EXECFN",
    51: "AT_MINSIGSTKSZ",
}


class ReferenceError(RuntimeError):
    """Raised when preparation or a full-system acceptance invariant fails."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReferenceError(f"cannot read {path}: {error}") from error


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
    timeout: int = 1800,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        input=input_bytes,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=input_bytes is None,
        timeout=timeout,
    )
    if result.returncode != 0:
        output = result.stdout if isinstance(result.stdout, str) else result.stdout.decode(errors="replace")
        raise ReferenceError(f"command failed ({result.returncode}): {' '.join(argv)}\n{output[-8000:]}")
    return result  # type: ignore[return-value]


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        for directory in (Path("/usr/sbin"), Path("/sbin")):
            candidate = directory / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        raise ReferenceError(f"required host tool is missing: {name}")
    return path


def validate_profile(profile: Any) -> None:
    expected = {"schema", "alpine_release", "kernel_release", "sources", "qemu", "erts"}
    if not isinstance(profile, dict) or set(profile) != expected:
        raise ReferenceError("reference profile fields differ")
    if profile["schema"] != "rust-beam/erts-linux-reference-profile/v1":
        raise ReferenceError("unsupported reference profile schema")
    if profile["alpine_release"] != "3.22.5" or profile["kernel_release"] != "6.12.94-0-virt":
        raise ReferenceError("reference Linux identity changed")
    if list(profile["sources"]) != sorted(profile["sources"]):
        raise ReferenceError("reference sources must be sorted")
    for source_id, source in profile["sources"].items():
        if set(source) != {"url", "sha256", "size"}:
            raise ReferenceError(f"source fields differ for {source_id}")
        if not source["url"].startswith("https://"):
            raise ReferenceError(f"source URL is not HTTPS for {source_id}")
        if not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ReferenceError(f"source digest is invalid for {source_id}")
        if not isinstance(source["size"], int) or source["size"] <= 0:
            raise ReferenceError(f"source size is invalid for {source_id}")
    qemu = profile["qemu"]
    expected_qemu = {
        "version": "11.1.0",
        "machine": "virt-11.1",
        "cpu": "cortex-a53",
        "gic": "3",
        "accelerator": "tcg,thread=multi",
        "vcpus": 4,
        "memory_mib": 1024,
        "dtb_randomness": False,
    }
    if qemu != expected_qemu:
        raise ReferenceError("QEMU reference profile changed")
    erts = profile["erts"]
    if (
        erts.get("version") != "17.0.5"
        or erts.get("otp_release") != "29.0.5"
        or erts.get("single_scheduler_flags") != ["-S", "1:1", "-SDcpu", "1:1", "-SDio", "1", "-A", "1"]
        or erts.get("candidate_flags") != ["-S", "2:2", "-SDcpu", "1:1", "-SDio", "1", "-A", "1"]
        or not re.fullmatch(r"[0-9a-f]{64}", str(erts.get("beam_sha256", "")))
    ):
        raise ReferenceError("ERTS reference profile changed")


def load_profile(root: Path) -> dict[str, Any]:
    profile = load_json(root / PROFILE_PATH)
    validate_profile(profile)
    return profile


def source_cache_path(root: Path, source: dict[str, Any]) -> Path:
    return root / CACHE_ROOT / source["sha256"]


def fetch_sources(root: Path, profile: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for source_id, source in profile["sources"].items():
        path = source_cache_path(root, source)
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(f".{path.name}.tmp")
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
                    source["url"],
                    "--output",
                    str(temporary),
                ],
                cwd=root,
            )
            if temporary.stat().st_size != source["size"] or sha256(temporary) != source["sha256"]:
                temporary.unlink(missing_ok=True)
                raise ReferenceError(f"downloaded source differs for {source_id}")
            temporary.replace(path)
        if path.stat().st_size != source["size"] or sha256(path) != source["sha256"]:
            raise ReferenceError(f"cached source differs for {source_id}")
        paths[source_id] = path
    return paths


def ensure_qemu(root: Path, profile: dict[str, Any]) -> Path:
    run([sys.executable, "scripts/virtio_probe.py", "prepare", "--root", str(root)], cwd=root)
    binary = root / QEMU_PATH
    version = run([str(binary), "--version"], cwd=root, timeout=20).stdout.splitlines()[0]
    machines = run([str(binary), "-machine", "help"], cwd=root, timeout=20).stdout
    if f"version {profile['qemu']['version']}" not in version or profile["qemu"]["machine"] not in machines:
        raise ReferenceError("prepared QEMU does not match the reference profile")
    return binary


def ensure_otp(root: Path, profile: dict[str, Any]) -> Path:
    beam = root / BEAM_PATH
    if not beam.is_file():
        run(["./scripts/toolchain-bootstrap.sh"], cwd=root, timeout=7200)
        run([sys.executable, "scripts/otp_artifact.py", "build"], cwd=root, timeout=7200)
    if not beam.is_file() or sha256(beam) != profile["erts"]["beam_sha256"]:
        raise ReferenceError("P005 beam.smp is absent or differs from the sealed artifact")
    headers = run(["readelf", "-l", str(beam)], cwd=root, timeout=30).stdout
    dynamic = run(["readelf", "-d", str(beam)], cwd=root, timeout=30).stdout
    if "INTERP" in headers or "NEEDED" in dynamic or "There is no dynamic section" not in dynamic:
        raise ReferenceError("P005 beam.smp is not the sealed static executable")
    return beam


def build_c_probe(root: Path, source: Path, destination: Path) -> None:
    common = root / "target/otp-aarch64/common"
    clang = common / "llvm/bin/clang"
    sysroot = common / "sysroot"
    if not clang.is_file() or not (sysroot / "usr/lib/libc.a").is_file():
        raise ReferenceError("P005 pinned AArch64-musl cross toolchain is missing")
    run(
        [
            str(clang),
            "--target=aarch64-linux-musl",
            f"--sysroot={sysroot}",
            "-march=armv8-a",
            "-mno-outline-atomics",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-static",
            "-fuse-ld=lld",
            "-rtlib=compiler-rt",
            "--unwindlib=none",
            "-Wl,-z,max-page-size=4096",
            "-Wl,-z,common-page-size=4096",
            "-Wl,--build-id=none",
            "-pthread",
            str(root / source),
            "-o",
            str(destination),
        ],
        cwd=root,
    )


def build_workload(root: Path, destination: Path) -> None:
    erlc = root / "target/toolchain-smoke/install/otp/bin/erlc"
    erl_root = root / "target/toolchain-smoke/install/otp/lib/erlang"
    if not erlc.is_file():
        raise ReferenceError("pinned host OTP compiler is missing; run just toolchain-bootstrap")
    destination.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment["ERL_ROOTDIR"] = str(erl_root)
    run(
        [
            str(erlc),
            "+deterministic",
            "+no_debug_info",
            "-Werror",
            "-o",
            str(destination),
            str(root / "tests/erts-linux/rb_erts_workload.erl"),
        ],
        cwd=root,
        env=environment,
    )


def preparation_identity(root: Path, profile: dict[str, Any], qemu: Path, beam: Path) -> dict[str, Any]:
    return {
        "profile_sha256": sha256(root / PROFILE_PATH),
        "sources": {source_id: source["sha256"] for source_id, source in profile["sources"].items()},
        "source_files": {str(path): sha256(root / path) for path in SOURCE_FILES},
        "beam_sha256": sha256(beam),
        "release_native_closure_sha256": sha256(
            root / "target/otp-aarch64/primary/inspection/native-closure.json"
        ),
        "qemu_sha256": sha256(qemu),
    }


def prepared_matches(root: Path, identity: dict[str, Any]) -> bool:
    receipt_path = root / WORK_ROOT / "provenance.json"
    initramfs = root / WORK_ROOT / "reference-initramfs.gz"
    if not receipt_path.is_file() or not initramfs.is_file():
        return False
    try:
        receipt = load_json(receipt_path)
    except ReferenceError:
        return False
    return (
        receipt.get("schema") == "rust-beam/erts-linux-preparation/v1"
        and receipt.get("identity") == identity
        and receipt.get("outputs", {}).get("initramfs_sha256") == sha256(initramfs)
    )


def set_tree_mtime(root: Path, epoch: int) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        os.utime(path, (epoch, epoch), follow_symlinks=False)
    os.utime(root, (epoch, epoch), follow_symlinks=False)


def pack_initramfs(root: Path, source: Path, destination: Path) -> None:
    listing = subprocess.run(
        ["bash", "-c", "find . -print0 | LC_ALL=C sort -z"],
        cwd=source,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    cpio = subprocess.Popen(
        ["cpio", "--null", "--create", "--format=newc", "--reproducible", "--owner=0:0", "--quiet"],
        cwd=source,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    cpio_output, cpio_error = cpio.communicate(listing)
    if cpio.returncode != 0:
        raise ReferenceError(f"cpio failed: {cpio_error.decode(errors='replace')}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as compressed:
            compressed.write(cpio_output)


def extract_concatenated_newc(source: Path, destination: Path) -> None:
    """Extract every concatenated newc archive in an Alpine initramfs."""
    data = gzip.decompress(source.read_bytes())
    offset = 0
    archives = 0
    while offset < len(data):
        while offset < len(data) and data[offset] == 0:
            offset += 1
        if offset == len(data):
            break
        if data[offset : offset + 6] not in (b"070701", b"070702"):
            raise ReferenceError(f"unexpected data between initramfs archives at offset {offset}")
        archives += 1
        hardlinks: dict[tuple[int, int, int], Path] = {}
        while True:
            if data[offset : offset + 6] not in (b"070701", b"070702") or offset + 110 > len(data):
                raise ReferenceError(f"invalid newc header at offset {offset}")
            try:
                fields = [int(data[offset + 6 + index * 8 : offset + 14 + index * 8], 16) for index in range(13)]
            except ValueError as error:
                raise ReferenceError(f"invalid newc field at offset {offset}") from error
            inode, mode, _uid, _gid, links, _mtime, size, dev_major, dev_minor, _rdev_major, _rdev_minor, name_size, _check = fields
            name_start = offset + 110
            name_end = name_start + name_size
            if name_size == 0 or name_end > len(data) or data[name_end - 1] != 0:
                raise ReferenceError(f"invalid newc name at offset {offset}")
            name = data[name_start : name_end - 1].decode("utf-8", errors="strict")
            content_start = (name_end + 3) & ~3
            content_end = content_start + size
            if content_end > len(data):
                raise ReferenceError(f"truncated newc content for {name}")
            offset = (content_end + 3) & ~3
            if name == "TRAILER!!!":
                break
            relative = Path(name.lstrip("/"))
            if name in ("", "."):
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise ReferenceError(f"unsafe initramfs path: {name}")
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            file_type = stat.S_IFMT(mode)
            permissions = stat.S_IMODE(mode)
            if file_type == stat.S_IFDIR:
                path.mkdir(exist_ok=True)
                path.chmod(permissions)
            elif file_type == stat.S_IFLNK:
                path.unlink(missing_ok=True)
                path.symlink_to(data[content_start:content_end].decode("utf-8", errors="strict"))
            elif file_type == stat.S_IFREG:
                path.unlink(missing_ok=True)
                link_key = (dev_major, dev_minor, inode)
                if links > 1 and link_key in hardlinks:
                    anchor = hardlinks[link_key]
                    if size > 0:
                        anchor.write_bytes(data[content_start:content_end])
                        anchor.chmod(permissions)
                    os.link(anchor, path)
                else:
                    path.write_bytes(data[content_start:content_end])
                    path.chmod(permissions)
                    if links > 1:
                        hardlinks[link_key] = path
            elif file_type not in (stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK):
                raise ReferenceError(f"unsupported initramfs entry type for {name}")
    if archives < 1 or not (destination / "bin/busybox").is_file():
        raise ReferenceError("Alpine initramfs extraction did not produce busybox")


def extract_apk_payload(root: Path, source: Path, build_directory: Path, destination: Path) -> None:
    build_directory.mkdir()
    run(["tar", "-xzf", str(source), "-C", str(build_directory)], cwd=root)
    for subtree in ("lib", "usr"):
        package_subtree = build_directory / subtree
        if package_subtree.exists():
            shutil.copytree(package_subtree, destination / subtree, dirs_exist_ok=True, symlinks=True)


def prepare_reference(root: Path) -> dict[str, Path]:
    profile = load_profile(root)
    for tool in ("cpio", "unsquashfs", "readelf"):
        require_tool(tool)
    sources = fetch_sources(root, profile)
    qemu = ensure_qemu(root, profile)
    beam = ensure_otp(root, profile)
    identity = preparation_identity(root, profile, qemu, beam)
    initramfs = root / WORK_ROOT / "reference-initramfs.gz"
    provenance = root / WORK_ROOT / "provenance.json"
    if prepared_matches(root, identity):
        print(f"erts-linux: using prepared {initramfs.relative_to(root)}")
        return {"qemu": qemu, "kernel": sources["alpine-aarch64-kernel"], "initramfs": initramfs}

    build_root = root / WORK_ROOT / "build"
    shutil.rmtree(build_root, ignore_errors=True)
    guest_root = build_root / "root"
    guest_root.mkdir(parents=True)
    extract_concatenated_newc(sources["alpine-aarch64-initramfs"], guest_root)

    modloop = build_root / "modloop"
    run(
        ["unsquashfs", "-quiet", "-d", str(modloop), str(sources["alpine-aarch64-modloop"])],
        cwd=root,
    )
    modules = guest_root / "lib/modules" / profile["kernel_release"]
    shutil.rmtree(modules, ignore_errors=True)
    shutil.copytree(modloop / "modules" / profile["kernel_release"], modules, symlinks=True)

    apk_sources = (
        "alpine-aarch64-libbz2",
        "alpine-aarch64-libdw",
        "alpine-aarch64-libelf",
        "alpine-aarch64-musl-fts",
        "alpine-aarch64-strace",
    )
    for source_id in apk_sources:
        extract_apk_payload(root, sources[source_id], build_root / f"{source_id}-apk", guest_root)

    shutil.copytree(root / RELEASE_PATH, guest_root / "otp", symlinks=True)
    probe = guest_root / "probe"
    probe.mkdir()
    build_c_probe(root, Path("tests/erts-linux/platform_probe.c"), probe / "platform_probe")
    build_c_probe(root, Path("tests/beam-host/fault_probe.c"), probe / "beam_host_fault_probe")
    build_workload(root, probe)
    shutil.copy2(root / "tests/erts-linux/init.sh", guest_root / "init")
    (guest_root / "init").chmod(0o755)
    (guest_root / "etc/hosts").write_text("127.0.0.1 localhost rb-erts-reference\n::1 localhost\n")
    (guest_root / "etc/resolv.conf").write_text("# Network services are disabled in this guest.\n")

    source_epoch = load_json(root / OTP_PROFILE_PATH)["source_date_epoch"]
    set_tree_mtime(guest_root, source_epoch)
    pack_initramfs(root, guest_root, initramfs)
    receipt = {
        "schema": "rust-beam/erts-linux-preparation/v1",
        "identity": identity,
        "alpine_release": profile["alpine_release"],
        "kernel_release": profile["kernel_release"],
        "strace_version": "6.13-r0",
        "outputs": {
            "initramfs_path": str(initramfs.relative_to(root)),
            "initramfs_sha256": sha256(initramfs),
            "initramfs_size": initramfs.stat().st_size,
            "kernel_path": str(sources["alpine-aarch64-kernel"].relative_to(root)),
            "kernel_sha256": sha256(sources["alpine-aarch64-kernel"]),
            "fault_probe_sha256": sha256(probe / "beam_host_fault_probe"),
            "platform_probe_sha256": sha256(probe / "platform_probe"),
            "workload_beam_sha256": sha256(probe / "rb_erts_workload.beam"),
        },
    }
    provenance.write_text(canonical_json(receipt), encoding="utf-8")
    print(f"erts-linux: prepared {initramfs.relative_to(root)}")
    return {"qemu": qemu, "kernel": sources["alpine-aarch64-kernel"], "initramfs": initramfs}


def qemu_argv(qemu: Path, kernel: Path, initramfs: Path, image: Path, serial: Path) -> list[str]:
    return [
        str(qemu),
        "-machine",
        "virt-11.1,gic-version=3,dtb-randomness=off",
        "-cpu",
        "cortex-a53",
        "-accel",
        "tcg,thread=multi",
        "-smp",
        "4",
        "-m",
        "1024",
        "-nodefaults",
        "-no-reboot",
        "-display",
        "none",
        "-serial",
        f"file:{serial}",
        "-kernel",
        str(kernel),
        "-initrd",
        str(initramfs),
        "-append",
        "console=ttyAMA0 rdinit=/init panic=-1 quiet loglevel=4",
        "-drive",
        f"file={image},format=raw,if=none,id=work,cache=unsafe",
        "-device",
        "virtio-blk-device,drive=work",
    ]


def normalize_serial(path: Path) -> None:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    path.write_bytes(data)


def parse_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def parse_proc_status(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key] = value.strip()
    return values


def parse_auxv(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) % 16 != 0:
        raise ReferenceError(f"invalid AArch64 auxv length: {path}")
    values: dict[str, int] = {}
    for offset in range(0, len(data), 16):
        kind, value = struct.unpack_from("<QQ", data, offset)
        name = AUXV_NAMES.get(kind, f"AT_{kind}")
        values[name] = value
        if kind == 0:
            break
    return values


def parse_nul_strings(path: Path) -> list[str]:
    return [part.decode(errors="replace") for part in path.read_bytes().split(b"\0") if part]


def normalize_trace_line(line: str) -> str:
    line = TIMESTAMP_RE.sub("", line.rstrip())
    return ADDRESS_RE.sub("0xADDR", line)


def trace_summary(trace_dir: Path, normalized_path: Path) -> dict[str, Any]:
    counts: collections.Counter[str] = collections.Counter()
    signals: collections.Counter[str] = collections.Counter()
    paths: set[str] = set()
    normalized: list[str] = []
    trace_files = sorted(path for path in trace_dir.iterdir() if path.is_file())
    if not trace_files:
        raise ReferenceError(f"no strace files in {trace_dir}")
    for index, path in enumerate(trace_files, 1):
        normalized.append(f"[trace-{index:03d}]")
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = SYSCALL_RE.match(line)
            if match:
                counts[match.group(1)] += 1
            signal = SIGNAL_RE.search(line)
            if signal:
                signals[signal.group(1)] += 1
            for encoded in PATH_RE.findall(line):
                paths.add(bytes(encoded, "utf-8").decode("unicode_escape").replace("\0", ""))
            normalized.append(normalize_trace_line(line))
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    with normalized_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as stream:
            stream.write(("\n".join(normalized) + "\n").encode())
    return {
        "trace_files": len(trace_files),
        "syscalls": dict(sorted(counts.items())),
        "signals": dict(sorted(signals.items())),
        "paths": sorted(paths),
        "normalized_trace_sha256": sha256(normalized_path),
    }


def parse_thread_topology(profile_dir: Path) -> dict[str, Any]:
    tasks = profile_dir / "tasks"
    threads: list[dict[str, Any]] = []
    for task in sorted(tasks.iterdir(), key=lambda path: int(path.name)):
        status = parse_proc_status(task / "status")
        threads.append(
            {
                "tid": int(task.name),
                "name": (task / "comm").read_text(encoding="utf-8").strip(),
                "state": status.get("State"),
                "cpus_allowed_list": status.get("Cpus_allowed_list"),
                "signal_blocked": status.get("SigBlk"),
                "signal_ignored": status.get("SigIgn"),
                "signal_caught": status.get("SigCgt"),
            }
        )
    if not threads:
        raise ReferenceError(f"no native threads captured for {profile_dir.name}")
    names = collections.Counter(thread["name"] for thread in threads)
    return {"count": len(threads), "name_counts": dict(sorted(names.items())), "threads": threads}


def normalize_mappings(profile_dirs: dict[str, Path], destination: Path) -> None:
    lines: list[str] = []
    for profile, directory in profile_dirs.items():
        lines.append(f"[{profile}]")
        for line in (directory / "maps").read_text(encoding="utf-8").splitlines():
            lines.append(ADDRESS_RE.sub("ADDR", line))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mapping_summary(profile_dirs: dict[str, Path]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for profile, directory in profile_dirs.items():
        file_paths: set[str] = set()
        for line in (directory / "maps").read_text(encoding="utf-8").splitlines():
            fields = line.split(maxsplit=5)
            if len(fields) == 6 and fields[5].startswith("/"):
                file_paths.add(fields[5])
        shared_objects = sorted(path for path in file_paths if re.search(r"\.so(?:\.|$)", path))
        result[profile] = {
            "file_paths": sorted(file_paths),
            "shared_objects": shared_objects,
        }
    return result


def file_access_summary(paths: list[str]) -> dict[str, list[str]]:
    classes: dict[str, list[str]] = {
        "required_runtime": [],
        "removable_harness": [],
        "optional_absent": [],
        "forbidden": [],
    }
    for path in paths:
        if path.endswith("/.erlang"):
            category = "optional_absent"
        elif path.startswith(("/probe", "/work", "/tmp")):
            category = "removable_harness"
        elif path == "/" or path.startswith(("/otp", "/bin/sh", "/dev/", "/etc/hosts", "/proc/", "/sys")):
            category = "required_runtime"
        else:
            category = "forbidden"
        classes[category].append(path)
    return classes


def contract_comparison(root: Path, syscalls: set[str]) -> dict[str, Any]:
    contract = root / "abi/beam-host.yaml"
    if not contract.is_file():
        return {
            "status": "pending",
            "contract": "abi/beam-host.yaml revision 0",
            "reason": "RB-T-P004 has not yet produced the source-plus-trace host contract",
            "observed_syscalls": sorted(syscalls),
        }
    value = load_json(contract)
    if value.get("schema") != "rust-beam/beam-host-contract/v1" or value.get("revision") != 0:
        raise ReferenceError("abi/beam-host.yaml is not revision 0")
    classified = {
        item.get("syscall")
        for item in value.get("interactions", [])
        if item.get("classification") in {"required", "optional/disabled", "build-time-only"}
    }
    missing = sorted(syscalls - classified)
    return {
        "status": "pass" if not missing else "mismatch",
        "contract": "abi/beam-host.yaml revision 0",
        "observed_syscalls": sorted(syscalls),
        "unmapped_syscalls": missing,
    }


def validate_workload(profile: str, value: dict[str, Any]) -> None:
    expected_schedulers = 1 if profile == "single" else 2
    required_true = ("process_message", "timer", "ets", "forced_gc")
    if (
        value.get("schema") != "rust-beam/erts-workload/v1"
        or value.get("profile") != profile
        or value.get("otp_release") != "29"
        or value.get("erts_version") != "17.0.5"
        or value.get("emu_flavor") != "emu"
        or value.get("schedulers") != expected_schedulers
        or value.get("schedulers_online") != expected_schedulers
        or value.get("dirty_cpu_schedulers") != 1
        or value.get("dirty_cpu_schedulers_online") != 1
        or value.get("dirty_io_schedulers") != 1
        or value.get("async_threads") != 1
        or value.get("binary_bytes") != 262144
        or not all(value.get(name) is True for name in required_true)
    ):
        raise ReferenceError(f"{profile} workload result differs: {value}")


def validate_platform(value: dict[str, Any]) -> None:
    if (
        value.get("schema") != "rust-beam/erts-linux-platform/v1"
        or value.get("sysname") != "Linux"
        or value.get("machine") != "aarch64"
        or value.get("release") != "6.12.94-0-virt"
        or value.get("page_size") != 4096
        or value.get("configured_cpus") != 4
        or value.get("online_cpus") != 4
        or value.get("hwcap_fp") is not True
        or value.get("hwcap_asimd") is not True
        or value.get("hwcap_atomics") is not False
        or value.get("signal_on_altstack") is not True
        or value.get("signal_context_magic") != 0x46508001
    ):
        raise ReferenceError(f"full-system platform result differs: {value}")


def memory_summary(profile_dir: Path) -> dict[str, Any]:
    status = parse_proc_status(profile_dir / "status")
    wanted = ("VmPeak", "VmSize", "VmHWM", "VmRSS", "RssAnon", "RssFile", "Threads")
    return {name: status.get(name) for name in wanted}


def network_summary(trace_dir: Path) -> dict[str, int]:
    external_connections = 0
    service_listeners = 0
    ephemeral_udp_binds = 0
    success = re.compile(r"\)\s+=\s+(?:0|[1-9][0-9]*)(?:<|\s|$)")
    for path in sorted(trace_dir.iterdir()):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not success.search(line):
                continue
            internet_address = "AF_INET" in line or "AF_INET6" in line
            if internet_address and "connect(" in line:
                external_connections += 1
            elif internet_address and "bind(" in line:
                if "sin_port=htons(0)" in line or "sin6_port=htons(0)" in line:
                    ephemeral_udp_binds += 1
                else:
                    service_listeners += 1
            elif "listen(" in line or "accept(" in line or "accept4(" in line:
                service_listeners += 1
    return {
        "external_connections": external_connections,
        "service_listeners": service_listeners,
        "ephemeral_udp_binds": ephemeral_udp_binds,
    }


def run_boot(
    root: Path,
    prepared: dict[str, Path],
    profile: dict[str, Any],
    output: Path,
    boot: int,
) -> dict[str, Any]:
    mkfs = require_tool("mkfs.ext4")
    debugfs = require_tool("debugfs")
    boot_dir = output / f"boot-{boot:02d}"
    boot_dir.mkdir(parents=True)
    image = boot_dir / "results.img"
    serial = boot_dir / "serial.log"
    qemu_log = boot_dir / "qemu.log"
    with image.open("wb") as stream:
        stream.truncate(256 * 1024 * 1024)
    run(
        [
            mkfs,
            "-q",
            "-F",
            "-O",
            "^has_journal",
            "-E",
            "lazy_itable_init=0,lazy_journal_init=0",
            "-U",
            "52554245-414d-4552-5453-000000000006",
            "-L",
            "RBERTS",
            str(image),
        ],
        cwd=root,
    )
    argv = qemu_argv(prepared["qemu"], prepared["kernel"], prepared["initramfs"], image, serial)
    started = time.monotonic()
    with qemu_log.open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run(
                argv,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=180,
            )
        except subprocess.TimeoutExpired as error:
            raise ReferenceError(f"full-system boot {boot} timed out") from error
    if result.returncode != 0:
        raise ReferenceError(f"QEMU boot {boot} exited with {result.returncode}")
    normalize_serial(serial)
    serial_text = serial.read_text(encoding="utf-8", errors="replace")
    required_serial = (
        "RB_GUEST event=minimal status=0",
        "RB_GUEST event=workload profile=single status=0",
        "RB_GUEST event=workload profile=candidate status=0",
        "RB_GUEST event=complete status=pass",
    )
    if "RB_GUEST event=fail" in serial_text or any(value not in serial_text for value in required_serial):
        raise ReferenceError(f"guest boot {boot} did not reach every milestone; see {serial}")

    run([debugfs, "-R", f"rdump /results {boot_dir}", str(image)], cwd=root)
    image.unlink()
    results = boot_dir / "results"
    guest_status = parse_key_values(results / "guest-status.txt")
    if guest_status != {
        "status": "pass",
        "fault": "0",
        "minimal": "0",
        "single": "0",
        "candidate": "0",
    }:
        raise ReferenceError(f"guest status differs: {guest_status}")
    platform_result = load_json(results / "platform.json")
    validate_platform(platform_result)
    fault_result = load_json(results / "fault-probe.json")
    if fault_result != {
        "schema": "rust-beam/beam-host-fault-probe/v1",
        "status": "pass",
        "allocation": "ENOMEM-or-EINVAL",
        "copy": "EFAULT",
        "timeout": "expired",
        "cancellation": "joined",
        "signal": "alternate-stack",
        "close": "EBADF",
        "thread_start": "created",
        "thread_exit": "joined",
        "shutdown": "normal",
    }:
        raise ReferenceError(f"fault probe result differs: {fault_result}")
    workloads = {name: load_json(results / f"workload-{name}.json") for name in ("single", "candidate")}
    for name, workload in workloads.items():
        validate_workload(name, workload)

    profile_dirs = {name: results / "profiles" / name for name in ("single", "candidate")}
    topologies = {name: parse_thread_topology(directory) for name, directory in profile_dirs.items()}
    if topologies["candidate"]["count"] <= topologies["single"]["count"]:
        raise ReferenceError("candidate profile did not create an additional scheduler thread")
    normalize_mappings(profile_dirs, boot_dir / "normalized-mappings.txt")
    mappings = mapping_summary(profile_dirs)
    if any(value["shared_objects"] for value in mappings.values()):
        raise ReferenceError("static ERTS unexpectedly mapped a shared object")

    trace = trace_summary(results / "traces", boot_dir / "normalized-strace.txt.gz")
    syscalls = set(trace["syscalls"])
    required_syscalls = {"clone", "futex", "mmap", "mprotect", "rt_sigaction", "rt_sigprocmask", "write", "exit_group"}
    if not required_syscalls.issubset(syscalls):
        raise ReferenceError(f"required runtime syscalls absent: {sorted(required_syscalls - syscalls)}")
    for line in (boot_dir / "normalized-strace.txt.gz",):
        if not line.is_file():
            raise ReferenceError("normalized trace was not written")
    file_access = file_access_summary(trace["paths"])
    if file_access["forbidden"]:
        raise ReferenceError(f"unclassified host file access: {file_access['forbidden']}")

    auxv = {name: parse_auxv(directory / "auxv") for name, directory in profile_dirs.items()}
    for name, values in auxv.items():
        if values.get("AT_PAGESZ") != 4096 or values.get("AT_HWCAP") != platform_result["at_hwcap"]:
            raise ReferenceError(f"{name} ERTS auxv differs from the full-system platform")
    argv_by_profile = {name: parse_nul_strings(directory / "cmdline") for name, directory in profile_dirs.items()}
    environment = {name: sorted(parse_nul_strings(directory / "environ")) for name, directory in profile_dirs.items()}
    memory = {name: memory_summary(directory) for name, directory in profile_dirs.items()}
    descriptors = {
        name: (directory / "fds.txt").read_text(encoding="utf-8").splitlines()
        for name, directory in profile_dirs.items()
    }

    network = network_summary(results / "traces")
    if network["external_connections"] or network["service_listeners"]:
        raise ReferenceError("ERTS unexpectedly depended on a network service")

    comparison = contract_comparison(root, syscalls)
    receipt = {
        "schema": "rust-beam/erts-linux-boot/v1",
        "status": "pass",
        "boot": boot,
        "duration_seconds": round(time.monotonic() - started, 3),
        "qemu_argv": argv,
        "qemu_sha256": sha256(prepared["qemu"]),
        "kernel_sha256": sha256(prepared["kernel"]),
        "initramfs_sha256": sha256(prepared["initramfs"]),
        "beam_sha256": sha256(root / BEAM_PATH),
        "full_system": True,
        "qemu_user": False,
        "network_devices": [],
        "dynamic_interpreter": None,
        "application_nifs": [],
        "platform": platform_result,
        "fault_probe": fault_result,
        "workloads": workloads,
        "thread_topology": topologies,
        "auxv": auxv,
        "argv": argv_by_profile,
        "environment": environment,
        "memory": memory,
        "descriptors": descriptors,
        "mappings": mappings,
        "file_access_classes": file_access,
        "trace": trace,
        "beam_host_comparison": comparison,
        "network": network,
        "serial_sha256": sha256(serial),
        "normalized_mappings_sha256": sha256(boot_dir / "normalized-mappings.txt"),
        "normalized_strace_sha256": sha256(boot_dir / "normalized-strace.txt.gz"),
        "shutdown": {"guest_poweroff": True, "qemu_exit_code": result.returncode},
    }
    (boot_dir / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    print(
        f"erts-linux: boot {boot}/{output.name} pass "
        f"threads={topologies['candidate']['count']} syscalls={len(trace['syscalls'])}"
    )
    return receipt


def run_boots(root: Path, boots: int, output: Path) -> Path:
    profile = load_profile(root)
    prepared = prepare_reference(root)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    receipts = [run_boot(root, prepared, profile, output, boot) for boot in range(1, boots + 1)]
    syscall_sets = [set(receipt["trace"]["syscalls"]) for receipt in receipts]
    aggregate = {
        "schema": "rust-beam/erts-linux-run/v1",
        "status": "pass",
        "boots_requested": boots,
        "boots_passed": len(receipts),
        "full_system": True,
        "qemu_user": False,
        "host": {"os": platform.system(), "architecture": platform.machine()},
        "machine": profile["qemu"]["machine"],
        "cpu": profile["qemu"]["cpu"],
        "vcpus": profile["qemu"]["vcpus"],
        "memory_mib": profile["qemu"]["memory_mib"],
        "kernel_release": profile["kernel_release"],
        "otp_release": profile["erts"]["otp_release"],
        "erts_version": profile["erts"]["version"],
        "beam_sha256": profile["erts"]["beam_sha256"],
        "all_candidate_thread_counts": [receipt["thread_topology"]["candidate"]["count"] for receipt in receipts],
        "all_syscall_sets_equal": all(values == syscall_sets[0] for values in syscall_sets),
        "observed_syscalls": sorted(set.union(*syscall_sets)),
        "all_external_network_connections": [receipt["network"]["external_connections"] for receipt in receipts],
        "all_network_service_listeners": [receipt["network"]["service_listeners"] for receipt in receipts],
        "all_ephemeral_udp_binds": [receipt["network"]["ephemeral_udp_binds"] for receipt in receipts],
        "all_shutdowns_clean": all(receipt["shutdown"]["qemu_exit_code"] == 0 for receipt in receipts),
        "beam_host_comparison": receipts[0]["beam_host_comparison"],
        "receipt_paths": [f"boot-{boot:02d}/receipt.json" for boot in range(1, boots + 1)],
    }
    aggregate_path = output / "aggregate.json"
    aggregate_path.write_text(canonical_json(aggregate), encoding="utf-8")
    print(f"erts-linux: {boots}/{boots} full-system TCG boots passed; receipt={aggregate_path.relative_to(root)}")
    return aggregate_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--boots", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "prepare":
            prepared = prepare_reference(root)
            print(prepared["initramfs"].relative_to(root))
        else:
            if not 1 <= args.boots <= 20:
                raise ReferenceError("--boots must be between 1 and 20")
            output = args.output or root / WORK_ROOT / "latest"
            if not output.is_absolute():
                output = root / output
            run_boots(root, args.boots, output)
    except (ReferenceError, OSError, subprocess.TimeoutExpired) as error:
        print(f"erts-linux: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
