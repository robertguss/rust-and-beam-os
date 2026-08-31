---
schema: "repo-plan/v1"
id: "RB-T-P017"
title: "Reproduce and disposition current BEAM-on-custom-kernel prior-art risks"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P003"
  - "RB-T-P001"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-17"
x_linear_id: "ROB-780"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-780/p0-17-reproduce-and-disposition-current-beam-on-custom-kernel-prior"
x_labels:
  - "ready-for-agent"
---
# RB-T-P017: Reproduce and disposition current BEAM-on-custom-kernel prior-art risks

## Goal

Use the closest current implementation evidence—especially Tyn's Rust kernel hosting upstream ERTS—to sharpen this project's risk model before repeating already-discovered mistakes.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-T-P001, RB-T-P003.

Blocks: RB-T-P008, RB-T-P013, RB-G-GATE0.

## Deliverables

* Pin a reviewed Tyn commit and inventory its actual ERTS version/build flags, ELF shape, syscalls, VFS, thread/futex/signal behavior, boot sequence, supported accelerators, patches, NIFs/drivers, and documented limitations.
* Read and summarize the futex/thread-progress history and every ruled-out mechanism relevant to this project's AArch64 design.
* Rebuild and run at least the smallest available upstream artifact on an appropriate KVM runner when feasible; record any non-reproducible claims explicitly.
* Compare Tyn's x86_64 assumptions with this project's AArch64/QEMU `virt`, EL0 isolation, non-JIT profile, two-process design, signals, atomics, and renderer requirements.
* Convert each relevant lesson into one of: already covered, new contract/test, accepted residual risk, architecture difference, or not reproducible.
* Add a targeted early liveness probe that repeatedly exercises ERTS-like thread startup, futex wait/wake, `clear_child_tid`, signal interruption, and scheduler progress before full ERTS integration.
* Forbid copying spin/yield or readiness-marker workarounds unless the underlying defect is isolated, bounded, instrumented, and explicitly approved as a failed central hypothesis or temporary diagnostic.

## Acceptance criteria

- [ ] The prior-art report distinguishes self-reported claims from independently reproduced results.
- [ ] Every documented Tyn limitation relevant to this architecture has an explicit disposition and linked test/issue.
- [ ] The project records why Tyn supports the feasibility hypothesis but does not prove AArch64/QEMU/HVF correctness.
- [ ] The early liveness probe can detect a lost wakeup, stalled startup, premature futex blocking, and thread-exit/join failure.
- [ ] No workaround that changes normal wait semantics is accepted silently into `beam-host.yaml`.
- [ ] Gate 0 lists ERTS SMP/thread progress as a first-class kill criterion rather than an ordinary integration bug.

## Verification

* `just prior-art-tyn-audit`
* `just prior-art-tyn-reproduce`
* `just test-thread-progress-probe`
* `just prior-art-coverage`

## Evidence

* Source/document audit at a pinned commit.
* Reproducible build/run attempt with exact host/accelerator evidence.
* Targeted liveness probe and injected lost-wakeup/stall cases.
* Side-by-side architecture/contract matrix and issue-link coverage report.

## Out of scope

* Forking Tyn, changing this POC to x86_64/cloud networking/JIT, or treating another project's benchmark claims as independent proof.
* Accepting a boot-only spin loop as correct futex semantics.

## Additional context
### Why this is a blocker

Tyn publicly demonstrates that a small Rust kernel can host unmodified, statically linked musl ERTS, but it also reports a remaining cold-boot SMP/thread-progress stall and a deliberate futex boot workaround, plus TCG-specific failures. That evidence supports feasibility while directly contradicting any assumption that a syscall checklist or one clean boot is enough.
### Completion rule

Done means the nearest prior art has been independently interrogated, its relevant failures are represented in this plan, and the central ERTS liveness hypothesis has a concrete early falsification path.
### Learning checkpoint

Explain what Tyn genuinely proves, what it does not prove for this AArch64 project, and why its futex/TCG history changes the required evidence.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Excellent. Classify Tyn claims as self-reported unless reproduced; compare architecture differences and prohibit wait-semantic workarounds.
