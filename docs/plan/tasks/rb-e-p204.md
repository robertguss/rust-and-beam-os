---
schema: "repo-plan/v1"
id: "RB-E-P204"
title: "TRACKING: Complete VMA, mapping, protection, and teardown semantics"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P204A"
  - "RB-T-P204C"
  - "RB-T-P204B"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-04"
x_linear_id: "ROB-713"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-713/p2-04-tracking-complete-vma-mapping-protection-and-teardown-semantics"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P204: TRACKING: Complete VMA, mapping, protection, and teardown semantics

## Goal

Provide the precise virtual-memory behavior needed by static musl and non-JIT ERTS while preserving W^X and process accounting.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P201, RB-T-P202.

## Deliverables

* Add per-process VM-area tracking with checked split/merge, overlap, ownership, and resource-limit rules.
* Implement the admitted anonymous and read-only file mapping modes for `brk`, `mmap`, `mprotect`, `munmap`, and selected `madvise`.
* Define page rounding, hint/fixed-address behavior, zero-fill, partial unmap/protect, guard mappings, failure atomicity, and error precedence.
* Instrument reserved versus committed pages and high-water use per process.

## Acceptance criteria

- [ ] Reference C probes pass for heap growth, anonymous mappings, guards, protection transitions, partial operations, holes, exhaustion, and reuse.
- [ ] Writable-plus-executable mappings are rejected in the non-JIT profile.
- [ ] Failed operations leave the previous address-space state unchanged.
- [ ] Every mapping is charged to one process and released exactly once on unmap/exit.
- [ ] The final ERTS reservation pattern can fit the declared guest/userland budgets or raises an explicit gate blocker.

## Verification

* `just test-beam-vm`
* `just stress-beam-vm`
* `just inspect-process-mappings`

## Evidence

* Run a software-model property suite and guest stress probes.
* Differentially test admitted cases against AArch64 Linux.
* Inspect page tables and VMA accounting after failures and exit.

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

### Scope and layering

* This issue owns the **single-address-space operation semantics and VMA model**. RB-T-P205C owns cross-CPU shootdown, concurrent mutation, and safe remote reclamation before the behavior is Gate-2 complete.
* All mapping operations must call RB-T-P114's common page-table/cache/TLB publication API. No compatibility syscall may manipulate page tables, barriers, or TLBI directly.
* The non-JIT profile rejects every executable writable transition and every writable/executable alias. Anonymous and immutable-file executable mappings are admitted only if the exact ERTS artifact requires them and are published through the executable-cache path.

### Exact contract

* Derive and admit only observed flags/protections/advice. Define `MAP_FIXED`/`MAP_FIXED_NOREPLACE` behavior only if observed; never approximate an unknown fixed-map request.
* Define overflow-safe page rounding, address hints, alignment, zero length, file offset, anonymous zero-fill, immutable file bounds, partial unmap/protect, holes, guard pages, VMA split/merge, address selection, process limits, `brk` collision, and errno precedence.
* File-backed mappings come only from immutable image objects; dirty shared writable file mappings, writeback, truncation races, and general page cache are forbidden.
* Every operation is transaction-like: validate and reserve all metadata/pages first or specify exact partial semantics; injected failure at any allocation/copy/file-read/page-table point cannot leave an undocumented half-applied VMA.
* Mapping generations must flow into futex keys, poll/user-copy lifetime checks, signal frames, and address-space reuse so unmap/remap cannot create ABA.

### Required additional evidence

* Reference-model randomized operation sequences; VMA metadata exhaustion; every split/merge edge; fixed/hint collisions; `brk`/`mmap` interaction; immutable-file EOF/offset cases; W^X/alias attempts; failure injection at each commit step; unmap-vs-futex/signal/user-copy races; and RB-T-P205C remote-stale-translation canaries.
* Measure ERTS reservation/commit behavior separately. Large reservations are not charged as committed pages, but both address-space and physical-memory budgets remain explicit.
### Implementation-readiness disposition — 2026-08-30

**Action:** SPLIT/TRACK

Split VMA/brk/anonymous mapping, protect/unmap/splitting/rollback, and only admitted file mappings. Block SMP completion on RB-T-P205C.
