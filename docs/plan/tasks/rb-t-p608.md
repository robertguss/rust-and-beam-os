---
schema: "repo-plan/v1"
id: "RB-T-P608"
title: "Run AI exercise C: change theme and feature composition by rebuilding the image"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P601"
  - "RB-T-P401"
  - "RB-T-P505"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-08"
x_linear_id: "ROB-763"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-763/p6-08-run-ai-exercise-c-change-theme-and-feature-composition-by"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P608: Run AI exercise C: change theme and feature composition by rebuilding the image

## Goal

Test the clarified AI-first vision: source/manifest changes produce a distinct, reproducible installable image without mutating the running OS.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601, RB-T-P401, RB-T-P505.

## Deliverables

* Give a fresh AI agent a bounded request to change the reference theme and disable/enable one declared feature through source/assets and `system.toml`.
* Build a distinct image with new build ID/receipt while preserving locked kernel/runtime/protocol behavior.
* Boot both variants, verify visual/feature differences, and return to the previous image by selecting/rebuilding it—not by live mutation.
* Measure clean/incremental build time, cache hits, changed files, artifact differences, test time, and human review burden.

## Acceptance criteria

- [ ] The variant is fully determined by committed source/manifest/assets and has a distinct reproducible digest.
- [ ] The running guest performs no code generation, package installation, self-modification, or network download.
- [ ] Disabled capability/resources are absent from the compiled boot plan, not merely hidden in UI.
- [ ] Both variants pass applicable boot/protocol/security tests.
- [ ] The previous image remains reproducible from its receipt.

## Verification

* `just exercise-c`
* `just compare-images`
* `just evidence-check --exercise c`

## Evidence

* Run clean and incremental variant builds, image inventory diff, boots, screenshots, and capability checks.
* Review agent task receipt and diff.
* Publish composition-productivity results.

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

Use isolated variant receipts; do not mutate canonical qualification image; prove disabled resources absent.
### Normative readiness correction — 2026-08-30

This exercise runs in an isolated branch/worktree from the RB-T-P601 canonical commit and produces an independent image/build ID. It does not mutate canonical qualification. Retaining its change requires an explicit merge, a newly frozen canonical image, RB-T-P605 reproducibility/SBOM/license rerun, and every affected qualification rerun.
