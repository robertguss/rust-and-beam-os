---
schema: "repo-plan/v1"
id: "RB-G-GATE0"
title: "Decide whether the Rust-kernel/standard-BEAM POC may enter kernel implementation"
type: "gate"
state: "open"
priority: "P1"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-AUDIT0"
  - "RB-T-P017"
  - "RB-T-P016"
  - "RB-T-P015"
  - "RB-T-P014"
  - "RB-T-P001"
  - "RB-T-P013"
  - "RB-T-P012"
  - "RB-T-P011"
  - "RB-T-P010"
  - "RB-T-P006"
  - "RB-T-P009"
  - "RB-T-P008"
  - "RB-T-P003"
  - "RB-T-P005"
  - "RB-T-P002"
  - "RB-T-P007"
  - "RB-T-P004"
related: []
actor: "human"
owner: null
defer_until: null
evidence: []
x_legacy_id: "GATE-0"
x_linear_id: "ROB-695"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-695/gate-0-decide-whether-the-rust-kernelstandard-beam-poc-may-enter"
x_labels:
  - "ready-for-human"
---
# RB-G-GATE0: Decide whether the Rust-kernel/standard-BEAM POC may enter kernel implementation

## Decision

[Architecture & Validation Plan](<../architecture.md>)

Make the cheapest honest Continue, Pivot, Narrow, or Stop decision before building the kernel.

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P001, RB-T-P002, RB-T-P003, RB-T-P004, RB-T-P005, RB-T-P006, RB-T-P007, RB-T-P008, RB-T-P009, RB-T-P010, RB-T-P011, RB-T-P012, RB-T-P013.

## Required evidence

* Review the gate in a fresh session using only repository plan content and linked evidence.
* Confirm all downstream milestones remain blocked until this issue is Done.
* Publish the decision as an ADR and repository status and evidence update.

## Acceptance criteria

- [ ] No required M0 result is accepted from a host-only substitute for the named target experiment.
- [ ] A Continue decision confirms no semantic ERTS patch, a bounded host contract, valid Mix pairing, and working HVF/TCG device path.
- [ ] A Narrow or Pivot decision edits affected downstream milestones/issues before they become actionable.
- [ ] The decision record names evidence, residual risks, rejected alternatives, and the next single issue.
- [ ] The user explicitly approves the decision.

## Decision record

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### What to build

* Review every M0 exit criterion and stop condition against linked evidence.
* Explicitly score H1 bounded upstream ERTS host contract, H2 implementable without broad Linux recreation, H3 clean Rust↔BEAM IPC, and H6 platform discipline.
* Audit the OTP diff, target artifact, Mix-release provenance, contract breadth/depth, two-host device results, protocol results, licenses, and remaining unknowns.
* Record one decision: Continue unchanged; Narrow with enumerated scope changes; Pivot to a Linux-based Rust/BEAM system; or Stop.
### Verification commands

* `just gate-report 0`
* `just evidence-check --phase 0`
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

### Mandatory authorization conditions

M1 remains blocked unless all of the following are true:

- [ ] The exact static target ERTS and exact immutable Mix release run repeatedly on authoritative AArch64 Linux with no undeclared file, dynamic-loader, native-extension, or writable-config dependency.
- [ ] `beam-host.yaml` covers startup/ELF/auxv/HWCAP plus every observed syscall family and coupled thread/futex/signal/poll lifetime behavior; every admitted behavior has positive, negative, race, and error evidence as applicable.
- [ ] The machine contract pins QEMU digest, versioned `virt-X.Y`, CPU, GIC, page size, HWCAPs, atomics, target features, and device transport, with TCG/HVF differences explicit.
- [ ] The no-std UI candidate renders and accepts input on both required hosts, obeys a proven single-thread ownership rule, fits measured budgets, remains replaceable, and has an approved distribution-license decision.
- [ ] Protocol framing has exactly one length-prefix owner per side; compressed/unsafe ETF and atom creation are impossible; malformed traffic remains bounded.
- [ ] Planned long tests have feasible measured runners, and qemu-user is not used as authoritative thread/signal/auxv evidence.
- [ ] Current BEAM-on-custom-kernel prior-art failures and workarounds have been independently dispositioned.
- [ ] There is no hidden “temporary” semantic workaround for futex/thread progress, no unknown syscall, no unclassified trace gap, and no unresolved contradiction between issue descriptions and ADRs.

### Kill/narrow criteria

RB-G-GATE0 must choose Repair, Narrow, Pivot, or Stop—not Authorize M1—if the required host contract expands into general Linux, ERTS needs prohibited semantic patches, the target release cannot boot read-only, scheduler/thread progress requires an unexplained wait-semantics workaround, the GUI path/license is unacceptable, or the available runners cannot produce valid evidence.

The gate is a human decision. Passing automated checks is necessary but not sufficient; the user must explicitly approve **Authorize M1**.
### Implementation-readiness disposition — 2026-08-30

**Action:** GATE

Strong corrected gate. It is currently unmet; authorize M1 only with all evidence and explicit human approval.
