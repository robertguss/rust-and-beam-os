---
schema: "repo-plan/v1"
id: "RB-T-P400"
title: "Freeze IPC, protocol, overload, and supervised-recovery qualification manifests"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P408"
  - "RB-T-P016"
  - "RB-T-P405"
  - "RB-T-P406"
  - "RB-T-P407"
  - "RB-T-P403"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-00"
x_linear_id: "ROB-799"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-799/p4-00-freeze-ipc-protocol-overload-and-supervised-recovery"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P400: Freeze IPC, protocol, overload, and supervised-recovery qualification manifests

## Goal

Pre-register the exact one-million-message, malformed-input, overload, disconnect, logical-resynchronization, and 1,000-worker-crash campaigns before official M4 results are inspected.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-T-P403, RB-T-P405, RB-T-P406, RB-T-P407, RB-T-P408, RB-T-P016.

Blocks: RB-T-P409, RB-T-P410.

## Deliverables

* Freeze exact build/image/platform/contract/protocol/release/native-service hashes, guest/runner profile, production entropy, vCPU/RAM, descriptor assignments, stream capacities, port busy limits, BEAM mailbox policy, Rust queue limits, frame/schema limits, watchdogs, host-resource policy, and artifact capacity.
* Define the M4 native qualification process separately from the later renderer. It receives only log/clock/UI-stream capabilities; display, pointer, and asset capabilities are absent. M5 must rerun boundary tests after the real renderer replaces it.
* Define exactly one wire frame: unsigned four-byte big-endian ETF-payload length plus one uncompressed approved ETF payload. ERTS `{packet,4}` owns the prefix on the BEAM side; the raw Rust stream codec owns it on the Rust side.
* Freeze valid message mix, directions, payload sizes, concurrency, burst/idle phases, sequence/session/revision ranges, operation and byte floors, acknowledgements, snapshots/patches, reconnect/resnapshot cases, and deterministic seeds for one million messages.
* Freeze the complete malformed corpus and mutation schedule: every truncated prefix/payload boundary, declared-size overflow, over-limit length, compressed term, unknown/forbidden ETF tag or atom, nesting/count/size/work limit, schema/type/range error, duplicate field/key policy, trailing data, handshake/sequence/revision/session error, and double framing.
* Predeclare all queue layers and hard/high/low bounds: kernel inbound/outbound stream, ERTS fd-driver output queue, ERTS port message queue, BEAM transport/coordinator work, Rust byte/frame/decode/model/event queue, telemetry, and trace buffers.
* Define progress and terminal-outcome oracles for accepted user events, protocol control messages, frames, bytes, sequence numbers, acknowledgements, snapshots/patches, reconnect/resnapshot attempts, failures, coalesces/replacements, and closures. Every accepted non-coalescible event reaches one explicit terminal outcome.
* Freeze the supervision campaign: exact initial state, crash command/action ID, expected worker generation transition, restart count/reason, state that survives only the worker restart, quiescent checkpoint, restart-intensity window/threshold, escalation tree, terminal state, and operation floor.
* Name lifecycle limits accurately. The POC supports worker-process restart and logical protocol reset/resnapshot while both OS processes and fixed streams remain alive. Unexpected fd-port owner, BEAM VM/application, native service/renderer, or kernel-stream loss is terminal until full system reboot unless a later explicitly gated process-relaunch/rebinding feature is added.
* Classify resources as exact-conservation or bounded-retention; freeze warm-up, sample cadence, absolute caps, slope/plateau rule, progress floor, and invalid-run conditions before official campaigns.
* Freeze failure taxonomy and no-retry policy: guest invariant/protocol failure, expected rejected input, progress failure, resource failure, trace/evidence loss, harness error, runner/QEMU invalidity, and host interruption remain distinct.
* Generate hashed machine-readable qualification manifests and independent analyzers; commit hashes before official runs.

## Acceptance criteria

- [ ] A fresh agent can execute and judge RB-T-P409/RB-T-P410 without inventing a message mix, threshold, queue bound, recovery rule, persistence claim, or runner substitution.
- [ ] Every byte/frame/message/event/action/acknowledgement/sequence/revision and resource has an accounting equation or explicit allowed coalescing/replacement rule.
- [ ] Queue saturation cannot be hidden as low throughput; minimum progress and scheduler-responsiveness floors are specified.
- [ ] The malformed corpus covers all framing, ETF, schema, state-machine, and resource-work boundaries, including compressed ETF and accidental double prefixing.
- [ ] Worker restart, protocol session reset, port closure, BEAM/application exit, native-service exit, and whole-system reboot have distinct expected state and recovery semantics.
- [ ] “Restart-persistent” never means durable across application, BEAM VM, or system restart; no writable persistence exists.
- [ ] Missing samples, trace loss, counter reset, artifact truncation, manifest drift, deterministic production entropy, insufficient operations, host/QEMU failure, or automatic retry invalidates a run.
- [ ] Deliberate corruption, loss, duplicate, queue saturation, scheduler stall, resource leak, false acknowledgement, and restart-generation failure canaries are detected in dry runs.

## Verification

* `just build-m4-qualification-manifests`
* `just validate-m4-qualification-manifests`
* `just dry-run-m4-qualification`
* `just test-m4-oracles`

## Evidence

* Reduced-duration dry runs for valid traffic, each malformed class, each queue saturation point, closure at every state, logical resnapshot, worker crash, crash storm, and every invalid-run class.
* Independent review of manifests/analyzers and deliberate mutation of their accounting equations.

## Out of scope

* Live relaunch/rebinding of a dead BEAM VM, fd-port owner, native OS process, or renderer; writable persistence; GUI pixels; or selecting thresholds after results.

## Additional context
### Why this is required

A message count, crash count, latency percentile, or apparently flat memory graph is not an auditable result unless message mix, concurrency, queue bounds, progress floors, failure semantics, runner validity, and resource analysis are fixed in advance. This phase also must not imply live OS-process restart/reconnection that the POC kernel has not implemented.
### Completion rule

Done means M4 qualification is deterministic, bounded, independently judged, and honest about which failures can be recovered without a system reboot.
### Learning checkpoint

Explain every queue and ownership boundary, the one-prefix rule, event terminal-outcome accounting, which state survives a worker crash, and why fixed boot-time streams do not automatically provide live OS-process reconnection.
