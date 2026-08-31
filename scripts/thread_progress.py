#!/usr/bin/env python3
"""Build and exercise the RB-T-P017 Linux thread-progress probe."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

FAULTS = (
    "lost-wakeup",
    "stalled-startup",
    "premature-futex-block",
    "scheduler-stall",
    "thread-exit-join",
)


def run(command: list[str], *, root: Path, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def build(root: Path) -> Path:
    source = root / "tests/thread-progress/thread_progress_probe.c"
    output = root / "target/thread-progress/thread-progress-probe"
    output.parent.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get("CC", "cc")
    command = [
        compiler,
        "-std=c11",
        "-O2",
        "-g",
        "-pthread",
        "-Wall",
        "-Wextra",
        "-Wpedantic",
        "-Werror",
        "-Wconversion",
        "-Wshadow",
        str(source),
        "-o",
        str(output),
    ]
    result = run(command, root=root)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    return output


def check(root: Path) -> int:
    probe = build(root)
    normal = run([str(probe), "--inject", "none"], root=root)
    if normal.returncode != 0 or "status=pass" not in normal.stdout:
        sys.stderr.write(normal.stdout + normal.stderr)
        return 1
    print(normal.stdout.strip())

    for fault in FAULTS:
        result = run([str(probe), "--inject", fault], root=root)
        combined = result.stdout + result.stderr
        expected = f"status=fail detected={fault} injected={fault}"
        if result.returncode != 1 or expected not in combined:
            sys.stderr.write(f"fault oracle failed for {fault}:\n{combined}")
            return 1
        print(f"oracle=pass {combined.strip()}")
    print(f"thread-progress probe: 1 healthy profile and {len(FAULTS)} injected faults passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "build":
        print(build(root).relative_to(root))
        return 0
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
