---
schema: "repo-plan/v1"
id: "RB-T-P013"
title: "Freeze Phase 0 ADRs, licenses, hypotheses, and evidence index"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P017"
  - "RB-T-P016"
  - "RB-T-P015"
  - "RB-T-P014"
  - "RB-T-P010"
  - "RB-T-P007"
  - "RB-T-P012"
  - "RB-T-P008"
  - "RB-T-P003"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-13"
x_linear_id: "ROB-691"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-691/p0-13-freeze-phase-0-adrs-licenses-hypotheses-and-evidence-index"
x_labels:
  - "ready-for-agent"
---
# RB-T-P013: Freeze Phase 0 ADRs, licenses, hypotheses, and evidence index

## Goal

Consolidate the spikes into auditable decisions so kernel work does not depend on chat history or implicit assumptions.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P003, RB-T-P007, RB-T-P008, RB-T-P010, RB-T-P012.

## Deliverables

* Finalize ADRs for AArch64 QEMU `virt`, immutable image input, target ERTS profile, release assembly, Linux-shaped ERTS personality, fd-port ETF boundary, selected display transport, and Slint/toolkit-neutral UI boundary.
* Record dependency licenses, source hashes, features, unsafe-code inventory, and the GPLv3 consequence of the open-source Slint path.
* Update H1–H6 with Phase 0 evidence and unresolved risks.
* Build a Phase 0 evidence index linking commands, raw artifacts, normalized results, decisions, and known limitations.

## Acceptance criteria

- [ ] Every locked project decision has one current ADR and no contradictory active ADR.
- [ ] Every Phase 0 exit criterion links to durable evidence.
- [ ] All third-party artifacts have a license and source record.
- [ ] All deviations from the architecture plan are explicitly dispositioned.
- [ ] A new agent can identify the next executable issue without prior conversation access.

## Verification

* `just adr-check`
* `just license-check`
* `just evidence-check --phase 0`

## Evidence

* Run ADR, link, license, and evidence-index validation.
* Have a fresh session review the index against the milestone exit criteria.
* Record unresolved items as explicit blockers, not prose caveats.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

This issue must synthesize, not merely collect, all Phase 0 evidence. Its decision packet must explicitly disposition:

1. Exact static ERTS ELF shape, built-in native inventory, upstream diff, and target CPU/atomic/TLS assumptions.
2. Native/full-system AArch64 Linux runtime evidence and the complete startup/auxv/HWCAP contract.
3. Immutable Mix release configuration with `runtime_config_path: false` and no runtime config provider.
4. Exact fd-port framing ownership, bounded ETF tag/schema subset, safe decoding, and malformed-traffic resource limits.
5. Versioned QEMU machine/CPU/GIC/device profiles, DTB discovery, TCG/HVF differences, and selected virtio transport.
6. No-std UI toolkit proof, single-thread safety rule, measured memory/frame feasibility, replacement seam, and explicit license choice.
7. Runner-capacity evidence showing where correctness, race, long-stress, performance, screenshot, and interactive campaigns will run.
8. Tyn/current prior-art reproduction and every relevant ERTS SMP/futex/TCG risk disposition.
9. A dependency/criterion coverage report proving every Gate 0 statement has executable evidence and no blocker is hidden in prose.

The recommendation must be exactly one of: **Authorize M1**, **Repair Phase 0**, **Narrow**, **Pivot**, or **Stop**. “Proceed with known unknowns” is not an acceptable substitute for naming and approving each residual risk.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Make RB-T-P015 the toolkit/license owner; include source/claim ledger, unresolved-risk register, and exact evidence coverage with no orphan claim.
