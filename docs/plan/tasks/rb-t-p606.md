---
schema: "repo-plan/v1"
id: "RB-T-P606"
title: "Run AI exercise A: add a high-level scheduler-utilization card"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P601"
  - "RB-T-P508"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-06"
x_linear_id: "ROB-768"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-768/p6-06-run-ai-exercise-a-add-a-high-level-scheduler-utilization-card"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P606: Run AI exercise A: add a high-level scheduler-utilization card

## Goal

Measure whether ordinary feature work is productive, understandable, and mostly confined to Elixir/UI layers.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P508.

## Deliverables

* Give a fresh AI agent only the project skill, relevant repository task file, architecture document, repository, and verification commands.
* Add a scheduler-utilization metric using an already available BEAM metric, expose it through the existing typed protocol, and render a new bounded card.
* Require tests/fixtures before implementation, a small reviewable change, protocol compatibility, and no kernel/unsafe change.
* Measure elapsed/active agent time, build/test feedback time, files/layers touched, tokens if available, retries, defects, human corrections, and explanation quality.

## Acceptance criteria

- [ ] The card reports a defined metric with unit, sample time, stale/unavailable state, and bounded sampling.
- [ ] No kernel, compatibility ABI, unsafe Rust, or capability change is needed.
- [ ] Protocol v1 compatibility and canonical fixtures remain valid.
- [ ] All automated/guest/UI tests pass and the builder can explain the change without relying on agent prose.
- [ ] The exercise report distinguishes tool friction from architectural friction.

## Verification

* `just exercise-a`
* `just test`
* `just evidence-check --exercise a`

## Evidence

* Run existing suites plus targeted metric/card tests and a guest screenshot.
* Review the diff and agent transcript/task receipt.
* Publish measured productivity and comprehension results.

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

Pin exact OTP metric/API/flags, scheduler classes, sampling formula and overhead; run in isolated branch/image.
### Normative readiness correction — 2026-08-30

This exercise runs in an isolated branch/worktree from the RB-T-P601 canonical commit and produces an independent image/build ID. It does not mutate canonical qualification. Retaining its change requires an explicit merge, a newly frozen canonical image, RB-T-P605 reproducibility/SBOM/license rerun, and every affected qualification rerun.
