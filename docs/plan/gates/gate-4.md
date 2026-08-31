---
id: "GATE-4"
linear_id: "ROB-737"
linear_url: "https://linear.app/robert-guss/issue/ROB-737/gate-4-decide-whether-the-elixir-release-and-rust-ipc-boundary-are"
title: "Decide whether the Elixir release and Rust IPC boundary are ready for GUI work"
milestone: "M4"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P4-10"
  - "P4-09"
  - "P4-08"
  - "P4-05"
  - "P4-07"
  - "P4-01"
  - "P4-06"
  - "P4-03"
  - "P4-04"
  - "P4-02"
blocks:
  - "P5-01a"
  - "P5-02"
---
# GATE-4: Decide whether the Elixir release and Rust IPC boundary are ready for GUI work

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Approve the application personality and fault boundary only after the final guest path survives load, malformed input, disconnects, and supervised failure.

## Locked context

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

## What to build

* Review release provenance, supervision semantics, cross-ABI streams, ETF safety, protocol state model, backpressure, million-message run, and 1,000-crash result.
* Score H3 interoperability and update H4 fault containment before visual evidence.
* Confirm the GUI can remain a renderer of explicit state rather than acquiring feature policy.
* Record Continue, Repair within M4, redesign protocol boundary, Narrow, Pivot, or Stop.

## Acceptance criteria

- [ ] Continue requires a genuine guest Mix release, standard fd port, bounded protocol/queues, no unsafe NIF, no corruption/deadlock, and correct supervised recovery.
- [ ] Every known disconnect and overload mode has an explicit renderer-visible state.
- [ ] No protocol ambiguity is deferred to GUI implementation.
- [ ] The user approves the decision; M5 remains blocked until then.

## Required tests and evidence

* Conduct a fresh-session protocol/fault review using only repository plan content and evidence.
* Publish gate ADR/status update and next issue.
* Confirm downstream dependency links.

## Verification commands

* `just gate-report 4`
* `just evidence-check --phase 4`

## Dependencies

Blocked by: P4-01, P4-02, P4-03, P4-04, P4-05, P4-06, P4-07, P4-08, P4-09, P4-10.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Completion rule

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.

## Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Require corrected fd-driver policy, protocol bounds, terminal action ledger, and objective leak/backpressure evidence.
