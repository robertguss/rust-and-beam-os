---
schema: "repo-plan/v1"
id: "RB-T-P607"
title: "Run AI exercise B: add a cross-boundary page-pressure capability"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P508"
  - "RB-T-P601"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-07"
x_linear_id: "ROB-771"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-771/p6-07-run-ai-exercise-b-add-a-cross-boundary-page-pressure-capability"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P607: Run AI exercise B: add a cross-boundary page-pressure capability

## Goal

Measure the real cost and safety of one intentionally bounded kernel→Rust→Elixir→UI capability change.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P508.

## Deliverables

* Give a fresh AI agent the approved task packet and require a design/policy explanation before edits.
* Define a read-only page-pressure metric with exact semantics, unit, sampling, permission, stale/error behavior, and privacy/security boundary.
* Add the minimal native capability/ABI, manifest right, renderer service exposure, protocol field, Elixir state, and UI card needed.
* Add negative permission, malformed/stale, sampling-bound, ABI/protocol compatibility, and end-to-end tests.

## Acceptance criteria

- [ ] Only the renderer with the declared right can read the metric; denial tests pass for BEAM and unrelated native processes.
- [ ] ABI/capability and protocol changes are explicit, versioned, bounded, and documented.
- [ ] Unsafe code remains confined to the existing audited kernel mechanism or receives an explicit new proof obligation.
- [ ] The UI value correlates with kernel telemetry.
- [ ] The result is materially more understandable than embedding feature policy in the kernel.

## Verification

* `just exercise-b`
* `just test-page-pressure-capability`
* `just evidence-check --exercise b`

## Evidence

* Run unit, ABI, capability-denial, protocol, guest, and screenshot tests.
* Review all cross-layer diff and task evidence.
* Publish layers/files/time/defects/human-corrections and comprehension results.

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

**Action:** AMEND

Run in isolated branch/image; define exact metric formula and capability; retained changes force new canonical qualification.
### Normative readiness correction — 2026-08-30

This exercise runs in an isolated branch/worktree from the RB-T-P601 canonical commit and produces an independent image/build ID. It does not mutate canonical qualification. Retaining its change requires an explicit merge, a newly frozen canonical image, RB-T-P605 reproducibility/SBOM/license rerun, and every affected qualification rerun.
