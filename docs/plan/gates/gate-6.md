---
id: "GATE-6"
linear_id: "ROB-769"
linear_url: "https://linear.app/robert-guss/issue/ROB-769/gate-6-choose-continue-pivot-narrow-or-stop-after-the-completed-poc"
title: "Choose Continue, Pivot, Narrow, or Stop after the completed POC"
milestone: "M6"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P6-10"
  - "P6-09"
  - "P6-08"
  - "P6-07"
  - "P6-02"
  - "P6-05"
  - "P6-04"
  - "P6-01"
  - "P6-06"
  - "P6-03"
blocks: []
---
# GATE-6: Choose Continue, Pivot, Narrow, or Stop after the completed POC

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Make the final investment decision using the complete POC evidence rather than novelty or sunk cost.

## Locked context

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

## What to build

* Review H1–H6, final qualification, productivity exercises, learning value, open risks, expected next-phase cost, and whether the architecture remains enjoyable to build.
* Choose exactly one outcome: Continue to portability/JIT; Narrow to a smaller Rust/BEAM system; Pivot to a Linux/Nerves-based product; Pivot to another runtime boundary; or Stop.
* If Continue, authorize only the next significant evidence chunk: second AArch64 target plus JIT/W^X—not a whole smartphone roadmap.
* If Pivot/Narrow/Stop, preserve the reusable kernel, protocol, runtime-hosting, and learning artifacts and update project status honestly.

## Acceptance criteria

- [ ] Continue requires H1–H4 Pass and H5 at least promising; the decision cites the final evidence report.
- [ ] No outcome claims phone readiness, production security, battery viability, hardware support, or ecosystem viability.
- [ ] The decision records expected value, residual risk, rejected alternatives, and the next bounded experiment or closure action.
- [ ] The user explicitly approves the outcome.
- [ ] Project and downstream roadmap status match the decision.

## Required tests and evidence

* Conduct a final fresh-session decision review.
* Publish the gate ADR and repository status and evidence update.
* Create a new post-POC project only if the selected outcome authorizes it.

## Verification commands

* `just gate-report 6`
* `just evidence-check --all`

## Dependencies

Blocked by: P6-01, P6-02, P6-03, P6-04, P6-05, P6-06, P6-07, P6-08, P6-09, P6-10.

## Out of scope

* New kernel/runtime/UI features not required by qualification.
* JIT, second hardware target, networking, persistent writable storage, update slots, phone drivers, or production security.
* Hiding failed runs, retroactively weakening thresholds, or presenting the emulator POC as a daily-driver phone OS.

## Completion rule

Done requires the frozen qualification contract, exact image/build provenance, raw and summarized evidence, and honest classification of every failure or exception.

## Learning checkpoint

Explain what the evidence proves, what it does not prove, one source of measurement bias, and the strongest fact that could justify stopping or pivoting.

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Good final investment gate. Require canonical evidence and no phone/production-security overclaim.
