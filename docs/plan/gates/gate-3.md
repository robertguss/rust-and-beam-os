---
id: "GATE-3"
linear_id: "ROB-735"
linear_url: "https://linear.app/robert-guss/issue/ROB-735/gate-3-decide-whether-standard-upstream-erts-on-the-custom-os-is"
title: "Decide whether standard upstream ERTS on the custom OS is proven"
milestone: "M3"
kind: "gate"
status: "ready-for-human"
priority: "high"
parent: null
labels:
  - "ready-for-human"
blocked_by:
  - "P3-00"
  - "P3-01"
  - "P3-09"
  - "P3-10"
  - "P3-08"
  - "P3-04"
  - "P3-07"
  - "P3-03"
  - "P3-02"
  - "P3-05"
  - "P3-06"
blocks:
  - "P4-01"
---
# GATE-3: Decide whether standard upstream ERTS on the custom OS is proven

[Architecture & Validation Plan](<../architecture.md>)

## Goal

Make the central project decision before investing in Elixir integration and GUI work.

## Locked context

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

## What to build

* Review upstream integrity, 100 clean boots, final SMP topology, 10,000-process result, 12-hour stress, memory budget, contract drift, and all residual defects.
* Decide whether the evidence supports standard ERTS, an unacceptable fork, a narrower runtime profile, or a pivot.
* Record Continue to Elixir/IPC, Repair within M3, Narrow, Pivot to Linux/Nerves or AtomVM, or Stop.
* Update downstream scope and project status to match the decision.

## Acceptance criteria

- [ ] Continue requires upstream semantic integrity, final SMP, zero unknown calls, repeatable boot, and successful sustained stress.
- [ ] A conditional result cannot be described as proven without explicit remaining gate work.
- [ ] The decision distinguishes technical feasibility from product worth.
- [ ] The user approves the record; M4 remains blocked until then.

## Required tests and evidence

* Conduct a fresh-session adversarial review of the feasibility report.
* Publish the gate ADR and repository status and evidence update.
* Name the exact next issue and remaining risks.

## Verification commands

* `just gate-report 3`
* `just evidence-check --phase 3`

## Dependencies

Blocked by: P3-01, P3-02, P3-03, P3-04, P3-05, P3-06, P3-07, P3-08, P3-09, P3-10.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.

## Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.

## Readiness-audit correction — 2026-08-30

### Mandatory authorization conditions

M4 remains blocked unless all original criteria plus the following are satisfied:

- [ ] The exact official `beam.smp` bytes in the immutable image trace to the pinned upstream source and sealed toolchain; runtime identity, artifact hash, manifests, and platform identity agree.
- [ ] Every compiled source that contributes ERTS runtime semantics is byte-identical to upstream. Build/configuration-only patches are proven non-semantic. Any OTP OS-adapter or runtime patch changes the result to a port/fork and cannot be labeled standard upstream ERTS.
- [ ] The final non-JIT profile uses the exact frozen arguments on four guest vCPUs, and evidence proves two normal schedulers perform overlapping real work on distinct vCPUs with no starvation or single-scheduler fallback.
- [ ] The actual native-thread topology, TLS, FP/SIMD migration, futex/robust cleanup, signals, polling, timers, mappings, descriptors, and shutdown behavior remain within the reauthorized M2 contract with zero unknown calls, flags, files, paths, CPU features, or semantic workarounds.
- [ ] All 100 fresh boots and the meaningful 10,000-process workload satisfy the preregistered manifest, operation floors, exact cleanup baselines, production entropy, valid runner/evidence requirements, and no-retry rule.
- [ ] The 12-hour campaign satisfies both duration and operation floors, all progress/correctness assertions, exact-resource conservation, and the prespecified memory attribution/plateau/slope/cap rules. No missing evidence, trace loss, host/QEMU invalidity, or post-hoc threshold change exists.
- [ ] Every earlier failure, TCG/HVF/KVM discrepancy, contract expansion, diagnostic artifact, and workaround has an explicit closed disposition and regression evidence. A later clean boot does not erase an unexplained defect.
- [ ] The evidence proves execution inside the custom OS without host loader/library, qemu-user, shared filesystem, forwarded syscall service, shell/launcher, host RPC, writable overlay, or manual intervention.
- [ ] The final feasibility report limits its claim to the exact tested profile and does not imply JIT, networking/distribution, arbitrary NIFs/drivers, writable storage, physical-phone hardware, production security, or general Linux/POSIX compatibility.

### Decision rule

The decision must be exactly one of:

* **Authorize M4 — standard upstream ERTS proven for the frozen POC profile**;
* **Repair M3**;
* **Narrow the runtime profile and requalify**;
* **Accept a port/fork and rename the hypothesis/project claim**;
* **Pivot to Linux/Nerves or AtomVM**; or
* **Stop**.

The user must explicitly approve authorization. Automated green checks are necessary but not sufficient. Any conditional, invalid, partially rerun, patched-runtime, single-scheduler, or unexplained-workaround result cannot be described as proof.

### Gate output

The gate record must include the exact claim sentence approved for downstream use, claim-to-evidence matrix, immutable evidence hashes, failed/invalid-run ledger, residual risks, exclusions, next authorized issue, and the conditions that would reopen Gate 2 or Gate 3.

## Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Continue only with objective SMP, memory, boot, upstream-diff, and unknown-call evidence.
