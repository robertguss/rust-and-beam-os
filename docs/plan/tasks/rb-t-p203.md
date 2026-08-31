---
schema: "repo-plan/v1"
id: "RB-T-P203"
title: "Implement the read-only VFS and admitted file/path syscalls"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P201"
  - "RB-T-P202"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-03"
x_linear_id: "ROB-711"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-711/p2-03-implement-the-read-only-vfs-and-admitted-filepath-syscalls"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P203: Implement the read-only VFS and admitted file/path syscalls

## Goal

Let ERTS read its immutable release tree through exact bounded file semantics without creating a general mutable Unix filesystem.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P201, RB-T-P202.

## Deliverables

* Adapt the immutable archive into internal inode/directory/file-description objects with stable metadata and independent offsets.
* Implement only contracted operations such as admitted `openat`, read/vector read, close, seek, stat-family queries, directory iteration, path queries, and descriptor flags.
* Define path normalization, root confinement, symlink policy, directory ordering, EOF, short-read, and error behavior.
* Create C probes for concurrent reads, independent/shared offsets, directory walking, invalid paths/flags, file-descriptor exhaustion, and closure.

## Acceptance criteria

- [ ] No path escapes the process's provisioned release-tree root.
- [ ] Read-only semantics reject every mutating open/operation.
- [ ] Concurrent and duplicated descriptor behavior matches the recorded contract.
- [ ] ERTS release files can be inventoried entirely through the admitted API.
- [ ] All path lengths, component counts, vectors, and descriptor tables are bounded.

## Verification

* `just test-beam-vfs`
* `just fuzz-beam-paths`

## Evidence

* Run positive, negative, boundary, concurrency, and exhaustion probes.
* Differentially compare admitted behavior with the AArch64 Linux reference.
* Fuzz archive paths and syscall arguments.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit correction — 2026-08-30

### Immutable namespace and path contract

* Freeze whether the image builder rejects symlinks entirely, dereferences them into regular immutable entries, or preserves a narrowly supported symlink subset. Do not discover this during ERTS boot; audit the exact Mix-release tree in RB-T-P007 and prove every required entry is representable.
* Treat Linux pathnames as bounded byte sequences, not assumed UTF-8 strings. Reject embedded NUL; define repeated `/`, `.`, `..`, absolute versus relative paths, trailing slash, empty path, root, maximum bytes/components, and `openat` `dirfd` behavior exactly for the admitted calls.
* Root confinement is checked during component traversal, including any symlink target if symlinks are admitted. Lexical normalization alone is insufficient. No path may reach another process image, kernel archive metadata, device tree, host file, or hidden compatibility object.
* Distinguish inode/image node, open file description, and descriptor. Duplicated descriptors share or do not share offsets exactly as observed; independent opens never accidentally share mutable offset state.

### File and directory semantics

* Admit only exact flag combinations and reject all create/write/truncate/append/tmpfile/directory-mutation forms before object allocation. Define error precedence for wrong type, missing component, not-a-directory, trailing slash, unsupported flags, permission, exhaustion, and invalid user memory.
* Define immutable stat metadata widths/overflow, mode/type bits, inode stability, link count policy, sizes, block fields, timestamps/build epoch, and device IDs so results are reproducible and cannot leak host archive metadata.
* Define short read/EOF, positioned versus offset-mutating reads, vector validation/partial result, seek overflow, directory ordering, `getdents64` record alignment/cookies, buffer-too-small behavior, and end-of-directory. Host filesystem enumeration order must never leak into the image.
* File mappings in RB-E-P204 must reference the same immutable object/generation and cannot outlive or mutate backing bytes; closing a descriptor does not invalidate a legal mapping.
* Descriptor/object tables, path scratch space, vector counts, directory records, and open descriptions have explicit per-process/global bounds and failure-atomic allocation.

### Required additional evidence

* Generated path corpus covering every component boundary, dot/dot-dot/root/empty/trailing slash/NUL/non-UTF8 byte, symlink loop/escape if applicable, type mismatch, long path, archive corruption, and host-order variation.
* Differential probes for open/openat/stat/fstat/read/readv/pread/seek/getdents/dup/close semantics admitted by the trace; concurrent offset tests; descriptor generation reuse; image hash verification; and a host-leak scan.
* Prove the complete release inventory opens from a sealed read-only image and that every mutating operation fails without changing counters or metadata.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Model open-file descriptions, shared offsets/status flags, per-fd CLOEXEC, dup semantics, /dev/null, release path probes, and directory/stat errno precedence.
