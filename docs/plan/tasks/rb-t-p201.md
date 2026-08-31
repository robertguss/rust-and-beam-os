---
schema: "repo-plan/v1"
id: "RB-T-P201"
title: "Create the ERTS compatibility personality and executable syscall contract"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P113"
  - "RB-T-P008"
  - "RB-G-GATE1"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-01"
x_linear_id: "ROB-712"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-712/p2-01-create-the-erts-compatibility-personality-and-executable-syscall"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P201: Create the ERTS compatibility personality and executable syscall contract

## Goal

Create a narrow AArch64 Linux syscall adapter whose admitted behavior is generated and tested from `beam-host.yaml`.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-G-GATE1, RB-T-P008.

## Deliverables

* Add `kernel/src/abi/linux_aarch64` as an explicit compatibility adapter over native kernel objects; select it only for processes whose image manifest names the ERTS personality.
* Generate syscall numbers, admitted operation/flag tables, trace names, and test coverage metadata from the validated contract where practical.
* Return `ENOSYS` plus a structured high-priority trace for every unknown call; reject unsupported flags rather than silently ignoring them.
* Create a contract-coverage report linking each admitted behavior to conformance tests and exact reference traces.

## Acceptance criteria

- [ ] A native Rust process cannot accidentally invoke or receive the compatibility personality.
- [ ] Every dispatched syscall and admitted flag exists in the pinned contract.
- [ ] Unknown numbers, unknown operation modes, and unsupported flags fail deterministically and appear in evidence.
- [ ] The generated coverage report fails CI for an untested contract entry or implemented-but-undocumented behavior.

## Verification

* `just beam-abi-generate`
* `just test-beam-abi-dispatch`
* `just beam-abi-coverage`

## Evidence

* Run dispatch-table completeness and negative tests.
* Replay representative reference calls through a host-side model adapter.
* Save adapter/contract hashes and the compatibility-boundary ADR.

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

### Personality isolation and dispatch

* Bind the compatibility personality only from the immutable, hashed process manifest at image construction/launch. EL0 cannot select, switch, inherit unexpectedly, or spoof the personality through a syscall or mutable field.
* Decode the exact AArch64 syscall ABI at the SVC boundary with checked register/size conversions. Native Rust ABI calls and Linux-shaped numbers use separate dispatch tables and types even if an operation ultimately reaches the same native object.
* Generate a deterministic schema-versioned artifact containing syscall numbers, operation/flag masks, argument shapes, size/version expectations, semantic family, allowed process type, errors, trace identity, and required tests. Hand-written dispatch entries are forbidden unless represented back in the contract.
* Validate unknown number, known number with unsupported operation, unknown flags, invalid structure size/version, and bad pointer as distinct contract cases with the correct error precedence. Do not return `ENOSYS` for every malformed form merely because it is convenient.
* Compatibility adapters translate into typed native operations; they cannot expose raw kernel pointers, native handles, internal error enums, architecture-specific page-table operations, or a general syscall-registration escape hatch.

### Evidence and abuse bounds

* Every admitted argument that references user memory uses the central bounded copy API with explicit copy-in/copy-out/partial-result rules. No implementation may dereference a user pointer after dropping the lifetime/generation protection that validated it.
* Unknown/unsupported events remain visible but traces are rate/volume bounded; preserve aggregate counts and first/last exemplars so an EL0 loop cannot exhaust evidence storage or hide a novel call.
* Generate four coverage views: contract→dispatch, dispatch→implementation, implementation→tests, and observed trace→contract. All must be bijective for admitted behavior; unused support is removed or separately justified.
* Mutation canaries must delete/change a syscall number, operation flag, errno rule, structure size, and personality binding and prove the appropriate test/generator check fails.
* The compatibility boundary ADR must quantify both breadth and semantic depth; syscall count alone is not evidence that the adapter is small.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Keep Linux-shaped ABI isolated to ERTS; generate dispatch/tests from contract; fail unsupported calls/flags before side effects; include coupled state machines.
