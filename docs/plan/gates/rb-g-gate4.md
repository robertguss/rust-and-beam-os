---
schema: "repo-plan/v1"
id: "RB-G-GATE4"
title: "Decide whether the Elixir release and Rust IPC boundary are ready for GUI work"
type: "gate"
state: "open"
priority: "P1"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P410"
  - "RB-T-P409"
  - "RB-T-P408"
  - "RB-T-P405"
  - "RB-T-P407"
  - "RB-T-P401"
  - "RB-T-P406"
  - "RB-T-P403"
  - "RB-T-P404"
  - "RB-T-P402"
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
x_legacy_id: "GATE-4"
x_linear_id: "ROB-737"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-737/gate-4-decide-whether-the-elixir-release-and-rust-ipc-boundary-are"
x_labels:
  - "ready-for-human"
---
# RB-G-GATE4: Decide whether the Elixir release and Rust IPC boundary are ready for GUI work

## Decision

[Architecture & Validation Plan](<../architecture.md>)

Approve the application personality and fault boundary only after the final guest path survives load, malformed input, disconnects, and supervised failure.

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P401, RB-T-P402, RB-T-P403, RB-T-P404, RB-T-P405, RB-T-P406, RB-T-P407, RB-T-P408, RB-T-P409, RB-T-P410.

## Required evidence

* Conduct a fresh-session protocol/fault review using only repository plan content and evidence.
* Publish gate ADR/status update and next issue.
* Confirm downstream dependency links.

## Acceptance criteria

- [ ] Continue requires a genuine guest Mix release, standard fd port, bounded protocol/queues, no unsafe NIF, no corruption/deadlock, and correct supervised recovery.
- [ ] Every known disconnect and overload mode has an explicit renderer-visible state.
- [ ] No protocol ambiguity is deferred to GUI implementation.
- [ ] The user approves the decision; M5 remains blocked until then.

## Decision record

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Additional context
### What to build

* Review release provenance, supervision semantics, cross-ABI streams, ETF safety, protocol state model, backpressure, million-message run, and 1,000-crash result.
* Score H3 interoperability and update H4 fault containment before visual evidence.
* Confirm the GUI can remain a renderer of explicit state rather than acquiring feature policy.
* Record Continue, Repair within M4, redesign protocol boundary, Narrow, Pivot, or Stop.
### Verification commands

* `just gate-report 4`
* `just evidence-check --phase 4`
### Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.
### Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Require corrected fd-driver policy, protocol bounds, terminal action ledger, and objective leak/backpressure evidence.
