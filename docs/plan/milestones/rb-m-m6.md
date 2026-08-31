---
schema: "repo-plan/v1"
id: "RB-M-M6"
title: "Qualification, Productivity & Decision"
type: "milestone"
order: 6
authorized_by: "RB-G-GATE5"
x_legacy_id: "M6"
---
## Outcome

Determine whether the architecture is reliable, reproducible, learnable, and productive enough to justify the next significant investment.

## Scope

* Complete-image boot, mixed stress, UI-action, memory-stability, and unknown-syscall qualification.
* Reproducible clean-build digests and build receipts.
* AI-assisted high-level feature, cross-boundary capability, and image-composition exercises.
* Evidence-backed scoring of hypotheses H1–H6.
* Final risk, license, security-boundary, and upstream-diff audit.
* Explicit next-phase or pivot recommendation.

## Exit criteria

* 100 clean boots of the complete image pass.
* A 12-hour mixed stress run passes.
* 10,000 scripted UI actions have complete sequence accounting.
* Zero unknown syscalls and zero unclassified kernel faults remain.
* Memory satisfies the RB-T-P601-frozen warm-up, robust slope, confidence interval, projected-growth budget, and exact-resource baseline rules.
* Two clean builds produce the same image digest.
* AI feature exercises remain understandable, tested, and appropriately isolated.
* H1–H6 are scored only Pass, Conditional, or Fail; “Promising” may appear only as explanatory narrative.
* RB-G-GATE6 records Continue, Pivot to Linux-based Rust/BEAM, Narrow, or Stop with linked evidence.

## Implementation-readiness status — 2026-08-30

**Gate-blocked; not authorized.** RB-T-P601 freezes the canonical commit/image, runner profiles, warm-up, samples, exact-resource baselines, memory-slope/confidence rules, invalid-run taxonomy, retry policy, and first-failure preservation. AI exercises run in isolated worktrees/images; retained changes require a new canonical image and affected requalification.
