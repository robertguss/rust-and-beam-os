---
schema: "repo-plan/v1"
id: "RB-T-P604"
title: "Qualify 10,000 scripted UI actions with complete sequence accounting"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P601"
  - "RB-T-P602"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-04"
x_linear_id: "ROB-765"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-765/p6-04-qualify-10000-scripted-ui-actions-with-complete-sequence"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P604: Qualify 10,000 scripted UI actions with complete sequence accounting

## Goal

Prove that interactive events remain correct and bounded across load, coalescing, crashes, and reconnects.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P602.

## Deliverables

* Generate a deterministic mixture of counter, stress, Crash Feature, allowed motion, and state-dependent actions totaling 10,000 semantic button actions plus separately counted motion events.
* Record input, semantic event, sequence, send/queue status, Elixir acceptance/rejection, state transition, response, render, and final visible state.
* Inject documented worker crashes, protocol saturation, BEAM disconnect/reconnect, disabled actions, and boundary timing.
* Reconcile every non-motion action into one explicit terminal outcome.

## Acceptance criteria

- [ ] All 10,000 button actions are accounted for; none are silently dropped or duplicated.
- [ ] Final Elixir authoritative state equals the renderer's applied state after resynchronization.
- [ ] Only pointer motion is coalesced according to policy and its counts reconcile.
- [ ] Injected disconnects/failures produce specified unresolved/failed/recovered outcomes.
- [ ] Latency/error distributions and queue high-water marks stay within frozen criteria.

## Verification

* `just qualify-ui-actions`
* `just reconcile-ui-actions`

## Evidence

* Run on the frozen runner profiles required by the qualification contract.
* Replay boundary and failure positions from the action ledger.
* Publish sequence-conservation and final-state hashes.

## Out of scope

* New kernel/runtime/UI features not required by qualification.
* JIT, second hardware target, networking, persistent writable storage, update slots, phone drivers, or production security.
* Hiding failed runs, retroactively weakening thresholds, or presenting the emulator POC as a daily-driver phone OS.

## Additional context
### Completion rule

Done requires the frozen qualification contract, exact image/build provenance, raw and summarized evidence, and honest classification of every failure or exception.
### Learning checkpoint

Explain what the evidence proves, what it does not prove, one source of measurement bias, and the strongest fact that could justify stopping or pivoting.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Terminal outcomes must use the F-16 definition and event metric must use present completion.
