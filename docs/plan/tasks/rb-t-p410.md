---
schema: "repo-plan/v1"
id: "RB-T-P410"
title: "Qualify 1,000 supervised crashes and restart-intensity escalation"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P400"
  - "RB-T-P409"
  - "RB-T-P403"
  - "RB-T-P407"
  - "RB-T-P408"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-10"
x_linear_id: "ROB-744"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-744/p4-10-qualify-1000-supervised-crashes-and-restart-intensity-escalation"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P410: Qualify 1,000 supervised crashes and restart-intensity escalation

## Goal

Prove that OTP feature recovery is visible across the Rust boundary and does not destabilize ERTS, IPC, or kernel resources.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P403, RB-T-P407, RB-T-P408, RB-T-P409.

## Deliverables

* Trigger 1,000 sequential intentional worker crashes through the semantic event path, waiting for a new generation/snapshot each cycle.
* Verify durable state, restart count/reason, PID/generation changes, connection state, and acknowledgements.
* Run a separate crash storm that crosses restart intensity and assert the declared supervisor escalation and UI/status outcome.
* Correlate OTP lifecycle events with port, process, queue, memory, and kernel counters.

## Acceptance criteria

- [ ] All 1,000 cycles produce exactly one observed new worker generation and preserve declared durable state.
- [ ] No ERTS, Rust service, or kernel crash occurs; no monotonic resource leak remains.
- [ ] The crash storm stops churn and exposes the specified terminal/degraded state.
- [ ] A UI/protocol consumer can distinguish worker restart, whole-application restart, and BEAM disconnect.
- [ ] Evidence contains no reliance on parsing human Logger strings.

## Verification

* `just qualify-supervision`
* `just analyze-supervision`

## Evidence

* Run normal, crash-cycle, crash-storm, BEAM-exit, and service-exit cases.
* Analyze resource slopes and sequence conservation.
* Save the complete supervised-recovery qualification report.

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

**Action:** KEEP

Good. Distinguish feature restart, supervisor escalation, release exit, and state reset.
