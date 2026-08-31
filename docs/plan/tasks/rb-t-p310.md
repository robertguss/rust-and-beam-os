---
schema: "repo-plan/v1"
id: "RB-T-P310"
title: "Audit upstream integrity and publish the central feasibility evidence"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P308"
  - "RB-T-P309"
  - "RB-T-P307"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-10"
x_linear_id: "ROB-731"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-731/p3-10-audit-upstream-integrity-and-publish-the-central-feasibility"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P310: Audit upstream integrity and publish the central feasibility evidence

## Goal

Produce a reviewable answer to whether standard upstream ERTS truly runs on the custom OS.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P307, RB-T-P308, RB-T-P309.

## Deliverables

* Inventory the exact OTP source tag/hash, build flags, patch set, target artifact hash, release files, runtime identity, and guest image.
* Diff every OTP source change and classify build detection, OS adapter, diagnostics, or prohibited semantic modification.
* Link the 100-boot, process-scale, SMP, 12-hour, contract, and memory evidence to H1/H2.
* Document limitations: interpreter-only, no networking, no writable storage, no general POSIX, and emulator-only hardware.

## Acceptance criteria

- [ ] A reviewer can reproduce artifact provenance from upstream tag to bytes in the guest image.
- [ ] No prohibited semantic change or bypass is present.
- [ ] The evidence proves ERTS ran inside the custom OS rather than through a host bridge.
- [ ] H1 and H2 have explicit pass/fail/conditional dispositions with residual risks.
- [ ] All milestone exit criteria have durable links.

## Verification

* `just audit-otp-diff`
* `just verify-image-provenance`
* `just evidence-check --phase 3`

## Evidence

* Run provenance, image-inventory, OTP-diff, and evidence-link checks.
* Have a fresh session attempt to falsify the central claim.
* Publish the Phase 3 feasibility report.

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

### Define and prove the central claim precisely

* The phrase **standard upstream ERTS** is permitted only when every source file that contributes runtime semantics is byte-identical to the pinned upstream tag. Configure/build-system/cross-compilation patches may remain only if a source-to-object and preprocessor/config audit proves they do not alter scheduler, thread, signal, allocator, loader, VM, instruction, process, GC, timing, polling, port, or shutdown behavior.
* Any compiled OTP OS-adapter, runtime compatibility patch, semantic feature switch introduced solely for this kernel, startup workaround, or changed ERTS source means the demonstrated artifact is a **ported or forked ERTS**, not standard upstream ERTS. The report must use that label and Gate 3 must disposition the changed hypothesis.
* Reconstruct a cryptographically linked provenance chain from upstream source archive/tag and signature/hash, accepted build-only patch set, sealed toolchain/container, configure output and generated headers, compile/link commands, object inventory, `beam.smp`, packaged native files/drivers, Mix/OTP files, immutable archive, process/system manifests, system image, QEMU platform manifest, and runtime self-identity.
* Prove that the official evidence used the exact RB-T-P005 artifact bytes. Diagnostic binaries, symbol-rich rebuilds, instrumented OTP, altered flags, single-scheduler images, host ERTS, qemu-user, 9p/shared folders, host file descriptors, host RPC, or a later rebuilt artifact cannot satisfy the claim.

### Evidence sufficiency and falsification

* Link the raw and normalized evidence for final-profile startup, actual native-thread topology, simultaneous two-scheduler progress, 100 fresh boots, meaningful 10,000-process lifecycle, preregistered 12-hour campaign, memory attribution/statistics, complete M2 conformance and stress, production entropy, platform identity, unknown-call count, and every reopened Gate 2 decision.
* Preserve all failed/invalid campaigns and defect history. A final clean result cannot erase an earlier unexplained race, semantic workaround, runner discrepancy, or contract expansion; each requires a closed disposition with regression evidence.
* Demonstrate absence of a host bridge through image/config/source/binary scans plus runtime I/O provenance: no host-mounted code/data, host loader/library, forwarded syscall service, shell/launcher, network control path, or writable overlay contributes to ERTS execution.
* Quantify exactly what was and was not exercised. The claim covers the pinned non-JIT, statically linked, two-normal-scheduler profile and tested OTP/ERTS capabilities only; it does not imply JIT, distribution, networking, dynamic loading, arbitrary NIFs/drivers, writable storage, every OTP application, production security, physical hardware, or general POSIX compatibility.
* Have an independent fresh-session reviewer receive only the immutable evidence index and attempt to falsify: artifact identity, upstream semantic integrity, in-guest execution, scheduler concurrency, host-contract completeness, memory stability, and no-host-bridge. Every objection is answered with a linked artifact or becomes a gate blocker.
* Generate a claim-to-evidence matrix in which every sentence in the executive conclusion maps to named immutable evidence. Unsupported adjectives such as “complete,” “production-ready,” “mobile,” “fully upstream,” or “Linux-compatible” are prohibited.

### Completion rule amendment

RB-T-P310 is not complete with a plausible narrative. It is complete only when a fresh reviewer can reproduce the provenance, independently recompute every hash/coverage/statistical verdict, distinguish standard upstream from a port/fork, and find no unresolved contradiction between the claim and the actual tested configuration.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong central evidence ticket. Include complete native/release closure and all accepted exceptions.
