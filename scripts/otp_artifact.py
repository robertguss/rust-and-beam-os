#!/usr/bin/env python3
"""Build and inspect the pinned static AArch64-musl Erlang/OTP artifact."""

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
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "toolchain/otp/aarch64-linux-musl.json"
SOURCE_LOCK_PATH = ROOT / "toolchain/sources.lock.json"
WORK_ROOT = ROOT / "target/otp-aarch64"
CACHE_ROOT = ROOT / "target/toolchain-cache"
BUILD_ROOT = WORK_ROOT / "work"

PROFILE_FIELDS = {
    "schema",
    "target",
    "otp_release",
    "erts_release",
    "source_date_epoch",
    "sources",
    "compiler",
    "configure_flags",
    "cross_answers",
    "applications",
    "native_policy",
    "artifact_contract",
    "patches",
}
SOURCE_IDS = {
    "otp-source",
    "musl-source",
    "llvm-source",
    "llvm-x86_64",
    "llvm-aarch64",
}
ELF_TYPES = {1: "ET_REL", 2: "ET_EXEC", 3: "ET_DYN", 4: "ET_CORE"}
PROGRAM_TYPES = {
    1: "PT_LOAD",
    2: "PT_DYNAMIC",
    3: "PT_INTERP",
    7: "PT_TLS",
    0x6474E550: "PT_GNU_EH_FRAME",
    0x6474E551: "PT_GNU_STACK",
    0x6474E552: "PT_GNU_RELRO",
}
LSE_MNEMONICS = re.compile(
    r"^(?:cas|casa|casal|casl|casp|caspa|caspal|caspl|swp|swpa|swpal|swpl|"
    r"ldadd|ldadda|ldaddal|ldaddl|ldclr|ldclra|ldclral|ldclrl|"
    r"ldeor|ldeora|ldeoral|ldeorl|ldset|ldseta|ldsetal|ldsetl|"
    r"ldsmax|ldsmaxa|ldsmaxal|ldsmaxl|ldsmin|ldsmina|ldsminal|ldsminl|"
    r"ldumax|ldumaxa|ldumaxal|ldumaxl|ldumin|ldumina|lduminal|lduminl)(?:b|h)?$"
)
BRANCH_PROTECTION_MNEMONICS = re.compile(
    r"^(?:bti|pac(?:ia|ib|da|db|iza|izb|dza|dzb|ga|iasp|ibsp)|"
    r"aut(?:ia|ib|da|db|iza|izb|dza|dzb|iasp|ibsp)|"
    r"(?:br|blr)(?:aa|ab|aaz|abz)|retaa|retab)$"
)


class ArtifactError(RuntimeError):
    """Raised when the build or artifact violates the sealed profile."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactError(f"cannot read {path}: {error}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def bytes_sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def profile_digest(profile: dict[str, Any]) -> str:
    return bytes_sha256(canonical_json(profile).encode())


def load_profile() -> dict[str, Any]:
    profile = load_json(PROFILE_PATH)
    validate_profile(profile)
    return profile


def validate_profile(profile: Any) -> None:
    if not isinstance(profile, dict) or set(profile) != PROFILE_FIELDS:
        actual = set(profile) if isinstance(profile, dict) else set()
        raise ArtifactError(
            f"profile fields differ: missing={sorted(PROFILE_FIELDS - actual)}, "
            f"extra={sorted(actual - PROFILE_FIELDS)}"
        )
    if profile["schema"] != "rust-beam/otp-build-profile/v1":
        raise ArtifactError("unsupported OTP build profile schema")
    if profile["target"] != "aarch64-unknown-linux-musl":
        raise ArtifactError("profile target must be aarch64-unknown-linux-musl")
    if set(profile["sources"]) != SOURCE_IDS:
        raise ArtifactError("profile must seal exactly the five required sources")
    for source_id, digest in profile["sources"].items():
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ArtifactError(f"invalid source digest for {source_id}")
    compiler = profile["compiler"]
    if set(compiler) != {"version", "target_flags", "cflags", "ldflags"}:
        raise ArtifactError("compiler profile fields differ")
    required_target_flags = {
        "--target=aarch64-linux-musl",
        "-march=armv8-a",
        "-mno-outline-atomics",
    }
    if not required_target_flags.issubset(set(compiler["target_flags"])):
        raise ArtifactError("compiler target flags do not seal the Armv8-A baseline")
    required_configure = {
        "--disable-jit",
        "--disable-kernel-poll",
        "--disable-pie",
        "--enable-deterministic-build",
        "--disable-static-nifs",
        "--enable-static-drivers",
    }
    if not required_configure.issubset(set(profile["configure_flags"])):
        raise ArtifactError("configure profile is missing required static non-JIT flags")
    applications = profile["applications"]
    if set(applications) != {"included", "excluded"}:
        raise ArtifactError("application profile fields differ")
    included = applications["included"]
    excluded = applications["excluded"]
    if set(included) & set(excluded) or len(included) != len(set(included)) or len(excluded) != len(set(excluded)):
        raise ArtifactError("included and excluded application sets must be unique and disjoint")
    mandatory = {"compiler", "erl_interface", "erts", "kernel", "sasl", "stdlib"}
    if set(included) != mandatory:
        raise ArtifactError("included OTP application closure differs from the mandatory runtime_lab set")
    if profile["patches"] != []:
        raise ArtifactError("the Phase 0 profile permits no OTP source patches")
    contract = profile["artifact_contract"]
    expected_contract = {
        "elf_class": "ELF64",
        "elf_data": "little-endian",
        "machine": "AArch64",
        "type": "ET_EXEC",
        "dynamic_segment": False,
        "interpreter": None,
        "dt_needed": [],
        "load_alignment": 4096,
        "max_load_end_exclusive": 2147483648,
        "executable_stack": False,
        "runtime_relocations": False,
        "pt_tls": False,
        "lse_instructions": False,
        "branch_protection_instructions": False,
    }
    for key, expected in expected_contract.items():
        if contract.get(key) != expected:
            raise ArtifactError(f"artifact contract {key} must be {expected!r}")


def source_entries(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lock = load_json(SOURCE_LOCK_PATH)
    entries = {entry["id"]: entry for entry in lock.get("entries", [])}
    selected: dict[str, dict[str, Any]] = {}
    for source_id, expected_digest in profile["sources"].items():
        if source_id not in entries:
            raise ArtifactError(f"source lock is missing {source_id}")
        entry = entries[source_id]
        if entry.get("digest") != expected_digest:
            raise ArtifactError(f"profile/source-lock digest mismatch for {source_id}")
        selected[source_id] = entry
    return selected


def verified_archives(profile: dict[str, Any]) -> dict[str, Path]:
    archives: dict[str, Path] = {}
    for source_id, entry in source_entries(profile).items():
        digest = entry["digest"].removeprefix("sha256:")
        path = CACHE_ROOT / entry["mirror_path"]
        if not path.is_file():
            raise ArtifactError(f"missing cached source {source_id}: run just toolchain-bootstrap")
        actual = sha256(path)
        if actual != entry["digest"]:
            raise ArtifactError(f"cached source digest mismatch for {source_id}: {actual}")
        archives[source_id] = path
        print(f"verified {source_id} {actual}", flush=True)
    return archives


def run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    log: Path | None = None,
    capture: bool = False,
) -> str:
    rendered = shlex.join(argv)
    print(f"+ ({cwd}) {rendered}", flush=True)
    if capture:
        result = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if log is not None:
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as stream:
                stream.write(f"+ ({cwd}) {rendered}\n{result.stdout}")
        if result.returncode:
            raise ArtifactError(f"command failed ({result.returncode}): {rendered}\n{result.stdout[-4000:]}")
        return result.stdout
    log_stream = None
    try:
        if log is not None:
            log.parent.mkdir(parents=True, exist_ok=True)
            log_stream = log.open("a", encoding="utf-8")
            log_stream.write(f"+ ({cwd}) {rendered}\n")
            log_stream.flush()
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            if log_stream is not None:
                log_stream.write(line)
        status = process.wait()
        if status:
            raise ArtifactError(f"command failed ({status}): {rendered}; see {log}")
    finally:
        if log_stream is not None:
            log_stream.close()
    return ""


def extract_archive(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    run(
        ["tar", "-xf", str(archive), "-C", str(destination), "--strip-components=1"],
        cwd=ROOT,
    )


def extract_selected(archive: Path, suffixes: Iterable[str], destination: Path) -> list[Path]:
    listing = run(["tar", "-tf", str(archive)], cwd=ROOT, capture=True).splitlines()
    selected = [name for name in listing if any(name.endswith(suffix) for suffix in suffixes)]
    if not selected:
        raise ArtifactError(f"none of the requested members exist in {archive}")
    destination.mkdir(parents=True, exist_ok=True)
    run(["tar", "-xf", str(archive), "-C", str(destination), *selected], cwd=ROOT)
    return [destination / name for name in selected]


def tool_version(argv: list[str], cwd: Path = ROOT) -> str:
    output = run(argv, cwd=cwd, capture=True)
    lines = [line for line in output.splitlines() if line.strip()]
    return lines[0] if lines else output.strip()


def common_receipt_matches(common: Path, profile: dict[str, Any]) -> bool:
    receipt = common / "receipt.json"
    if not receipt.is_file():
        return False
    try:
        value = load_json(receipt)
    except ArtifactError:
        return False
    config = common / "musl-src/config.mak"
    if not config.is_file():
        return False
    config_text = config.read_text(encoding="utf-8")
    return (
        value.get("schema") == "rust-beam/otp-common-toolchain/v1"
        and value.get("sources") == profile["sources"]
        and profile["compiler"]["version"] in value.get("clang", "")
        and all(flag in config_text for flag in profile["compiler"]["target_flags"])
        and (common / "llvm/bin/clang").is_file()
        and (common / "sysroot/usr/lib/libc.a").is_file()
        and (common / "sysroot/usr/lib/crtbeginT.o").is_file()
    )


def prepare_common(profile: dict[str, Any], archives: dict[str, Path]) -> Path:
    common = WORK_ROOT / "common"
    if common_receipt_matches(common, profile):
        print(f"reusing verified common cross toolchain at {common}", flush=True)
        return common
    if common.exists():
        shutil.rmtree(common)
    common.mkdir(parents=True)
    setup_log = common / "setup.log"
    llvm = common / "llvm"
    print("extracting pinned x86_64 LLVM toolchain", flush=True)
    extract_archive(archives["llvm-x86_64"], llvm)
    clang = llvm / "bin/clang"
    clang_version = tool_version([str(clang), "--version"])
    if profile["compiler"]["version"] not in clang_version:
        raise ArtifactError(f"unexpected Clang identity: {clang_version}")

    with tempfile.TemporaryDirectory(dir=common, prefix="arm-builtins-") as temporary:
        extracted = extract_selected(
            archives["llvm-aarch64"],
            ["/lib/clang/20/lib/aarch64-unknown-linux-gnu/libclang_rt.builtins.a"],
            Path(temporary),
        )
        resource = llvm / "lib/clang/20/lib/aarch64-unknown-linux-musl"
        resource.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted[0], resource / "libclang_rt.builtins.a")

    musl_src = common / "musl-src"
    sysroot = common / "sysroot"
    extract_archive(archives["musl-source"], musl_src)
    compiler = profile["compiler"]
    target_flags = compiler["target_flags"]
    musl_cflags = [
        *target_flags,
        "-O2",
        f"-ffile-prefix-map={musl_src}=/usr/src/musl",
    ]
    musl_ldflags = [
        "-fuse-ld=lld",
        "-Wl,-z,max-page-size=4096",
        "-Wl,-z,common-page-size=4096",
        "-Wl,--build-id=none",
    ]
    musl_env = os.environ.copy()
    musl_env.update(
        {
            "LC_ALL": "C",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": str(profile["source_date_epoch"]),
            "ZERO_AR_DATE": "1",
            "CC": str(clang),
            "AR": str(llvm / "bin/llvm-ar"),
            "RANLIB": str(llvm / "bin/llvm-ranlib"),
            "CFLAGS": shlex.join(musl_cflags),
            "LDFLAGS": shlex.join(musl_ldflags),
        }
    )
    run(
        ["./configure", "--prefix=/usr", "--target=aarch64-linux-musl", "--enable-static", "--disable-shared"],
        cwd=musl_src,
        env=musl_env,
        log=setup_log,
    )
    jobs = str(min(os.cpu_count() or 1, 8))
    run(["make", f"-j{jobs}"], cwd=musl_src, env=musl_env, log=setup_log)
    run(["make", f"DESTDIR={sysroot}", "install"], cwd=musl_src, env=musl_env, log=setup_log)

    with tempfile.TemporaryDirectory(dir=common, prefix="compiler-rt-") as temporary:
        temp = Path(temporary)
        listing = run(["tar", "-tf", str(archives["llvm-source"])], cwd=ROOT, capture=True).splitlines()
        selected = [name for name in listing if "/compiler-rt/lib/builtins/" in name and not name.endswith("/")]
        if not selected:
            raise ArtifactError("LLVM source archive contains no compiler-rt builtins")
        run(["tar", "-xf", str(archives["llvm-source"]), "-C", str(temp), *selected], cwd=ROOT)
        crtbegin = next(temp.rglob("compiler-rt/lib/builtins/crtbegin.c"), None)
        crtend = next(temp.rglob("compiler-rt/lib/builtins/crtend.c"), None)
        if crtbegin is None or crtend is None:
            raise ArtifactError("compiler-rt CRT sources are missing")
        crt_flags = [
            *target_flags,
            f"--sysroot={sysroot}",
            "-std=c11",
            "-DCRT_HAS_INITFINI_ARRAY",
            "-DEH_USE_FRAME_REGISTRY",
            "-fPIC",
            "-Wno-pedantic",
            "-O2",
        ]
        libdir = sysroot / "usr/lib"
        for output in ("crtbegin.o", "crtbeginS.o", "crtbeginT.o"):
            run([str(clang), *crt_flags, "-c", str(crtbegin), "-o", str(libdir / output)], cwd=ROOT, log=setup_log)
        for output in ("crtend.o", "crtendS.o"):
            run([str(clang), *crt_flags, "-c", str(crtend), "-o", str(libdir / output)], cwd=ROOT, log=setup_log)

    receipt = {
        "schema": "rust-beam/otp-common-toolchain/v1",
        "profile_digest": profile_digest(profile),
        "sources": profile["sources"],
        "clang": clang_version,
        "musl_libc": {
            "path": "sysroot/usr/lib/libc.a",
            "digest": sha256(sysroot / "usr/lib/libc.a"),
        },
        "compiler_rt_builtins": {
            "path": "llvm/lib/clang/20/lib/aarch64-unknown-linux-musl/libclang_rt.builtins.a",
            "digest": sha256(llvm / "lib/clang/20/lib/aarch64-unknown-linux-musl/libclang_rt.builtins.a"),
        },
        "crt_objects": {
            name: sha256(sysroot / "usr/lib" / name)
            for name in ("crtbegin.o", "crtbeginS.o", "crtbeginT.o", "crtend.o", "crtendS.o")
        },
    }
    (common / "receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    return common


def write_compiler_wrapper(path: Path, clang: Path, common: Path, lane: Path, cxx: bool = False) -> None:
    compiler = clang.with_name("clang++") if cxx else clang
    beam_map = lane / "beam-link.map"
    text = f"""#!/bin/sh
set -eu
map_flag=
want_output=no
for argument in "$@"; do
    if [ "$want_output" = yes ]; then
        case "$argument" in
            */beam.emu|beam.emu|*/beam.smp|beam.smp) map_flag={shlex.quote(f'-Wl,-Map,{beam_map}')} ;;
        esac
        want_output=no
    elif [ "$argument" = -o ]; then
        want_output=yes
    fi
done
exec {shlex.quote(str(compiler))} --target=aarch64-linux-musl --sysroot={shlex.quote(str(common / 'sysroot'))} -march=armv8-a -mno-outline-atomics ${{map_flag:+"$map_flag"}} "$@"
"""
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def xcomp_text(profile: dict[str, Any], common: Path, lane: Path) -> str:
    wrapper_dir = lane / "toolchain"
    cc = wrapper_dir / "aarch64-linux-musl-clang"
    cxx = wrapper_dir / "aarch64-linux-musl-clang++"
    llvm = common / "llvm"
    prefix_maps = [
        f"-ffile-prefix-map={lane / 'src'}=/usr/src/otp",
        f"-ffile-prefix-map={common}=/opt/rust-beam-cross",
    ]
    cflags = [*profile["compiler"]["cflags"], *prefix_maps]
    ldflags = profile["compiler"]["ldflags"]
    flags = " ".join(profile["configure_flags"])
    lines = [
        "# Generated from toolchain/otp/aarch64-linux-musl.json; do not edit.",
        "erl_xcomp_build=guess",
        "erl_xcomp_host=aarch64-unknown-linux-musl",
        f"erl_xcomp_configure_flags={shlex.quote(flags)}",
        f"CC={shlex.quote(str(cc))}",
        f"CFLAGS={shlex.quote(' '.join(cflags))}",
        f"STATIC_CFLAGS={shlex.quote(' '.join(cflags))}",
        "CFLAG_RUNTIME_LIBRARY_PATH=",
        f"CPP={shlex.quote(str(cc) + ' -E')}",
        "CPPFLAGS=",
        f"CXX={shlex.quote(str(cxx))}",
        f"CXXFLAGS={shlex.quote(' '.join(cflags))}",
        f"LD={shlex.quote(str(cc))}",
        f"LDFLAGS={shlex.quote(' '.join(ldflags))}",
        "LIBS=",
        f"DED_LD={shlex.quote(str(cc))}",
        "DED_LDFLAGS='-r -nostdlib -fuse-ld=lld'",
        "DED_LD_FLAG_RUNTIME_LIBRARY_PATH=",
        f"RANLIB={shlex.quote(str(llvm / 'bin/llvm-ranlib'))}",
        f"AR={shlex.quote(str(llvm / 'bin/llvm-ar'))}",
        "GETCONF=false",
        f"erl_xcomp_sysroot={shlex.quote(str(common / 'sysroot'))}",
        f"erl_xcomp_isysroot={shlex.quote(str(common / 'sysroot'))}",
    ]
    lines.extend(f"{key}={shlex.quote(value)}" for key, value in profile["cross_answers"].items())
    return "\n".join(lines) + "\n"


def build_environment(profile: dict[str, Any], common: Path, lane: Path) -> dict[str, str]:
    env = os.environ.copy()
    for name in list(env):
        if name.startswith("ERL_") or name in {"CC", "CXX", "CPP", "LD", "AR", "RANLIB", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "LIBS"}:
            env.pop(name, None)
    home = lane / "home"
    temporary = lane / "tmp"
    home.mkdir()
    temporary.mkdir()
    env.update(
        {
            "HOME": str(home),
            "TMPDIR": str(temporary),
            "LC_ALL": "C",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": str(profile["source_date_epoch"]),
            "ZERO_AR_DATE": "1",
            "V": "1",
            "MAKEFLAGS": f"-j{min(os.cpu_count() or 1, 8)}",
            "PATH": f"{common / 'llvm/bin'}:{env['PATH']}",
        }
    )
    return env


def configuration_manifest(source: Path, target: str) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    names = {"config.log", "config.status", "config.h", "SKIP"}
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if path.name in names or (path.name == "Makefile" and (target in relative or relative.count("/") <= 2)):
            manifest.append({"path": relative, "size": path.stat().st_size, "digest": sha256(path)})
    return manifest


def locate_beam(release: Path) -> Path:
    matches = sorted(release.glob("erts-*/bin/beam.smp"))
    if len(matches) != 1:
        raise ArtifactError(f"expected one released beam.smp, found {len(matches)}")
    return matches[0]


def build_lane(name: str, profile: dict[str, Any], archives: dict[str, Path], common: Path) -> Path:
    destination = WORK_ROOT / name
    if destination.exists():
        shutil.rmtree(destination)
    lane = BUILD_ROOT
    if lane.exists():
        shutil.rmtree(lane)
    lane.mkdir(parents=True)
    source = lane / "src"
    release = lane / "release"
    extract_archive(archives["otp-source"], source)
    wrapper_dir = lane / "toolchain"
    wrapper_dir.mkdir()
    clang = common / "llvm/bin/clang"
    write_compiler_wrapper(wrapper_dir / "aarch64-linux-musl-clang", clang, common, lane)
    write_compiler_wrapper(wrapper_dir / "aarch64-linux-musl-clang++", clang, common, lane, cxx=True)
    xcomp = lane / "erl-xcomp-aarch64-linux-musl.conf"
    xcomp.write_text(xcomp_text(profile, common, lane), encoding="utf-8")
    env = build_environment(profile, common, lane)
    log = lane / "build.log"
    configure_command = ["./otp_build", "configure", f"--xcomp-conf={xcomp}"]
    boot_command = ["./otp_build", "boot", "-a"]
    release_command = ["./otp_build", "release", "-a", str(release)]
    run(configure_command, cwd=source, env=env, log=log)
    skip_file = source / "lib/SKIP-APPLICATIONS"
    configured_skips = set(skip_file.read_text(encoding="utf-8").splitlines()) if skip_file.is_file() else set()
    configured_skips.update(profile["applications"]["excluded"])
    skip_file.write_text("".join(f"{application}\n" for application in sorted(configured_skips)), encoding="utf-8")
    with log.open("a", encoding="utf-8") as stream:
        stream.write(
            "+ generated lib/SKIP-APPLICATIONS from the sealed application exclusion profile; "
            "this makes --without-odbc exclude the Erlang application in addition to its native driver\n"
        )
    run(boot_command, cwd=source, env=env, log=log)
    run(release_command, cwd=source, env=env, log=log)
    commands = [configure_command, boot_command, release_command]
    beam = locate_beam(release)
    if not (lane / "beam-link.map").is_file():
        raise ArtifactError("target linker did not produce the required beam link map")
    excluded = profile["applications"]["excluded"]
    recorded_skips = set(skip_file.read_text(encoding="utf-8").splitlines())
    missing_skips = [application for application in excluded if application not in recorded_skips]
    if missing_skips:
        raise ArtifactError(f"excluded OTP applications lack generated SKIP files: {missing_skips}")
    controlled_environment = {
        key: env[key]
        for key in ("HOME", "TMPDIR", "LC_ALL", "TZ", "SOURCE_DATE_EPOCH", "ZERO_AR_DATE", "V", "MAKEFLAGS", "PATH")
    }
    receipt = {
        "schema": "rust-beam/otp-build-receipt/v1",
        "lane": name,
        "profile": {"path": PROFILE_PATH.relative_to(ROOT).as_posix(), "digest": sha256(PROFILE_PATH)},
        "source_lock": {"path": SOURCE_LOCK_PATH.relative_to(ROOT).as_posix(), "digest": sha256(SOURCE_LOCK_PATH)},
        "sources": source_entries(profile),
        "source_start": {
            "archive_verified": True,
            "fresh_extraction": True,
            "upstream_reference": source_entries(profile)["otp-source"]["immutable_reference"],
            "patches": [],
        },
        "commands": [shlex.join(command) for command in commands],
        "environment": controlled_environment,
        "cross_configuration": {
            "path": xcomp.relative_to(lane).as_posix(),
            "digest": sha256(xcomp),
            "configure_flags": profile["configure_flags"],
            "cross_answers": profile["cross_answers"],
            "application_skip_file": {
                "path": skip_file.relative_to(source).as_posix(),
                "digest": sha256(skip_file),
                "generated_odbc_override": True
            },
        },
        "generated_configuration": configuration_manifest(source, profile["target"]),
        "tools": {
            "host": {
                "architecture": platform.machine(),
                "system": platform.platform(),
                "make": tool_version(["make", "--version"]),
                "perl": tool_version(["perl", "--version"]),
            },
            "target": {
                "clang": tool_version([str(common / "llvm/bin/clang"), "--version"]),
                "lld": tool_version([str(common / "llvm/bin/ld.lld"), "--version"]),
                "llvm_ar": tool_version([str(common / "llvm/bin/llvm-ar"), "--version"]),
            },
        },
        "outputs": {
            "release": release.relative_to(lane).as_posix(),
            "beam": beam.relative_to(lane).as_posix(),
            "beam_size": beam.stat().st_size,
            "beam_digest": sha256(beam),
            "beam_link_map": {"path": "beam-link.map", "digest": sha256(lane / "beam-link.map")},
            "build_log": {"path": "build.log", "digest": sha256(log)},
        },
    }
    (lane / "build-receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    lane.rename(destination)
    beam = locate_beam(destination / "release")
    print(f"built {beam.relative_to(ROOT)} {sha256(beam)}", flush=True)
    return destination


def parse_elf(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ArtifactError(f"not an ELF file: {path}")
    if data[4] != 2 or data[5] != 1:
        raise ArtifactError(f"ELF must be 64-bit little-endian: {path}")
    header = struct.unpack_from("<16sHHIQQQIHHHHHH", data, 0)
    e_type, e_machine = header[1], header[2]
    e_phoff, e_shoff = header[5], header[6]
    e_phentsize, e_phnum = header[9], header[10]
    e_shentsize, e_shnum = header[11], header[12]
    programs: list[dict[str, Any]] = []
    for index in range(e_phnum):
        offset = e_phoff + index * e_phentsize
        if offset + 56 > len(data):
            raise ArtifactError(f"truncated program header in {path}")
        p_type, p_flags, p_offset, p_vaddr, _, p_filesz, p_memsz, p_align = struct.unpack_from(
            "<IIQQQQQQ", data, offset
        )
        programs.append(
            {
                "type": PROGRAM_TYPES.get(p_type, f"0x{p_type:x}"),
                "flags": p_flags,
                "offset": p_offset,
                "vaddr": p_vaddr,
                "filesz": p_filesz,
                "memsz": p_memsz,
                "align": p_align,
            }
        )
    relocation_sections: list[dict[str, int]] = []
    for index in range(e_shnum):
        offset = e_shoff + index * e_shentsize
        if offset + 64 > len(data):
            raise ArtifactError(f"truncated section header in {path}")
        section = struct.unpack_from("<IIQQQQIIQQ", data, offset)
        if section[1] in {4, 9, 19}:
            relocation_sections.append({"index": index, "type": section[1], "size": section[5]})
    return {
        "class": "ELF64",
        "data": "little-endian",
        "osabi": data[7],
        "type": ELF_TYPES.get(e_type, str(e_type)),
        "machine": "AArch64" if e_machine == 183 else str(e_machine),
        "program_headers": programs,
        "relocation_sections": relocation_sections,
    }


def validate_runtime_elf(path: Path, metadata: dict[str, Any], contract: dict[str, Any]) -> None:
    if metadata["machine"] != contract["machine"]:
        raise ArtifactError(f"non-AArch64 ELF in release closure: {path}")
    if metadata["type"] != contract["type"]:
        raise ArtifactError(f"runtime ELF is {metadata['type']}, expected {contract['type']}: {path}")
    programs = metadata["program_headers"]
    types = {program["type"] for program in programs}
    if "PT_INTERP" in types:
        raise ArtifactError(f"runtime ELF has PT_INTERP: {path}")
    if "PT_DYNAMIC" in types:
        raise ArtifactError(f"runtime ELF has PT_DYNAMIC and may contain DT_NEEDED: {path}")
    loads = [program for program in programs if program["type"] == "PT_LOAD"]
    if not loads or any(program["align"] != contract["load_alignment"] for program in loads):
        raise ArtifactError(f"runtime ELF PT_LOAD alignment differs from 4096: {path}")
    if any(program["vaddr"] + program["memsz"] >= contract["max_load_end_exclusive"] for program in loads):
        raise ArtifactError(f"runtime ELF is not wholly linked below 2 GiB: {path}")
    has_tls = "PT_TLS" in types
    if has_tls != contract["pt_tls"]:
        raise ArtifactError(f"runtime ELF PT_TLS presence differs from the sealed contract: {path}")
    stacks = [program for program in programs if program["type"] == "PT_GNU_STACK"]
    if len(stacks) != 1 or stacks[0]["flags"] & 1:
        raise ArtifactError(f"runtime ELF lacks a single non-executable GNU stack: {path}")
    if metadata["relocation_sections"]:
        raise ArtifactError(f"runtime ELF contains runtime relocation sections: {path}")


def llvm_output(tool: Path, arguments: list[str], path: Path) -> str:
    result = subprocess.run(
        [str(tool), *arguments, str(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode:
        raise ArtifactError(f"{tool.name} failed for {path}: {result.stdout[-2000:]}")
    return result.stdout


def undefined_elf_symbols(readelf: Path, path: Path) -> list[dict[str, str]]:
    symbols: list[dict[str, str]] = []
    output = llvm_output(readelf, ["--symbols"], path)
    pattern = re.compile(
        r"^\s*(\d+):\s+\S+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+UND(?:\s+(.*))?$"
    )
    for line in output.splitlines():
        match = pattern.match(line)
        if not match or match.group(1) == "0":
            continue
        symbols.append(
            {
                "type": match.group(2),
                "binding": match.group(3),
                "visibility": match.group(4),
                "name": (match.group(5) or "").strip(),
            }
        )
    return symbols


def native_closure(release: Path, common: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    llvm_nm = common / "llvm/bin/llvm-nm"
    llvm_readelf = common / "llvm/bin/llvm-readelf"
    closure: list[dict[str, Any]] = []
    for path in sorted(item for item in release.rglob("*") if item.is_file()):
        relative = path.relative_to(release).as_posix()
        with path.open("rb") as stream:
            magic = stream.read(8)
        if path.suffix == ".so" or ".so." in path.name:
            raise ArtifactError(f"dynamic library is forbidden in release closure: {relative}")
        if magic.startswith(b"\x7fELF"):
            metadata = parse_elf(path)
            validate_runtime_elf(path, metadata, contract)
            undefined = undefined_elf_symbols(llvm_readelf, path)
            disallowed = [
                symbol
                for symbol in undefined
                if symbol["binding"] != "WEAK"
                and not (
                    symbol["binding"] == "LOCAL"
                    and symbol["visibility"] == "HIDDEN"
                    and symbol["name"] == "_DYNAMIC"
                )
            ]
            if disallowed:
                raise ArtifactError(f"runtime ELF contains unresolved strong symbols: {relative}: {disallowed[:8]}")
            closure.append(
                {
                    "path": relative,
                    "kind": "elf",
                    "size": path.stat().st_size,
                    "digest": sha256(path),
                    "elf": metadata,
                    "undefined_symbols": undefined,
                }
            )
        elif magic == b"!<arch>\n":
            symbols = [line.strip() for line in llvm_output(llvm_nm, ["--undefined-only"], path).splitlines() if line.strip()]
            closure.append(
                {
                    "path": relative,
                    "kind": "archive",
                    "size": path.stat().st_size,
                    "digest": sha256(path),
                    "undefined_symbols": symbols,
                }
            )
    if not closure:
        raise ArtifactError("release contains no native objects")
    return closure


def installed_applications(release: Path) -> list[str]:
    applications: list[str] = []
    for app_file in release.glob("lib/*/ebin/*.app"):
        applications.append(app_file.parent.parent.name.rsplit("-", 1)[0])
    return sorted(set(applications))


def generated_builtins(source: Path) -> dict[str, Any]:
    candidates = [
        path
        for path in source.rglob("driver_tab.c")
        if "aarch64-unknown-linux-musl" in path.relative_to(source).parts
    ]
    if len(candidates) != 1:
        raise ArtifactError(f"expected one target driver_tab.c, found {len(candidates)}")
    text = candidates[0].read_text(encoding="utf-8")
    drivers = sorted(set(re.findall(r"\{&(\w+)_driver_entry,\s*0\}", text)))
    static_drivers = sorted(set(re.findall(r"\{NULL,\s*1\},\s*/\*\s*(\w+)\s*\*/", text)))
    nifs = sorted(set(re.findall(r"\{&(\w+)_nif_init,\s*0,", text)))
    application_nifs = sorted(set(re.findall(r"\{&(\w+)_nif_init,\s*1,", text)))
    return {
        "generated_table": candidates[0].relative_to(source).as_posix(),
        "builtin_drivers": drivers,
        "statically_linked_application_drivers": static_drivers,
        "builtin_nifs": nifs,
        "statically_linked_application_nifs": application_nifs,
    }


def cpu_extension_scan(objdump: Path, path: Path) -> tuple[list[str], list[str], int]:
    output = llvm_output(objdump, ["--disassemble", "--no-show-raw-insn"], path)
    lse_matches: list[str] = []
    branch_protection_matches: list[str] = []
    instructions = 0
    for line in output.splitlines():
        match = re.match(r"^\s*[0-9a-f]+:\s+([a-z0-9.]+)\b", line)
        if not match:
            continue
        instructions += 1
        mnemonic = match.group(1).split(".", 1)[0]
        if LSE_MNEMONICS.fullmatch(mnemonic):
            lse_matches.append(line.strip())
        if BRANCH_PROTECTION_MNEMONICS.fullmatch(mnemonic):
            branch_protection_matches.append(line.strip())
    return lse_matches, branch_protection_matches, instructions


def build_mode_report(lane: Path, profile: dict[str, Any]) -> dict[str, Any]:
    target = profile["target"]
    makefile = lane / "src/erts/emulator" / target / "Makefile"
    config_h = lane / "src/erts" / target / "config.h"
    link_map = lane / "beam-link.map"
    make_text = makefile.read_text(encoding="utf-8")
    config_text = config_h.read_text(encoding="utf-8")
    map_text = link_map.read_text(encoding="utf-8")
    checks = {
        "jit_disabled": "JIT_ENABLED=no" in make_text and "/jit/" not in map_text,
        "kernel_poll_disabled": "/* #undef ERTS_ENABLE_KERNEL_POLL */" in config_text,
        "application_nifs_disabled": "STATIC_NIFS=no" in make_text,
        "application_drivers_static": "STATIC_DRIVERS=yes" in make_text,
        "security_hardening_extensions_disabled": "-mbranch-protection=standard" not in make_text,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ArtifactError(f"generated OTP build mode differs from profile: {failed}")
    return {
        "checks": checks,
        "generated_makefile": makefile.relative_to(lane / "src").as_posix(),
        "generated_config_h": config_h.relative_to(lane / "src").as_posix(),
        "configure_flags": profile["configure_flags"],
    }


def runtime_load_attempts(release: Path, strings_tool: Path) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    markers = re.compile(r"(?:load_nif|open_port|spawn_executable|inet_gethost|erl_child_setup|_nif)", re.IGNORECASE)
    for path in sorted(release.glob("lib/*/ebin/*.beam")):
        matches = sorted(set(line.strip() for line in llvm_output(strings_tool, [], path).splitlines() if markers.search(line)))
        if matches:
            attempts.append({"path": path.relative_to(release).as_posix(), "strings": matches})
    return attempts


def write_inspection_reports(lane: Path, profile: dict[str, Any], common: Path) -> dict[str, Any]:
    release = lane / "release"
    beam = locate_beam(release)
    inspection = lane / "inspection"
    if inspection.exists():
        shutil.rmtree(inspection)
    inspection.mkdir()
    llvm = common / "llvm/bin"
    closure = native_closure(release, common, profile["artifact_contract"])
    applications = installed_applications(release)
    if applications != profile["applications"]["included"]:
        raise ArtifactError(f"installed application closure differs: {applications}")
    builtins = generated_builtins(lane / "src")
    if builtins["statically_linked_application_nifs"] != profile["native_policy"]["application_nifs"]:
        raise ArtifactError("unapproved application NIF is linked into beam.smp")
    if builtins["statically_linked_application_drivers"] != profile["native_policy"]["dynamic_drivers"]:
        raise ArtifactError("unapproved application driver is linked into beam.smp")
    lse_matches, branch_protection_matches, instruction_count = cpu_extension_scan(llvm / "llvm-objdump", beam)
    if lse_matches:
        raise ArtifactError(f"beam.smp contains Arm LSE instructions: {lse_matches[:8]}")
    if branch_protection_matches:
        raise ArtifactError(f"beam.smp contains out-of-profile branch-protection instructions: {branch_protection_matches[:8]}")

    reports = {
        "native-closure.json": closure,
        "applications.json": {
            "included": applications,
            "excluded": profile["applications"]["excluded"],
        },
        "builtins.json": builtins,
        "runtime-load-attempts.json": {
            "method": "String-table inventory; P006 owns authoritative target runtime load tracing.",
            "attempts": runtime_load_attempts(release, llvm / "llvm-strings"),
        },
        "cpu-scan.json": {
            "tool": tool_version([str(llvm / "llvm-objdump"), "--version"]),
            "instructions_scanned": instruction_count,
            "lse_instructions": lse_matches,
            "branch_protection_instructions": branch_protection_matches,
            "compiler_flags": profile["compiler"]["target_flags"],
            "assumptions": profile["artifact_contract"]["auxv"],
        },
        "build-mode.json": build_mode_report(lane, profile),
    }
    for name, value in reports.items():
        (inspection / name).write_text(canonical_json(value), encoding="utf-8")
    textual_commands = {
        "beam-headers.txt": ["llvm-readelf", "--file-header", "--program-headers", "--dynamic-table", str(beam)],
        "beam-relocations.txt": ["llvm-readelf", "--relocations", str(beam)],
        "beam-symbols.txt": ["llvm-readelf", "--symbols", str(beam)],
    }
    for name, command in textual_commands.items():
        tool = llvm / command[0]
        output = llvm_output(tool, command[1:-1], beam)
        (inspection / name).write_text(output, encoding="utf-8")
    shutil.copy2(lane / "beam-link.map", inspection / "beam-link.map")
    shutil.copy2(lane / "erl-xcomp-aarch64-linux-musl.conf", inspection / "erl-xcomp-aarch64-linux-musl.conf")
    receipt = {
        "schema": "rust-beam/otp-artifact-inspection/v1",
        "profile_digest": sha256(PROFILE_PATH),
        "beam": {
            "path": beam.relative_to(lane).as_posix(),
            "size": beam.stat().st_size,
            "digest": sha256(beam),
            "elf": parse_elf(beam),
        },
        "native_closure": {
            "count": len(closure),
            "digest": sha256(inspection / "native-closure.json"),
        },
        "applications": applications,
        "builtins": builtins,
        "patch_audit": {
            "profile_patches": profile["patches"],
            "source_archive": profile["sources"]["otp-source"],
            "source_operations_before_build": ["verify digest", "extract archive"],
            "semantic_otp_patches": [],
        },
        "artifact_assumptions": profile["artifact_contract"],
        "reports": {
            path.name: sha256(path)
            for path in sorted(inspection.iterdir())
            if path.is_file()
        },
    }
    (inspection / "inspection-receipt.json").write_text(canonical_json(receipt), encoding="utf-8")
    print(f"inspected {len(closure)} native objects; beam.smp {sha256(beam)}", flush=True)
    return receipt


def inspect_lane(name: str, profile: dict[str, Any], common: Path) -> dict[str, Any]:
    lane = WORK_ROOT / name
    if not (lane / "build-receipt.json").is_file():
        raise ArtifactError(f"missing {name} build; run just build-otp first")
    receipt = load_json(lane / "build-receipt.json")
    if receipt.get("profile", {}).get("digest") != sha256(PROFILE_PATH):
        raise ArtifactError(f"{name} was built with a different profile; rebuild it")
    return write_inspection_reports(lane, profile, common)


def comparison_manifest(lane: Path) -> list[dict[str, Any]]:
    path = lane / "inspection/native-closure.json"
    closure = load_json(path)
    return [
        {"path": entry["path"], "kind": entry["kind"], "size": entry["size"], "digest": entry["digest"]}
        for entry in closure
    ]


def verify_rebuild(profile: dict[str, Any], archives: dict[str, Path], common: Path) -> None:
    primary = WORK_ROOT / "primary"
    if not (primary / "build-receipt.json").is_file():
        build_lane("primary", profile, archives, common)
    inspect_lane("primary", profile, common)
    secondary = build_lane("rebuild", profile, archives, common)
    inspect_lane("rebuild", profile, common)
    first = comparison_manifest(primary)
    second = comparison_manifest(secondary)
    first_beam = locate_beam(primary / "release")
    second_beam = locate_beam(secondary / "release")
    comparison = {
        "schema": "rust-beam/otp-rebuild-comparison/v1",
        "result": "equivalent",
        "equivalence": "Every native runtime object has the same relative path, kind, size, and SHA-256 digest.",
        "primary_beam": sha256(first_beam),
        "rebuild_beam": sha256(second_beam),
        "beam_exact_match": sha256(first_beam) == sha256(second_beam),
        "native_closure_exact_match": first == second,
        "native_closure_count": len(first),
        "profile_digest": sha256(PROFILE_PATH),
    }
    if not comparison["beam_exact_match"] or not comparison["native_closure_exact_match"]:
        comparison["result"] = "mismatch"
        (WORK_ROOT / "rebuild-comparison.json").write_text(canonical_json(comparison), encoding="utf-8")
        raise ArtifactError("clean rebuild differs from the primary native closure")
    (WORK_ROOT / "rebuild-comparison.json").write_text(canonical_json(comparison), encoding="utf-8")
    print(f"clean rebuild equivalent: {len(first)} native objects, beam {sha256(first_beam)}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="build a fresh primary OTP release")
    inspect_parser = subparsers.add_parser("inspect", help="inspect a built OTP release")
    inspect_parser.add_argument("--lane", default="primary")
    subparsers.add_parser("verify-rebuild", help="build a second clean release and compare native closure")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        profile = load_profile()
        archives = verified_archives(profile)
        common = prepare_common(profile, archives)
        if args.command == "build":
            build_lane("primary", profile, archives, common)
        elif args.command == "inspect":
            inspect_lane(args.lane, profile, common)
        elif args.command == "verify-rebuild":
            verify_rebuild(profile, archives, common)
        else:
            raise AssertionError(args.command)
    except ArtifactError as error:
        print(f"otp-artifact: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
