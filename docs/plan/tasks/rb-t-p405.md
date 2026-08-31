---
schema: "repo-plan/v1"
id: "RB-T-P405"
title: "Implement the bounded Rust ETF codec and packet framing"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P009"
  - "RB-T-P404"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-05"
x_linear_id: "ROB-743"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-743/p4-05-implement-the-bounded-rust-etf-codec-and-packet-framing"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P405: Implement the bounded Rust ETF codec and packet framing

## Goal

Create a no_std-capable Rust implementation of only the approved ETF UI protocol subset.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P404, RB-T-P009.

## Deliverables

* Implement four-byte big-endian packet framing and the fixed v1 ETF subset: allowlisted atoms, bounded integers, binaries, tuples, lists, and maps.
* Enforce frame, nesting, list, string/binary, allocation, key, atom, and integer limits before or during decode.
* Represent decoded messages as typed protocol enums/structures rather than exposing arbitrary terms to the renderer.
* Support incremental reads/writes, partial frames, multiple frames, backpressure, and deterministic encoding.

## Acceptance criteria

- [ ] Every canonical fixture round-trips or decodes to the exact typed value.
- [ ] Every malformed, truncated, oversized, over-nested, unknown-atom, duplicate/invalid-field, and trailing-data fixture fails safely.
- [ ] The decoder performs no unbounded allocation and never interns runtime-supplied atoms.
- [ ] Property/differential tests agree with Erlang encoding for the admitted subset.
- [ ] Fuzzing finds no panic, out-of-bounds access, or resource-bound bypass.

## Verification

* `just test-etf-rust`
* `just fuzz-etf-rust`
* `just protocol-conformance`

## Evidence

* Run fixtures, properties, differential checks, corpus fuzzing, and allocation-bound tests.
* Save codec feature/unsafe inventory and protocol digest.
* Verify compatibility in no_std renderer build.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Additional context
### Completion rule

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.
### Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Add compressed-term policy, atom allowlist, depth/arity/binary/integer/trailing-byte limits, allocation accounting, and differential fuzzing.
### Normative readiness correction — 2026-08-30

Enforce exactly one four-byte length prefix per direction; 64 KiB or the frozen frame limit; compressed-term rejection or pre-allocation uncompressed-size bounds; nesting, arity, binary/string, integer, atom-allowlist, trailing-byte, tag, envelope, sequence, and application-schema limits; and differential/fuzz evidence against Erlang.
