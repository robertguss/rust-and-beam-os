---
schema: "repo-plan/v1"
id: "RB-G-GATE6"
title: "Choose Continue, Pivot, Narrow, or Stop after the completed POC"
type: "gate"
state: "open"
priority: "P1"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P610"
  - "RB-T-P609"
  - "RB-T-P608"
  - "RB-T-P607"
  - "RB-T-P602"
  - "RB-T-P605"
  - "RB-T-P604"
  - "RB-T-P601"
  - "RB-T-P606"
  - "RB-T-P603"
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
x_legacy_id: "GATE-6"
x_linear_id: "ROB-769"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-769/gate-6-choose-continue-pivot-narrow-or-stop-after-the-completed-poc"
x_labels:
  - "ready-for-human"
---
# RB-G-GATE6: Choose Continue, Pivot, Narrow, or Stop after the completed POC

## Decision

[Architecture & Validation Plan](<../architecture.md>)

Make the final investment decision using the complete POC evidence rather than novelty or sunk cost.

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P602, RB-T-P603, RB-T-P604, RB-T-P605, RB-T-P606, RB-T-P607, RB-T-P608, RB-T-P609, RB-T-P610.

## Required evidence

* Conduct a final fresh-session decision review.
* Publish the gate ADR and repository status and evidence update.
* Create a new post-POC project only if the selected outcome authorizes it.

## Acceptance criteria

- [ ] Continue requires H1–H4 Pass and H5 at least promising; the decision cites the final evidence report.
- [ ] No outcome claims phone readiness, production security, battery viability, hardware support, or ecosystem viability.
- [ ] The decision records expected value, residual risk, rejected alternatives, and the next bounded experiment or closure action.
- [ ] The user explicitly approves the outcome.
- [ ] Project and downstream roadmap status match the decision.

## Decision record

Done requires the frozen qualification contract, exact image/build provenance, raw and summarized evidence, and honest classification of every failure or exception.

## Out of scope

* New kernel/runtime/UI features not required by qualification.
* JIT, second hardware target, networking, persistent writable storage, update slots, phone drivers, or production security.
* Hiding failed runs, retroactively weakening thresholds, or presenting the emulator POC as a daily-driver phone OS.

## Additional context
### What to build

* Review H1–H6, final qualification, productivity exercises, learning value, open risks, expected next-phase cost, and whether the architecture remains enjoyable to build.
* Choose exactly one outcome: Continue to portability/JIT; Narrow to a smaller Rust/BEAM system; Pivot to a Linux/Nerves-based product; Pivot to another runtime boundary; or Stop.
* If Continue, authorize only the next significant evidence chunk: second AArch64 target plus JIT/W^X—not a whole smartphone roadmap.
* If Pivot/Narrow/Stop, preserve the reusable kernel, protocol, runtime-hosting, and learning artifacts and update project status honestly.
### Verification commands

* `just gate-report 6`
* `just evidence-check --all`
### Learning checkpoint

Explain what the evidence proves, what it does not prove, one source of measurement bias, and the strongest fact that could justify stopping or pivoting.
### Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Good final investment gate. Require canonical evidence and no phone/production-security overclaim.
