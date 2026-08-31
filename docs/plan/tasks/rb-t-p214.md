---
schema: "repo-plan/v1"
id: "RB-T-P214"
title: "Audit and freeze the bounded BEAM host contract revision 2"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P212"
  - "RB-T-P213"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-14"
x_linear_id: "ROB-720"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-720/p2-14-audit-and-freeze-the-bounded-beam-host-contract-revision-2"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P214: Audit and freeze the bounded BEAM host contract revision 2

## Goal

Confirm that the implemented compatibility surface is exact, tested, and still materially smaller than a general Linux/POSIX OS.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P212, RB-T-P213.

## Deliverables

* Diff implemented syscalls, operations, flags, errors, and blocking semantics against `beam-host.yaml` and the target reference trace.
* Classify every implementation as exact workload requirement, intentionally conservative semantic support, or accidental scope expansion.
* Audit thread/signal/VM semantic depth, unsafe code, denial-of-service bounds, and native-object translations.
* Update the contract, conformance map, security boundary, risk register, and evidence index; remove unused behaviors.

## Acceptance criteria

- [ ] Zero implemented-but-undocumented and zero documented-but-unimplemented contract entries remain.
- [ ] Zero unknown syscalls appear in the complete reference workload and conformance run.
- [ ] General process creation, networking, dynamic loading, mutable filesystem, and broad device/proc behavior remain absent.
- [ ] Every unavoidable semantic expansion has a written rationale and tests.
- [ ] A fresh reviewer can explain the compatibility boundary without reading kernel internals.

## Verification

* `just beam-host-audit`
* `just beam-abi-coverage`
* `just evidence-check --phase 2`

## Evidence

* Run generated contract/implementation/test diffs.
* Perform a fresh-session breadth and semantics audit.
* Publish the revision-2 contract digest and Phase 2 evidence index.

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

The revision-2 audit must prove **semantic boundedness**, not celebrate a small syscall count.

* Diff the pinned target workload trace, contract schema, generated dispatch, reachable implementation, conformance inventory/results, stress traces, and actual ERTS build flags/artifact. Each discrepancy is blocking until removed or explicitly approved.
* Report breadth by syscall, operation, flag, structure version, descriptor/object class, file/path capability, and platform query. Report depth by every state machine/race obligation for VM, SMP/TLB, thread lifecycle, futex/robust cleanup, signal frame/return/restart, stream/poll, timer, entropy, and cleanup.
* Prove the personality is reachable only by the immutable ERTS process manifest. Search binaries/source/config for dormant broad Linux/POSIX implementations, hidden feature flags, debug fallbacks, host passthroughs, generic syscall registration, shell/process spawning, writable paths, sockets, dynamic loading, JIT, and permissive unknown-flag handling.
* Reconcile all copies of platform identity and ABI state: ELF type, page size, auxv/HWCAPs, CPU/atomics, TLS, FP/SIMD, signal frame, vCPU count/affinity, cache lines, clock source, entropy mode, limits, release paths, and descriptor assignments.
* Identify every deliberately conservative semantic expansion. It remains only if its security/complexity cost is bounded, tests are complete, and removing it would harm correctness or maintainability more than keeping it.
* Treat every workaround—especially spin/yield, relaxed blocking, ignored flags, broadened files, artificial readiness, timeout retries, or alternate ERTS flags—as a first-class contract deviation. It cannot be hidden as an implementation detail.
* Freeze hashes for contract, generated code, implementation inventory, target artifact, release image, platform manifest, conformance suite/results, qualification manifest/results, ADRs, and toolchain.
* Have a fresh reviewer attempt to add a prohibited capability through each boundary and verify generation/CI/gate checks reject it.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Define boundedness by semantic state-machine depth, code/test/unsafe surface, and excluded families—not merely syscall count.
