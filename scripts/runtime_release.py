#!/usr/bin/env python3
"""Build, pair, inspect, and boot the pinned runtime_lab Mix release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

try:
    from scripts import erts_linux, otp_artifact
except ModuleNotFoundError:
    import erts_linux  # type: ignore[no-redef]
    import otp_artifact  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / "target/runtime-release"
MIX_PROJECT = ROOT / "beam/runtime_lab"
HOST_RUNTIME = ROOT / "target/toolchain-smoke"
TARGET_RELEASE = ROOT / "target/otp-aarch64/primary/release"
TARGET_BEAM = TARGET_RELEASE / "erts-17.0.5/bin/beam.smp"
TARGET_NATIVE_CLOSURE_PATH = ROOT / "target/otp-aarch64/primary/inspection/native-closure.json"
LAUNCHER_PATH = ROOT / "image/runtime-lab-launcher.json"
INIT_PATH = ROOT / "tests/runtime-release/init.sh"
OTP_PROFILE_PATH = ROOT / "toolchain/otp/aarch64-linux-musl.json"
OTP_ARTIFACT_ARGS: list[str] = []
RELEASE_ROOT = "/system/beam/runtime_lab"
TARGET_BEAM_SHA256 = "54ea7bc1953eb19908817ed243f63ddfabb7d8d9eefdb9d88f15ef4fe3577201"
ARTIFACT_BUILD_ID = (
    "otp-29.0.5-erts-17.0.5-beam-sha256-"
    "54ea7bc1953eb19908817ed243f63ddfabb7d8d9eefdb9d88f15ef4fe3577201"
)
PROBE_EVAL = "'Elixir.RuntimeLab.ReleaseProbe':run()."
RELEASE_BUILD_ENV: dict[str, str] = {}
ALLOWED_RUNTIME_HELPERS = {
    "erl_child_setup": "upstream-erts-helper",
    "inet_gethost": "upstream-erts-helper",
}
MIX_APPLICATIONS = {"elixir", "iex", "logger", "runtime_lab"}
TARGET_APPLICATIONS = {"compiler", "erl_interface", "erts", "kernel", "sasl", "stdlib"}
WRITE_FLAGS = {"O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND", "O_TMPFILE"}
OPENAT_RE = re.compile(r'^(?:\d+\.\d+\s+)?openat(?:2)?\([^,]+, "((?:[^"\\]|\\.)*)", ([^,)]+)')
OPEN_RE = re.compile(r'^(?:\d+\.\d+\s+)?open\("((?:[^"\\]|\\.)*)", ([^,)]+)')
EXEC_RE = re.compile(r'execve\("((?:[^"\\]|\\.)*)"')


class ReleaseError(RuntimeError):
    """Raised when release construction or execution violates the contract."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseError(f"cannot read {path}: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def run(
    argv: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: int = 7200,
    log: Path | None = None,
) -> str:
    rendered = shlex.join(argv)
    print(f"+ ({cwd}) {rendered}", flush=True)
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(f"+ ({cwd}) {rendered}\n")
            stream.write(result.stdout)
    if result.returncode:
        raise ReleaseError(f"command failed ({result.returncode}): {rendered}\n{result.stdout[-8000:]}")
    return result.stdout


def source_epoch() -> int:
    value = load_json(OTP_PROFILE_PATH).get("source_date_epoch")
    if not isinstance(value, int):
        raise ReleaseError("OTP profile has no integer source_date_epoch")
    return value


def release_inputs() -> list[dict[str, Any]]:
    paths = [MIX_PROJECT / "mix.exs", MIX_PROJECT / "config/config.exs"]
    paths.extend(sorted((MIX_PROJECT / "lib").rglob("*.ex")))
    paths.extend(sorted((MIX_PROJECT / "rel").rglob("*")))
    result = []
    for path in paths:
        if path.is_file():
            result.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return result


def validate_launcher(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != "rust-beam/runtime-lab-launcher/v1":
        raise ReleaseError("unsupported runtime_lab launcher manifest")
    process = value.get("process", {})
    runtime = value.get("runtime", {})
    release = value.get("release", {})
    arguments = value.get("arguments")
    environment = value.get("environment")
    if (
        process.get("root_directory") != RELEASE_ROOT
        or process.get("executable") != f"{RELEASE_ROOT}/erts-17.0.5/bin/beam.smp"
        or process.get("read_only_release") is not True
        or runtime.get("otp") != "29.0.5"
        or runtime.get("erts") != "17.0.5"
        or runtime.get("elixir") != "1.20.4"
        or runtime.get("beam_sha256") != TARGET_BEAM_SHA256
        or runtime.get("artifact_build_id") != ARTIFACT_BUILD_ID
        or release.get("version") != "0.1.0"
        or release.get("runtime_config_path") is not False
        or release.get("config_providers") != []
        or value.get("vm_flags") != ["-S 2:2", "-SDcpu 1:1", "-SDio 1", "-A 1"]
        or not isinstance(arguments, list)
        or not isinstance(environment, dict)
    ):
        raise ReleaseError("launcher runtime or release contract changed")
    if arguments[0] != process["executable"] or environment.get("RB_ERTS_ARTIFACT_BUILD_ID") != ARTIFACT_BUILD_ID:
        raise ReleaseError("launcher executable or artifact identity changed")
    if environment.get("RELEASE_DISTRIBUTION") != "none" or environment.get("LC_ALL") != "C.UTF-8":
        raise ReleaseError("target release distribution or locale changed")
    rendered = " ".join(arguments)
    for forbidden in ("bin/runtime_lab", "erlexec", "/bin/sh", "-remsh"):
        if forbidden in rendered:
            raise ReleaseError(f"launcher uses forbidden path: {forbidden}")
    for required in (
        f"{RELEASE_ROOT}/releases/0.1.0/start",
        f"{RELEASE_ROOT}/releases/0.1.0/sys",
        f"{RELEASE_ROOT}/releases/0.1.0/vm.args",
        PROBE_EVAL,
    ):
        if required not in arguments:
            raise ReleaseError(f"launcher is missing {required}")
    if arguments[1:9] != ["-S", "2:2", "-SDcpu", "1:1", "-SDio", "1", "-A", "1"]:
        raise ReleaseError("launcher does not apply the frozen profile directly to beam.smp")
    return value


def launcher() -> dict[str, Any]:
    return validate_launcher(load_json(LAUNCHER_PATH))


def copy_project(destination: Path) -> None:
    shutil.copytree(
        MIX_PROJECT,
        destination,
        ignore=shutil.ignore_patterns("_build", "deps", ".elixir_ls"),
    )


def host_paths() -> tuple[Path, Path, Path]:
    otp = HOST_RUNTIME / "install/otp"
    elixir = HOST_RUNTIME / "build/elixir"
    return otp, elixir / "bin/mix", elixir / "bin/elixir"


def host_environment(home: Path) -> dict[str, str]:
    otp, mix, _elixir = host_paths()
    env = os.environ.copy()
    for name in list(env):
        if name.startswith(("ERL_", "MIX_", "HEX_")):
            env.pop(name, None)
    home.mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "PATH": f"{mix.parent}:{otp / 'bin'}:{env['PATH']}",
            "ERL_ROOTDIR": str(otp / "lib/erlang"),
            "HOME": str(home),
            "MIX_HOME": str(home / ".mix"),
            "HEX_HOME": str(home / ".hex"),
            "HEX_OFFLINE": "1",
            "MIX_ENV": "prod",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": str(source_epoch()),
            "ERL_COMPILER_OPTIONS": "deterministic",
        }
    )
    env.update(RELEASE_BUILD_ENV)
    return env


def ensure_host_runtime() -> dict[str, Any]:
    otp, mix, elixir = host_paths()
    otp_version = otp / "lib/erlang/releases/29/OTP_VERSION"
    if not otp_version.is_file() or not mix.is_file() or not elixir.is_file():
        run(
            [
                "./scripts/toolchain-smoke.sh",
                str((ROOT / "target/toolchain-cache").resolve()),
                str(HOST_RUNTIME.resolve()),
            ],
            cwd=ROOT,
        )
    if otp_version.read_text(encoding="utf-8").strip() != "29.0.5":
        raise ReleaseError("host OTP is not the pinned 29.0.5 build")
    env = host_environment(WORK_ROOT / "host-identity-home")
    elixir_version = run([str(elixir), "--short-version"], env=env, timeout=30).strip()
    erts_version = run(
        [
            str(otp / "bin/erl"),
            "-noshell",
            "-eval",
            'io:format("~s", [erlang:system_info(version)]), halt().',
        ],
        env=env,
        timeout=30,
    ).strip()
    if elixir_version != "1.20.4" or erts_version != "17.0.5":
        raise ReleaseError(f"host runtime pair changed: Elixir {elixir_version}, ERTS {erts_version}")
    return {
        "otp": "29.0.5",
        "erts": erts_version,
        "elixir": elixir_version,
        "otp_root": str(otp.relative_to(ROOT)),
        "elixir_root": str((HOST_RUNTIME / "build/elixir").relative_to(ROOT)),
    }


def tree_manifest(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            entries.append(
                {
                    "path": relative,
                    "kind": "symlink",
                    "mode": stat.S_IMODE(metadata.st_mode),
                    "target": os.readlink(path),
                }
            )
        elif stat.S_ISDIR(metadata.st_mode):
            entries.append(
                {
                    "path": relative,
                    "kind": "directory",
                    "mode": stat.S_IMODE(metadata.st_mode),
                }
            )
        elif stat.S_ISREG(metadata.st_mode):
            entries.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": stat.S_IMODE(metadata.st_mode),
                    "size": metadata.st_size,
                    "sha256": sha256(path),
                }
            )
    return entries


def scripts_inventory(root: Path) -> list[dict[str, Any]]:
    scripts: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        with path.open("rb") as stream:
            first = stream.readline(512)
        if first.startswith(b"#!"):
            scripts.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "interpreter": first.decode("utf-8", errors="replace").strip(),
                    "invoked_by_launcher": False,
                }
            )
    return scripts


def app_name(path: Path) -> str:
    name = path.name.removesuffix(".ez")
    match = re.match(r"^(.+)-[0-9].*$", name)
    if not match:
        raise ReleaseError(f"cannot derive application name from {path.name}")
    return match.group(1)


def release_applications(root: Path) -> set[str]:
    return {app_name(path) for path in (root / "lib").iterdir()}


def inspect_zip_native(path: Path, relative: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not zipfile.is_zipfile(path):
        return entries
    with zipfile.ZipFile(path) as archive:
        for member in sorted(archive.infolist(), key=lambda item: item.filename):
            if member.is_dir():
                continue
            data = archive.read(member)
            if member.filename.endswith((".so", ".dll", ".dylib")) or data.startswith((b"\x7fELF", b"!<arch>\n")):
                entries.append(
                    {
                        "path": f"{relative}!/{member.filename}",
                        "kind": "embedded-native",
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
    return entries


def native_inventory(root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    contract = otp_artifact.load_profile()["artifact_contract"]
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        relative = path.relative_to(root).as_posix()
        if path.suffix in {".so", ".dll", ".dylib"} or ".so." in path.name:
            raise ReleaseError(f"dynamic library is forbidden in paired release: {relative}")
        with path.open("rb") as stream:
            magic = stream.read(8)
        if magic.startswith(b"\x7fELF"):
            elf = otp_artifact.parse_elf(path)
            otp_artifact.validate_runtime_elf(path, elf, contract)
            entries.append(
                {
                    "path": relative,
                    "kind": "elf",
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                    "machine": elf["machine"],
                    "type": elf["type"],
                }
            )
        elif magic == b"!<arch>\n":
            entries.append(
                {
                    "path": relative,
                    "kind": "archive",
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        elif path.suffix == ".ez":
            embedded = inspect_zip_native(path, relative)
            if embedded:
                raise ReleaseError(f"native object is hidden inside release archive: {embedded[0]['path']}")
    return entries


def validate_mix_release(release: Path) -> dict[str, Any]:
    applications = release_applications(release)
    if applications != MIX_APPLICATIONS:
        raise ReleaseError(f"Mix payload applications differ: {sorted(applications)}")
    embedded_erts = sorted(path.name for path in release.glob("erts-*"))
    if embedded_erts:
        raise ReleaseError(f"Mix payload embedded host ERTS: {embedded_erts}")
    native = native_inventory(release)
    if native:
        raise ReleaseError(f"Mix payload contains a native object: {native[0]['path']}")
    version = release / "releases/0.1.0"
    required = ("runtime_lab.rel", "start.boot", "start.script", "sys.config", "vm.args")
    missing = [name for name in required if not (version / name).is_file()]
    if missing:
        raise ReleaseError(f"Mix release is incomplete: {missing}")
    rel_text = (version / "runtime_lab.rel").read_text(encoding="utf-8")
    for application in ("runtime_lab", "elixir", "logger"):
        if application not in rel_text:
            raise ReleaseError(f"Mix release specification omits {application}")
    sys_config = (version / "sys.config").read_text(encoding="utf-8")
    for forbidden in ("RUNTIME_CONFIG=true", "Elixir.Config.Provider", "Elixir.Config.Reader"):
        if forbidden in sys_config:
            raise ReleaseError(f"writable runtime configuration is present: {forbidden}")
    expected_vm_args = (MIX_PROJECT / "rel/vm.args.eex").read_text(encoding="utf-8")
    if (version / "vm.args").read_text(encoding="utf-8") != expected_vm_args:
        raise ReleaseError("generated release vm.args differs from its immutable input")
    return {
        "applications": sorted(applications),
        "embedded_erts": embedded_erts,
        "native_objects": native,
        "scripts": scripts_inventory(release),
        "tree": tree_manifest(release),
    }


def build_mix_lane(name: str) -> Path:
    runtime = ensure_host_runtime()
    lane = WORK_ROOT / f"mix-{name}"
    work = WORK_ROOT / f"mix-work-{name}"
    shutil.rmtree(lane, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)
    source = work / "source"
    copy_project(source)
    env = host_environment(work / "home")
    _otp, mix, _elixir = host_paths()
    log = work / "build.log"
    commands = [
        [str(mix), "clean"],
        [str(mix), "compile", "--warnings-as-errors"],
        [str(mix), "release", "runtime_lab", "--overwrite"],
    ]
    for command in commands:
        run(command, cwd=source, env=env, log=log)
    generated = source / "_build/prod/rel/runtime_lab"
    if not generated.is_dir():
        raise ReleaseError("mix release did not produce runtime_lab")
    release = lane / "release"
    lane.mkdir(parents=True)
    shutil.copytree(generated, release, symlinks=True)
    shutil.copy2(log, lane / "build.log")
    inspection = validate_mix_release(release)
    receipt = {
        "schema": "rust-beam/runtime-lab-mix-build/v1",
        "lane": name,
        "result": "pass",
        "runtime_pair": runtime,
        "mix_env": "prod",
        "network_required": False,
        "release_options": {
            "include_erts": False,
            "include_executables_for": ["unix"],
            "runtime_config_path": False,
        },
        "commands": [shlex.join(command) for command in commands],
        "inputs": release_inputs(),
        "applications": inspection["applications"],
        "embedded_erts": inspection["embedded_erts"],
        "native_objects": inspection["native_objects"],
        "scripts": inspection["scripts"],
        "tree_digest": value_sha256(inspection["tree"]),
        "tree_entry_count": len(inspection["tree"]),
        "build_log_sha256": sha256(lane / "build.log"),
    }
    (lane / "build-receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    print(
        f"runtime-release: built genuine Mix lane {name}; "
        f"files={len(inspection['tree'])} digest={receipt['tree_digest']}"
    )
    return lane


def mix_lane_current(name: str) -> bool:
    lane = WORK_ROOT / f"mix-{name}"
    receipt_path = lane / "build-receipt.json"
    release = lane / "release"
    if not receipt_path.is_file() or not release.is_dir():
        return False
    try:
        receipt = load_json(receipt_path)
        inspection = validate_mix_release(release)
    except ReleaseError:
        return False
    return (
        receipt.get("schema") == "rust-beam/runtime-lab-mix-build/v1"
        and receipt.get("inputs") == release_inputs()
        and receipt.get("tree_digest") == value_sha256(inspection["tree"])
    )


def ensure_target_release() -> None:
    if not TARGET_BEAM.is_file() or sha256(TARGET_BEAM) != TARGET_BEAM_SHA256:
        run([sys.executable, "scripts/otp_artifact.py", *OTP_ARTIFACT_ARGS, "build"])
    run([sys.executable, "scripts/otp_artifact.py", *OTP_ARTIFACT_ARGS, "inspect"])
    if sha256(TARGET_BEAM) != TARGET_BEAM_SHA256:
        raise ReleaseError("target beam.smp differs from the sealed artifact")


def copy_entry(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)


def pair_lane(mix_name: str, pair_name: str) -> tuple[Path, dict[str, Any]]:
    ensure_target_release()
    mix_release = WORK_ROOT / f"mix-{mix_name}/release"
    mix_inspection = validate_mix_release(mix_release)
    pair = WORK_ROOT / pair_name
    shutil.rmtree(pair, ignore_errors=True)
    shutil.copytree(TARGET_RELEASE, pair, symlinks=True)

    for directory in ("bin", "releases"):
        for source in sorted((mix_release / directory).iterdir()):
            copy_entry(source, pair / directory / source.name)
    for source in sorted((mix_release / "lib").iterdir()):
        application = app_name(source)
        if application in TARGET_APPLICATIONS:
            raise ReleaseError(f"Mix payload attempted to replace target OTP application {application}")
        copy_entry(source, pair / "lib" / source.name)

    pair_native = native_inventory(pair)
    target_native = load_json(TARGET_NATIVE_CLOSURE_PATH)
    expected_native = [
        {
            "path": entry["path"],
            "kind": entry["kind"],
            "size": entry["size"],
            "sha256": entry["digest"].removeprefix("sha256:"),
        }
        for entry in target_native
    ]
    actual_native = [
        {key: entry[key] for key in ("path", "kind", "size", "sha256")}
        for entry in pair_native
    ]
    if actual_native != expected_native:
        raise ReleaseError("paired native closure is not byte-identical to the sealed target")
    if sha256(pair / "erts-17.0.5/bin/beam.smp") != TARGET_BEAM_SHA256:
        raise ReleaseError("paired release substituted beam.smp")
    if not (pair / "releases/29/OTP_VERSION").is_file():
        raise ReleaseError("paired release lacks target OTP_VERSION")
    for application in MIX_APPLICATIONS:
        if application not in release_applications(pair):
            raise ReleaseError(f"paired release lost Mix application {application}")

    tree = tree_manifest(pair)
    receipt = {
        "schema": "rust-beam/runtime-lab-pair/v1",
        "result": "pass",
        "mix_lane": mix_name,
        "pair_lane": pair_name,
        "genuine_mix_release": True,
        "mix_tree_digest": value_sha256(mix_inspection["tree"]),
        "target_beam_sha256": TARGET_BEAM_SHA256,
        "paired_beam_sha256": sha256(pair / "erts-17.0.5/bin/beam.smp"),
        "native_closure_exact_match": True,
        "native_closure_count": len(pair_native),
        "native_inventory": pair_native,
        "applications": sorted(release_applications(pair)),
        "scripts": scripts_inventory(pair),
        "launcher_sha256": sha256(LAUNCHER_PATH),
        "pair_tree_digest": value_sha256(tree),
        "pair_tree_entry_count": len(tree),
    }
    return pair, receipt


def build_squashfs(source: Path, destination: Path) -> None:
    destination.unlink(missing_ok=True)
    run(
        [
            "mksquashfs",
            str(source),
            str(destination),
            "-noappend",
            "-comp",
            "xz",
            "-all-root",
            "-no-xattrs",
            "-mkfs-time",
            str(source_epoch()),
            "-all-time",
            str(source_epoch()),
            "-processors",
            "1",
            "-no-progress",
            "-quiet",
        ],
        timeout=1800,
    )


def pair_all() -> Path:
    launcher()
    if not mix_lane_current("primary"):
        build_mix_lane("primary")
    primary, primary_receipt = pair_lane("primary", "paired")
    build_mix_lane("rebuild")
    rebuild, rebuild_receipt = pair_lane("rebuild", "paired-rebuild")
    if primary_receipt["mix_tree_digest"] != rebuild_receipt["mix_tree_digest"]:
        raise ReleaseError("clean Mix rebuild differs")
    if primary_receipt["pair_tree_digest"] != rebuild_receipt["pair_tree_digest"]:
        raise ReleaseError("clean paired release rebuild differs")

    primary_image = WORK_ROOT / "paired.squashfs"
    rebuild_image = WORK_ROOT / "paired-rebuild.squashfs"
    build_squashfs(primary, primary_image)
    build_squashfs(rebuild, rebuild_image)
    if sha256(primary_image) != sha256(rebuild_image):
        raise ReleaseError("reproducible SquashFS images differ")
    mix_inventory_path = WORK_ROOT / "mix-tree-manifest.json"
    pair_inventory_path = WORK_ROOT / "paired-tree-manifest.json"
    mix_inventory_path.write_text(
        canonical_json(tree_manifest(WORK_ROOT / "mix-primary/release")), encoding="utf-8"
    )
    pair_inventory_path.write_text(canonical_json(tree_manifest(primary)), encoding="utf-8")
    receipt = {
        "schema": "rust-beam/runtime-lab-pair-comparison/v1",
        "result": "equivalent",
        "mix_release_exact_match": True,
        "paired_tree_exact_match": True,
        "squashfs_exact_match": True,
        "mix_tree_digest": primary_receipt["mix_tree_digest"],
        "pair_tree_digest": primary_receipt["pair_tree_digest"],
        "squashfs_sha256": sha256(primary_image),
        "squashfs_size": primary_image.stat().st_size,
        "target_beam_sha256": TARGET_BEAM_SHA256,
        "native_closure_count": primary_receipt["native_closure_count"],
        "applications": primary_receipt["applications"],
        "scripts": primary_receipt["scripts"],
        "launcher": {
            "path": LAUNCHER_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(LAUNCHER_PATH),
        },
        "inventories": {
            "mix_tree": {
                "path": mix_inventory_path.relative_to(ROOT).as_posix(),
                "sha256": sha256(mix_inventory_path),
            },
            "paired_tree": {
                "path": pair_inventory_path.relative_to(ROOT).as_posix(),
                "sha256": sha256(pair_inventory_path),
            },
        },
        "primary": primary_receipt,
        "rebuild": rebuild_receipt,
    }
    receipt_path = WORK_ROOT / "pair-receipt.json"
    receipt_path.write_text(canonical_json(receipt), encoding="utf-8")
    print(
        "runtime-release: paired exact target ERTS; "
        f"native={receipt['native_closure_count']} squashfs={receipt['squashfs_sha256']}"
    )
    return receipt_path


def pair_current() -> bool:
    receipt_path = WORK_ROOT / "pair-receipt.json"
    image = WORK_ROOT / "paired.squashfs"
    pair = WORK_ROOT / "paired"
    if not receipt_path.is_file() or not image.is_file() or not pair.is_dir():
        return False
    try:
        receipt = load_json(receipt_path)
        pair_native = native_inventory(pair)
    except ReleaseError:
        return False
    return (
        receipt.get("schema") == "rust-beam/runtime-lab-pair-comparison/v1"
        and receipt.get("result") == "equivalent"
        and receipt.get("target_beam_sha256") == TARGET_BEAM_SHA256
        and receipt.get("launcher", {}).get("sha256") == sha256(LAUNCHER_PATH)
        and receipt.get("squashfs_sha256") == sha256(image)
        and receipt.get("pair_tree_digest") == value_sha256(tree_manifest(pair))
        and receipt.get("native_closure_count") == len(pair_native)
        and mix_lane_current("primary")
    )


def prepare_guest() -> dict[str, Path]:
    if not pair_current():
        pair_all()
    base = erts_linux.prepare_reference(ROOT)
    identity = {
        "base_initramfs_sha256": sha256(base["initramfs"]),
        "init_source_sha256": sha256(INIT_PATH),
        "launcher_sha256": sha256(LAUNCHER_PATH),
        "release_squashfs_sha256": sha256(WORK_ROOT / "paired.squashfs"),
    }
    initramfs = WORK_ROOT / "runtime-release-initramfs.gz"
    provenance = WORK_ROOT / "guest-preparation.json"
    if provenance.is_file() and initramfs.is_file():
        previous = load_json(provenance)
        if previous.get("identity") == identity and previous.get("initramfs_sha256") == sha256(initramfs):
            return {**base, "initramfs": initramfs, "release": WORK_ROOT / "paired.squashfs"}

    build_root = WORK_ROOT / "guest-root"
    shutil.rmtree(build_root, ignore_errors=True)
    build_root.mkdir(parents=True)
    erts_linux.extract_concatenated_newc(base["initramfs"], build_root)
    for relative in ("otp", "probe"):
        path = build_root / relative
        if path.is_dir():
            shutil.rmtree(path)
    shutil.copy2(INIT_PATH, build_root / "init")
    (build_root / "init").chmod(0o755)
    erts_linux.set_tree_mtime(build_root, source_epoch())
    erts_linux.pack_initramfs(ROOT, build_root, initramfs)
    receipt = {
        "schema": "rust-beam/runtime-lab-guest-preparation/v1",
        "identity": identity,
        "initramfs_sha256": sha256(initramfs),
        "initramfs_size": initramfs.stat().st_size,
    }
    provenance.write_text(canonical_json(receipt), encoding="utf-8")
    return {**base, "initramfs": initramfs, "release": WORK_ROOT / "paired.squashfs"}


def qemu_argv(
    qemu: Path,
    kernel: Path,
    initramfs: Path,
    release: Path,
    results: Path,
    serial: Path,
) -> list[str]:
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
        f"file={release},format=raw,if=none,readonly=on,id=release",
        "-device",
        "virtio-blk-device,drive=release,serial=RBMIXRELEASE",
        "-drive",
        f"file={results},format=raw,if=none,id=results,cache=unsafe",
        "-device",
        "virtio-blk-device,drive=results,serial=RBRELEASERESULTS",
    ]


def parse_open_attempt(line: str) -> dict[str, Any] | None:
    match = OPENAT_RE.match(line) or OPEN_RE.match(line)
    if not match:
        return None
    path = bytes(match.group(1), "utf-8").decode("unicode_escape").replace("\0", "")
    flags = match.group(2).strip()
    result = line.rsplit(" = ", 1)[-1].strip() if " = " in line else "unknown"
    return {
        "path": path,
        "flags": flags,
        "write_capable": any(flag in flags.split("|") for flag in WRITE_FLAGS),
        "result": result,
        "normalized": erts_linux.normalize_trace_line(line),
    }


def audit_open_attempts(trace_dir: Path) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for trace_file in sorted(path for path in trace_dir.iterdir() if path.is_file()):
        for line in trace_file.read_text(encoding="utf-8", errors="replace").splitlines():
            attempt = parse_open_attempt(line)
            if attempt is None:
                continue
            path = attempt["path"]
            if path == f"{RELEASE_ROOT}/.rb-write-probe":
                attempt["classification"] = "declared-read-only-negative"
            elif path.startswith(f"{RELEASE_ROOT}/") or path == RELEASE_ROOT:
                attempt["classification"] = "immutable-release-read"
            elif path == "/dev/null" and attempt["write_capable"]:
                attempt["classification"] = "declared-crash-dump-sink"
            elif attempt["write_capable"]:
                attempt["classification"] = "undeclared-write"
            else:
                attempt["classification"] = "external-read"
            attempts.append(attempt)
    negative = [attempt for attempt in attempts if attempt["classification"] == "declared-read-only-negative"]
    undeclared = [attempt for attempt in attempts if attempt["classification"] == "undeclared-write"]
    release_writes = [
        attempt
        for attempt in attempts
        if attempt["write_capable"] and attempt["path"].startswith(RELEASE_ROOT)
    ]
    if len(negative) != 1 or "EROFS" not in negative[0]["result"]:
        raise ReleaseError(f"read-only release negative write differs: {negative}")
    if undeclared:
        raise ReleaseError(f"undeclared write-capable open observed: {undeclared[0]}")
    if release_writes != negative:
        raise ReleaseError("an unexpected release-tree write was attempted")
    return {
        "status": "pass",
        "attempt_count": len(attempts),
        "release_read_count": sum(
            attempt["classification"] == "immutable-release-read" for attempt in attempts
        ),
        "declared_negative_count": len(negative),
        "undeclared_write_attempts": undeclared,
        "attempts": attempts,
    }


def exec_inventory(trace_dir: Path) -> list[dict[str, str]]:
    paths: list[str] = []
    for trace_file in sorted(path for path in trace_dir.iterdir() if path.is_file()):
        for line in trace_file.read_text(encoding="utf-8", errors="replace").splitlines():
            match = EXEC_RE.search(line)
            if match:
                paths.append(bytes(match.group(1), "utf-8").decode("unicode_escape"))
    expected_beam = f"{RELEASE_ROOT}/erts-17.0.5/bin/beam.smp"
    if expected_beam not in paths:
        raise ReleaseError("trace did not execute the manifest beam.smp")
    forbidden = [path for path in paths if path.endswith(("/erlexec", "/erl", "/runtime_lab", "/sh"))]
    if forbidden:
        raise ReleaseError(f"release launch used a forbidden executable: {forbidden}")
    allowed_helpers = {expected_beam: "manifest-entrypoint"}
    allowed_helpers.update(
        {
            f"{RELEASE_ROOT}/erts-17.0.5/bin/{name}": classification
            for name, classification in ALLOWED_RUNTIME_HELPERS.items()
        }
    )
    unknown = sorted(set(paths) - set(allowed_helpers))
    if unknown:
        raise ReleaseError(f"unexpected executable in release trace: {unknown}")
    return [{"path": path, "classification": allowed_helpers[path]} for path in paths]


def validate_serial(serial: Path) -> None:
    text = serial.read_text(encoding="utf-8", errors="replace")
    required = (
        "RB_RELEASE_GUEST event=boot",
        "type=application_started",
        "type=runtime_identity",
        'build_id="runtime_lab-0.1.0"',
        'elixir="1.20.4"',
        'otp="29.0.5"',
        'erts="17.0.5"',
        "type=target_release_result",
        "application_ensure_all_started=true",
        f'artifact_build_id="{ARTIFACT_BUILD_ID}"',
        "config_loaded=true",
        "read_only_error=erofs",
        "status=pass",
        "supervision=true",
        "workloads=true",
        "type=application_stopped",
        "RB_RELEASE_GUEST event=beam-exit status=0",
        "RB_RELEASE_GUEST event=complete status=pass",
    )
    missing = [marker for marker in required if marker not in text]
    if missing or "RB_RELEASE_GUEST event=fail" in text:
        raise ReleaseError(f"target release serial milestones differ: missing={missing}")
    if text.count("type=target_release_result") != 1 or text.count("type=application_stopped") != 1:
        raise ReleaseError("target release emitted duplicate or missing terminal milestones")


def run_boot(prepared: dict[str, Path], output: Path, boot: int) -> dict[str, Any]:
    boot_dir = output / f"boot-{boot:02d}"
    boot_dir.mkdir(parents=True)
    image = boot_dir / "results.img"
    serial = boot_dir / "serial.log"
    qemu_log = boot_dir / "qemu.log"
    with image.open("wb") as stream:
        stream.truncate(256 * 1024 * 1024)
    mkfs = erts_linux.require_tool("mkfs.ext4")
    debugfs = erts_linux.require_tool("debugfs")
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
            "52554245-414d-4552-5453-000000000007",
            "-L",
            "RBRELEASE",
            str(image),
        ],
        timeout=60,
    )
    argv = qemu_argv(
        prepared["qemu"],
        prepared["kernel"],
        prepared["initramfs"],
        prepared["release"],
        image,
        serial,
    )
    started = time.monotonic()
    with qemu_log.open("w", encoding="utf-8") as log:
        try:
            result = subprocess.run(
                argv,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=300,
            )
        except subprocess.TimeoutExpired as error:
            raise ReleaseError(f"full-system target release boot {boot} timed out") from error
    if result.returncode != 0:
        raise ReleaseError(f"QEMU target release boot {boot} exited {result.returncode}")
    erts_linux.normalize_serial(serial)
    validate_serial(serial)
    run([debugfs, "-R", f"rdump /results {boot_dir}", str(image)], timeout=120)
    image.unlink()
    results = boot_dir / "results"
    if erts_linux.parse_key_values(results / "guest-status.txt") != {
        "status": "pass",
        "release": "0",
        "mount": "squashfs-ro",
    }:
        raise ReleaseError("guest release status differs")
    mount = (results / "release-mount.txt").read_text(encoding="utf-8").strip()
    if f" {RELEASE_ROOT} squashfs ro," not in mount:
        raise ReleaseError("release tree was not mounted read-only from SquashFS")
    trace_dir = results / "traces"
    trace = erts_linux.trace_summary(trace_dir, boot_dir / "normalized-strace.txt.gz")
    opens = audit_open_attempts(trace_dir)
    executable_inventory = exec_inventory(trace_dir)
    network = erts_linux.network_summary(trace_dir)
    if network["external_connections"] or network["service_listeners"]:
        raise ReleaseError("target release used an external network or listener")
    pair = load_json(WORK_ROOT / "pair-receipt.json")
    receipt = {
        "schema": "rust-beam/runtime-lab-linux-boot/v1",
        "status": "pass",
        "boot": boot,
        "duration_seconds": round(time.monotonic() - started, 3),
        "full_system": True,
        "qemu_user": False,
        "host": {"os": platform.system(), "architecture": platform.machine()},
        "qemu_argv": argv,
        "qemu_sha256": sha256(prepared["qemu"]),
        "kernel_sha256": sha256(prepared["kernel"]),
        "initramfs_sha256": sha256(prepared["initramfs"]),
        "release_squashfs_sha256": sha256(prepared["release"]),
        "launcher_sha256": sha256(LAUNCHER_PATH),
        "genuine_mix_release": True,
        "mix_tree_digest": pair["mix_tree_digest"],
        "pair_tree_digest": pair["pair_tree_digest"],
        "target_beam_sha256": TARGET_BEAM_SHA256,
        "artifact_build_id": ARTIFACT_BUILD_ID,
        "read_only_mount": mount,
        "open_attempts": opens,
        "executable_inventory": executable_inventory,
        "trace": trace,
        "network": network,
        "serial_sha256": sha256(serial),
        "normalized_strace_sha256": sha256(boot_dir / "normalized-strace.txt.gz"),
        "shutdown": {"application_stop_event": True, "guest_poweroff": True, "qemu_exit_code": 0},
    }
    (boot_dir / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    print(
        f"runtime-release: boot {boot}/{output.name} pass "
        f"opens={opens['attempt_count']} syscalls={len(trace['syscalls'])}"
    )
    return receipt


def run_boots(boots: int, output: Path) -> Path:
    prepared = prepare_guest()
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    receipts = [run_boot(prepared, output, boot) for boot in range(1, boots + 1)]
    pair = load_json(WORK_ROOT / "pair-receipt.json")
    aggregate = {
        "schema": "rust-beam/runtime-lab-linux-run/v1",
        "status": "pass",
        "boots_requested": boots,
        "boots_passed": len(receipts),
        "full_system": True,
        "qemu_user": False,
        "machine": "virt-11.1",
        "cpu": "cortex-a53",
        "accelerator": "tcg,thread=multi",
        "vcpus": 4,
        "memory_mib": 1024,
        "kernel_release": "6.12.94-0-virt",
        "otp": "29.0.5",
        "erts": "17.0.5",
        "elixir": "1.20.4",
        "artifact_build_id": ARTIFACT_BUILD_ID,
        "target_beam_sha256": TARGET_BEAM_SHA256,
        "genuine_mix_release": True,
        "mix_release_exact_match": pair["mix_release_exact_match"],
        "paired_tree_exact_match": pair["paired_tree_exact_match"],
        "squashfs_exact_match": pair["squashfs_exact_match"],
        "mix_tree_digest": pair["mix_tree_digest"],
        "pair_tree_digest": pair["pair_tree_digest"],
        "squashfs_sha256": pair["squashfs_sha256"],
        "native_closure_count": pair["native_closure_count"],
        "all_read_only_mounts": all(" squashfs ro," in receipt["read_only_mount"] for receipt in receipts),
        "all_undeclared_write_attempts": [
            len(receipt["open_attempts"]["undeclared_write_attempts"]) for receipt in receipts
        ],
        "all_application_shutdowns_clean": all(
            receipt["shutdown"]["application_stop_event"] and receipt["shutdown"]["qemu_exit_code"] == 0
            for receipt in receipts
        ),
        "all_external_network_connections": [receipt["network"]["external_connections"] for receipt in receipts],
        "all_network_service_listeners": [receipt["network"]["service_listeners"] for receipt in receipts],
        "receipt_paths": [f"boot-{boot:02d}/receipt.json" for boot in range(1, boots + 1)],
    }
    aggregate_path = output / "aggregate.json"
    aggregate_path.write_text(canonical_json(aggregate), encoding="utf-8")
    print(f"runtime-release: {boots}/{boots} full-system target release boots passed")
    return aggregate_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="build a fresh genuine Mix release")
    subparsers.add_parser("pair", help="pair and compare two clean release assemblies")
    run_parser = subparsers.add_parser("run", help="boot the paired release on full-system AArch64 Linux")
    run_parser.add_argument("--boots", type=int, default=1)
    run_parser.add_argument("--output", type=Path, default=WORK_ROOT / "latest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "build":
            build_mix_lane("primary")
        elif args.command == "pair":
            pair_all()
        elif args.command == "run":
            if not 1 <= args.boots <= 20:
                raise ReleaseError("--boots must be between 1 and 20")
            output = args.output if args.output.is_absolute() else ROOT / args.output
            run_boots(args.boots, output)
        else:
            raise AssertionError(args.command)
    except (ReleaseError, otp_artifact.ArtifactError, erts_linux.ReferenceError, OSError, subprocess.TimeoutExpired) as error:
        print(f"runtime-release: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
