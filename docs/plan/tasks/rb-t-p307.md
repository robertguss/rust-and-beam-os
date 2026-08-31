---
schema: "repo-plan/v1"
id: "RB-T-P307"
title: "Close ERTS-discovered host-contract defects without semantic runtime patches"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P302"
  - "RB-T-P306"
  - "RB-T-P304"
  - "RB-T-P305"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-07"
x_linear_id: "ROB-729"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-729/p3-07-close-erts-discovered-host-contract-defects-without-semantic"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P307: Close ERTS-discovered host-contract defects without semantic runtime patches

## Goal

Resolve integration defects through tested kernel/adapter semantics while protecting the upstream-runtime hypothesis.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P302, RB-T-P304, RB-T-P305, RB-T-P306.

## Deliverables

* For every failure, reproduce it with the smallest musl/C/Erlang probe and classify kernel bug, contract omission, build-profile issue, or genuine ERTS-port requirement.
* Add or change kernel behavior only after updating `beam-host.yaml`, conformance tests, and reference evidence.
* Maintain a running upstream diff report and reject changes to scheduler, GC, loader, instruction execution, process semantics, or boot shortcuts.
* Remove temporary diagnostics/workarounds that bypass normal runtime behavior.

## Acceptance criteria

- [ ] Every integration fix has a pre-fix failing test and post-fix passing evidence outside the full ERTS boot when feasible.
- [ ] Zero unexplained deviations from reference semantics remain.
- [ ] The OTP source diff is zero or confined to a small build-detection/OS-adapter patch that is explicitly reviewed for upstream suitability.
- [ ] No unsupported syscall is reclassified as success without exact semantics.

## Verification

* `just test-musl-guest`
* `just test-erts-core-workloads`
* `just audit-otp-diff`

## Evidence

* Run the complete musl contract suite after each family of fixes.
* Audit OTP and kernel diffs in a fresh session.
* Publish defect dispositions and updated contract digest.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Additional context
### Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.
### Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.
### Readiness-audit correction — 2026-08-30

### Preserve the exact central claim

* “Standard upstream ERTS” requires compiled runtime semantic sources to be unchanged from the pinned upstream tag. Cross-build/configure/build-script patches may be tolerated only when proven not to alter compiled runtime behavior; an OTP OS-adapter, scheduler, loader, allocator, signal, thread, GC, instruction, boot, or compatibility patch changes the claim and requires Gate 3 to classify a port/fork rather than upstream ERTS.
* Diagnostics for defect localization must be external or use a separately hashed diagnostic artifact. They are removed before official evidence, and the official artifact hash must return exactly to the RB-T-P005 value.
* Every failure receives one disposition: kernel/native-object defect, Linux-personality semantic defect, contract omission, toolchain/build defect, unsupported platform assumption, QEMU/runner defect, or genuine ERTS-port requirement. “Integration issue” is not a terminal classification.
* A newly observed syscall, flag, structure, file, path, CPU feature, thread behavior, or semantic requirement invalidates the frozen M2 contract until `beam-host.yaml`, independent reference evidence, conformance, contention qualification, revision-2 audit, and Gate 2 are rerun and reauthorized.
* A changed ERTS argument/profile made to avoid a defect is a deliberate scope narrowing and goes to Gate 3; it is not a routine fix.
* Spin/yield loops, startup delays, fake readiness, ignored errors/flags, timeout inflation/retry, disabled signals, forced single scheduler, host-file passthrough, writable scratch, and relaxed futex/poll/VM semantics are forbidden as accepted fixes. Diagnostic experiments remain named, time-bounded, and excluded from official images.
* Each fix begins with the smallest independent failing probe and invariant trace, applies at the lowest correct abstraction, then reruns the affected model/property tests, all M2 conformance/mutation tests, runner-specific regressions, and the complete official ERTS path.
* Maintain a cumulative defect ledger including first evidence, reproduction rate, root cause, alternatives rejected, code/contract changes, proof of removal, regression ID, reopened gates, and residual uncertainty. No defect is closed because a later boot happened to pass.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Correct repair seam. Every new syscall/flag is a contract change requiring tests and human review.
