---
schema: "repo-plan/v1"
id: "RB-T-P403"
title: "Implement final runtime_lab supervision and supervisor-resilient in-memory demo state"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P402"
  - "RB-T-P002"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-03"
x_linear_id: "ROB-739"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-739/p4-03-implement-final-runtime-lab-supervision-and-supervisor-resilient"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P403: Implement final runtime_lab supervision and supervisor-resilient in-memory demo state

## Goal

Create the exact Elixir behavior that will later drive the GUI and visibly demonstrate OTP fault recovery.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P402, RB-T-P002.

## Deliverables

* Implement or port the durable-state process, crashable feature worker, UI coordinator, metric sampler, and dynamic supervisor/supervisor structure into the guest release.
* Define initial state, counter transitions, worker generation, restart count/reason, stress state, connection state, and restart-intensity escalation.
* Keep durable view state outside the intentionally crashing worker and define what resets only when the whole release restarts.
* Emit semantic lifecycle/status events independent of Logger prose.

## Acceptance criteria

- [ ] Counter and feature state transitions are deterministic and covered by pure/stateful tests.
- [ ] A worker crash creates a new PID/generation and increments restart evidence without losing durable state.
- [ ] A deliberate crash storm escalates through the declared supervisor strategy and stops churn.
- [ ] No GUI, kernel, or renderer assumption is embedded in the domain state beyond the versioned protocol model.

## Verification

* `cd beam/runtime_lab && mix test`
* `just test-runtime-lab-guest`

## Evidence

* Run unit, supervision, property, crash-once, crash-storm, and release-restart tests on Linux and in the guest.
* Save supervision-tree and state-ownership diagrams.
* Compare lifecycle events across reference and guest runs.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Additional context
### Completion rule

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.
### Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.
### Readiness-audit correction — 2026-08-30

### Correct persistence terminology and ownership

* Replace every use of “durable state” with **restart-persistent in-memory state across the intentionally crashing feature worker**. There is no writable persistence. State is expected to reset on application restart, BEAM VM restart/exit, or whole-system reboot unless an individual field explicitly has a different tested owner.
* Publish an ownership table for every field: authoritative process/module, initial value, transition function, whether it survives feature-worker restart, transport/protocol reset, coordinator restart if allowed, application restart, BEAM VM restart, native-service restart, and system reboot.
* The feature worker cannot own any value claimed to survive its crash. The stable state owner must not link its own fate to the intentionally crashing worker in a way that loses state, and stale worker messages are rejected by worker-generation/action identity.
* Define one supervision tree and strategy with child order, restart type, intensity/max-seconds, shutdown timeout, significant-child behavior if used, and expected escalation. A crash storm must not accidentally restart or retain children in an implementation-dependent order.

### Deterministic domain and lifecycle semantics

* Specify the state machine independently of PIDs and wall-clock strings: counter range/overflow, feature status, worker generation, accepted/applied/rejected action IDs, restart count and normalized reason category, stress state, transport/session state, model revision, and terminal application state.
* PIDs may be diagnostic evidence but are not protocol identity. Use monotonic bounded generation/session/action identifiers with explicit overflow behavior; a reused PID or wrapped counter cannot make a stale result current.
* Separate semantic lifecycle events from Logger and OTP report formatting. Every event has schema version, process/worker generation, application/session identity, cause category, state revision, and correlation/action ID where applicable.
* A crash command has one defined point after which the requested worker is guaranteed to fail. Duplicate/stale crash commands, crash while already restarting, coordinator timeout, restart failure, and escalation race have explicit outcomes; no exactly-once side-effect claim is made across application/VM restart.
* The stable owner, coordinator, transport owner, metric sampler, feature worker, and any dynamic children have bounded mailboxes/work queues or admission/credit policies. Metrics and Logger traffic cannot starve control/lifecycle messages.
* Define normal shutdown versus crash/escalation cleanup, including timers/monitors/links/ETS tables/process dictionary/binaries and pending protocol acknowledgements.

### Required additional evidence

* Pure model/property tests and OTP integration tests cover every legal transition, duplicate/stale action, generation/revision overflow boundary, worker crash at every state mutation boundary, owner/coordinator/transport failure, restart intensity at boundary times, shutdown timeout, and application restart.
* Run the same semantic trace on reference Linux and the guest, comparing normalized events/state—not PIDs, timestamps, scheduling order, or Logger text.
* Explicitly test and document expected state after: one worker crash; 1,000 sequential worker crashes; logical protocol reset; coordinator restart if supported; stable owner failure; supervisor escalation; application restart; BEAM VM restart; native process exit; and full reboot.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Rename to supervisor-resilient in-memory state; document and test reset on BEAM/OS restart.
### Normative readiness correction — 2026-08-30

The state is supervisor-resilient in-memory state. It survives the intentional worker restart and resets on release, BEAM, or OS restart. Add acceptance evidence for both preservation and the intentional reset boundary.
