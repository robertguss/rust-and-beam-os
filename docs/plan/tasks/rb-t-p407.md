---
schema: "repo-plan/v1"
id: "RB-T-P407"
title: "Implement protocol handshake, sequencing, snapshots, patches, events, and metrics"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P406"
  - "RB-T-P405"
  - "RB-T-P403"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-07"
x_linear_id: "ROB-745"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-745/p4-07-implement-protocol-handshake-sequencing-snapshots-patches-events"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P407: Implement protocol handshake, sequencing, snapshots, patches, events, and metrics

## Goal

Turn the byte channel into a deterministic, versioned application boundary shared by Rust and Elixir.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P403, RB-T-P405, RB-T-P406.

## Deliverables

* Implement connection state machines on both sides for hello/version/capability negotiation, initial snapshot, incremental patch, event, acknowledgement, status, and metric envelopes.
* Define source-of-truth ownership: Elixir owns application view state; Rust owns local shell/connection state and last valid applied model.
* Enforce monotonic sequences, duplicate/out-of-order handling, snapshot resynchronization, unknown optional fields, and incompatible-version rejection.
* Generate state-machine tests from shared transition tables/fixtures where possible.

## Acceptance criteria

- [ ] Both sides reach Ready only after compatible handshake and initial snapshot.
- [ ] Duplicate, missing, stale, out-of-order, and future-version messages produce exactly the specified recovery/error action.
- [ ] Semantic button events are acknowledged exactly according to protocol—not falsely claimed as exactly-once side effects.
- [ ] Snapshots and patches converge to the same view model in property tests.
- [ ] Metrics/status cannot mutate application state.

## Verification

* `just test-ui-protocol-state`
* `just test-ui-protocol-guest`

## Evidence

* Run model/state-machine tests against both endpoints.
* Inject every invalid transition and sequence class in the guest.
* Save transition traces and protocol-version report.

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

Define current-session sequence semantics, terminal action outcomes, application-state/native-telemetry namespaces, and reconnection wrap/reset.
### Normative readiness correction — 2026-08-30

After bounded ETF decoding, validate canonical protocol envelope and application schema. An accepted action is durably admitted into the bounded Elixir transition path for the current session and receives exactly one terminal result: applied, rejected, failed, or unresolved-by-disconnect. Freeze sequence wrap and reconnect semantics.
