---
schema: "repo-plan/v1"
id: "RB-T-P601"
title: "Freeze the final qualification contract and runner profiles"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P016"
  - "RB-G-GATE5"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-01"
x_linear_id: "ROB-761"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-761/p6-01-freeze-the-final-qualification-contract-and-runner-profiles"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P601: Freeze the final qualification contract and runner profiles

## Goal

Define the evidence, thresholds, samples, failure policy, and runner identities before seeing final results.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-G-GATE5.

## Deliverables

* Create a versioned qualification manifest covering complete boots, mixed stress, UI actions, reproducible builds, memory stability, unknown syscalls/faults, protocol accounting, feature exercises, and hypothesis scoring.
* Freeze Linux/TCG and Apple Silicon/HVF runner profiles, image/toolchain hashes, seeds, warm-up, durations, sample sizes, timeout policy, and artifact retention.
* Define pass/fail/invalid-run classification, when reruns are permitted, and how the first failure is preserved.
* Map every M6 criterion and H1–H6 evidence requirement to one or more executable checks or reviewed artifacts.

## Acceptance criteria

- [ ] No threshold can be changed after results without a new version and explicit rationale.
- [ ] The contract distinguishes correctness gates from informative performance observations.
- [ ] Runner-specific baselines are separate; TCG and HVF are not compared as equivalent performance environments.
- [ ] Every invalid/retried run retains its original artifacts and classification.
- [ ] A generated coverage report shows no orphan milestone criterion or hypothesis.

## Verification

* `just qualification-validate`
* `just qualification-coverage`

## Evidence

* Run manifest/schema/coverage tests.
* Have a fresh session challenge sample sizes, thresholds, and retry policy.
* Publish the frozen qualification digest before running RB-T-P602 onward.

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

Freeze objective statistics and canonical commit/image; define isolated worktrees for exercises and invalid-run/retry policy.
### Normative readiness correction — 2026-08-30

Qualification uses the RB-T-P601-frozen warm-up, sample interval, observation windows, exact resource baselines, robust memory-slope estimator and confidence interval, projected-growth budget, outlier/invalid-run classification, retry policy, host-interruption policy, and first-failure preservation. Exact tasks, descriptors, handles, ports, queues, waiters, and mappings return to baseline after cleanup unless a named cache is explicitly admitted. No automatic retry converts a failed run to pass. Freeze one canonical qualification commit/image. Exercises A–C run in isolated worktrees and cannot mutate its result.
