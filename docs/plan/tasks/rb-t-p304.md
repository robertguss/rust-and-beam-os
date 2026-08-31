---
schema: "repo-plan/v1"
id: "RB-T-P304"
title: "Validate ERTS module loading against the immutable release tree"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P301"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-04"
x_linear_id: "ROB-726"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-726/p3-04-validate-erts-module-loading-against-the-immutable-release-tree"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P304: Validate ERTS module loading against the immutable release tree

## Goal

Prove code loading and file access independently enough that boot failures are not confused with scheduler or VM defects.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P301.

## Deliverables

* Package the exact `kernel`/`stdlib` BEAM files, boot data, and required ERTS support data using the target release layout.
* Instrument read-only VFS operations by module/path and correlate them with the reference run.
* Test short reads, directory iteration, seek, metadata, missing/truncated/corrupt module, descriptor exhaustion, and concurrent reads.
* Verify that code paths and root directory cannot escape the provisioned tree.

## Acceptance criteria

- [ ] Every required module and boot artifact is located through the declared release layout.
- [ ] Corrupt or missing content fails deterministically with the expected ERTS error and kernel trace.
- [ ] Concurrent loader reads preserve offsets and data integrity.
- [ ] No mutable file, temporary directory, home directory, locale database, or host path is silently required.

## Verification

* `just test-erts-loader-files`
* `just trace-erts-file-access`

## Evidence

* Run a module/file fault matrix before the full boot test.
* Compare normalized access traces with AArch64 Linux.
* Save release-tree inventory and hashes.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Additional context
### Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.
### Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.
### Readiness-audit correction — 2026-08-30

* Consume the exact RB-T-P007 release-tree manifest, symlink policy, path-byte rules, deterministic metadata, module/boot-file hashes, and directory order. Repacking may not silently dereference, rename, normalize, timestamp, or reorder entries differently from the VFS contract.
* Inventory every file opened on the native AArch64 reference, classify required/optional/probe-only/forbidden, and prove the final guest opens only declared image objects. Any new path or metadata query reopens the M2 contract evidence.
* Distinguish code-path resolution, directory enumeration, open-file-description offsets, short reads, positioned reads, metadata, and module-content validation. Do not infer that a successful final module load proves each underlying behavior.
* Corrupt/truncate every relevant region of representative BEAM/boot/archive files, not only the first bytes; include short reads at every boundary, descriptor exhaustion mid-load, concurrent independent/shared offsets, path escape attempts, wrong type, deterministic directory-order variation, and mapping/read failures.
* Loaded-module evidence must include module name, source image object, immutable content hash, code index/generation, and load outcome. A module supplied through `-pa`, host mount, eval injection, preloaded diagnostic image, or manual console is forbidden.
* Assert the release makes no undeclared write/open of temp/home/cwd/config/crash-dump/locale/timezone/NSS/proc/sys paths. The configured crash behavior must remain serial/evidence-only and cannot require a writable dump file.
* After each failure, descriptor/VMA/page/module-loader state and process resources must reach the declared terminal baseline; a deterministic ERTS error accompanied by a kernel leak is not a pass.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Specify executable fault injection through malformed/missing/corrupt BEAM and path cases without requiring a boot state that already assumes success.
