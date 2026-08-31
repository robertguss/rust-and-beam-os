---
schema: "repo-plan/v1"
id: "RB-T-P009"
title: "Specify ETF UI protocol v1 and conformance fixtures"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P002"
  - "RB-T-P001"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-09"
x_linear_id: "ROB-687"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-687/p0-09-specify-etf-ui-protocol-v1-and-conformance-fixtures"
x_labels:
  - "ready-for-agent"
---
# RB-T-P009: Specify ETF UI protocol v1 and conformance fixtures

## Goal

Define a small, versioned, bounded protocol before either endpoint depends on it.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P001, RB-T-P002.

## Deliverables

* Write `protocol/ui-etf-v1.md` covering handshake, event, snapshot, patch, acknowledgement, status, and metric envelopes.
* Fix four-byte big-endian packet framing, a 64 KiB frame cap, maximum depth/list/string limits, fixed atom allowlist, sequence rules, timestamps, and version negotiation.
* Specify button-event reliability, pointer-motion coalescing, stale-patch replacement, backpressure, disconnect, reconnect, and last-valid-model behavior.
* Generate canonical valid, boundary, malformed, oversized, unknown-version, unknown-atom, and out-of-order fixtures from Erlang's encoder.

## Acceptance criteria

- [ ] The spec contains no unbounded collection, queue, frame, atom, or nesting behavior.
- [ ] Every message documents producer, consumer, state precondition, response, and error behavior.
- [ ] Rust and Erlang can consume the same committed fixtures.
- [ ] The protocol can add an optional field without breaking a v1 peer, and a breaking change is rejected by version negotiation.

## Verification

* `just protocol-fixtures`
* `just test-protocol-elixir`
* `just protocol-lint`

## Evidence

* Run fixture generation twice and compare hashes.
* Decode all positive fixtures in Erlang and reject all negative fixtures safely.
* Review the state machine for reconnect and backpressure ambiguity.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

### Normative framing ownership

* The raw stream wire format is exactly: unsigned four-byte big-endian **payload length**, followed by one **uncompressed** ETF payload.
* On the BEAM side, `open_port({:fd, in_fd, out_fd}, [:binary, packet: 4, ...])` owns insertion/removal of that four-byte prefix. The owning Elixir process sends and receives ETF payload bytes only. It must not prepend or parse another length.
* On the Rust/raw-stream side, the codec owns the one four-byte prefix. Tests must include a double-prefix fixture that fails immediately rather than deadlocks.

### Normative ETF safety

* Pin version byte/tag subset. Reject `COMPRESSED` ETF, distribution-only/cache tags, PIDs/ports/references, funs/exports, arbitrary atoms, bitstrings outside the chosen byte-aligned subset, and every unknown tag.
* Elixir decodes only after the packet limit using `:erlang.binary_to_term(payload, [:safe])`, then applies a strict typed schema, depth, collection-count, binary/text-length, integer-range, and semantic-work budget. All protocol atoms must already exist in the release.
* Rust uses a bounded non-recursive or explicitly depth-bounded decoder with checked arithmetic and allocation-before-length guards.
* `term_to_binary/1` is not a canonical-byte guarantee. Define one canonical outbound encoding/order for protocol maps or use fixed tuples; compare semantic state separately from raw bytes.
* Specify malformed-frame recovery, EOF/partial-frame behavior, maximum frame size, maximum decode work, and whether the connection is closed on each violation.

### Required additional evidence

* Cross-language golden corpus, property round trips, differential decoding, duplicate-map-key/ordering cases, compressed bombs, declared-size overflow, truncated input at every byte, deep nesting, huge counts, unknown atoms/tags, and sustained malformed traffic.
* Prove zero atom-table growth and bounded memory/CPU for every rejected corpus class.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Freeze one framing owner, compressed-term policy, atom allowlist, depth/arity/size limits, trailing bytes, sequence/reconnect rules, and differential fixtures.
