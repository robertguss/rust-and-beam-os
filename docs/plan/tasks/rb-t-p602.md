---
schema: "repo-plan/v1"
id: "RB-T-P602"
title: "Qualify 100 clean boots of the complete image"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P601"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-02"
x_linear_id: "ROB-764"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-764/p6-02-qualify-100-clean-boots-of-the-complete-image"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P602: Qualify 100 clean boots of the complete image

## Goal

Prove repeatable end-to-end boot from custom kernel through Mix release, renderer readiness, and controlled shutdown.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601.

## Deliverables

* Automate 100 complete boots of the final image using the frozen headless runner profile.
* Require milestones for kernel, devices, renderer, ERTS, Elixir application, protocol Ready, canonical view, scripted action, and clean shutdown.
* Track duration, pages, tasks, descriptors/handles, ports, queues, unknown calls, faults, trace loss, and cleanup baseline.
* Preserve first-failure evidence and prohibit blind automatic retries from converting failure to pass.

## Acceptance criteria

- [ ] All 100 boots reach Ready, complete the canonical action, and shut down with expected sentinels.
- [ ] Zero hang, kernel panic, ERTS abort, renderer crash, unknown syscall, unclassified fault, or cleanup discrepancy occurs.
- [ ] Boot and readiness distributions have no unexplained outlier class.
- [ ] Each result is tied to the exact image and qualification contract.

## Verification

* `just qualify-complete-boots`
* `just analyze-complete-boots`

## Evidence

* Run the complete campaign from a clean builder-produced image.
* Replay an injected failure to prove artifact preservation.
* Publish per-run and aggregate results.

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

Define outlier classification before run; all 100 must pass without retried-away failures; discrete cleanup exactness.
