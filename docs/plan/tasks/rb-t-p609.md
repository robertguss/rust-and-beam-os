---
schema: "repo-plan/v1"
id: "RB-T-P609"
title: "Conduct the final security-boundary, fault-model, dependency, and upstream audit"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P608"
  - "RB-T-P604"
  - "RB-T-P605"
  - "RB-T-P602"
  - "RB-T-P606"
  - "RB-T-P607"
  - "RB-T-P603"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-09"
x_linear_id: "ROB-767"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-767/p6-09-conduct-the-final-security-boundary-fault-model-dependency-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P609: Conduct the final security-boundary, fault-model, dependency, and upstream audit

## Goal

Confirm that the POC makes only the security and portability claims it actually proves and that no shortcut invalidates the architecture.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P602, RB-T-P603, RB-T-P604, RB-T-P605, RB-T-P606, RB-T-P607, RB-T-P608.

## Deliverables

* Audit EL0/EL1 separation, address spaces, W^X, user-copy, handle/fd rights, IPC bounds, immutable image, device rights, ETF limits/atoms, process cleanup, and unknown-call policy.
* Review every unsafe module, dependency feature/license, OTP patch, Slint decision, bundled asset, build download, and unclassified failure.
* Fault the renderer, BEAM, worker, IPC endpoint, device, malformed image, malformed ETF, and resource limits; confirm documented containment/degradation.
* Update the threat/fault model with explicitly deferred production controls and forbid production/mobile-security claims.

## Acceptance criteria

- [ ] No known path grants BEAM direct display/input, renderer ERTS release access, unrelated process capabilities, writable executable storage, or unbounded protocol/kernel allocation.
- [ ] Every fault class produces the documented containment or an explicit blocker.
- [ ] The upstream diff contains no prohibited semantic change.
- [ ] SBOM/license/provenance are complete and consistent.
- [ ] Deferred secure boot, signing, rollback, ASLR/hardening, third-party sandboxing, and phone security remain clearly deferred.

## Verification

* `just audit-security-boundaries`
* `just run-final-fault-matrix`
* `just audit-otp-diff`

## Evidence

* Run the fault matrix and capability-denial suite.
* Perform fresh-session unsafe, dependency, license, and claim audits.
* Publish findings with accepted/fixed/blocking disposition.

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

Include platform/HWCAP, FP, cache/TLB, VirtIO, display-surface, user-copy, release-native closure, source ledger, and prior-art claim audit.
