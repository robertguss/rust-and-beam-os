---
schema: "repo-plan/v1"
id: "RB-T-P211C"
title: "Implement bounded platform identity, limits, CPU-count, and affinity queries"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P211"
depends_on:
  - "RB-T-P205A"
  - "RB-T-P205B"
  - "RB-T-P201"
  - "RB-T-P014"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-11c"
x_linear_id: "ROB-796"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-796/p2-11c-implement-bounded-platform-identity-limits-cpu-count-and"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P211C: Implement bounded platform identity, limits, CPU-count, and affinity queries

## Goal

Return one stable, internally consistent Linux-shaped platform identity for only the queries observed from pinned musl/ERTS.

## Context

Blocked by: RB-T-P201, RB-E-P205, RB-T-P014.

## Deliverables

* Derive the exact identity, page-size, resource-limit, processor-count, scheduler-affinity, cache/topology, `uname`, and related query calls/fields from `beam-host.yaml` and reference traces.
* Generate responses from the frozen guest manifest and actual initialized CPU/memory state—not host properties and not scattered constants.
* Define online/configured/affinity-allowed CPU counts, CPU ID numbering, affinity-mask width, one- versus four-vCPU profiles, and what happens when a caller asks for an unsupported CPU or mask size.
* Reconcile reported page size, cache line sizes, HWCAP/HWCAP2, target CPU, machine, GIC, memory limits, clock tick assumptions, hostname/domain placeholders, and release identity with RB-T-P014 and RB-T-P202 startup auxv.
* Implement only observed resource-limit queries/updates. Immutable hard bounds cannot be raised beyond the process/kernel budgets even when Linux would permit broader policy.
* Prevent host leakage: no remote VM hostname, host CPU brand, macOS/Linux host release, host core count, host memory, or host filesystem data may appear.
* Add one generated `platform_identity.json` source and validation that all startup/query/reporting paths consume it or an explicitly measured runtime field.

## Acceptance criteria

- [ ] Every reported value is stable across repeated boots of one profile, matches the guest's actual configured/online resources, and has one source of truth.
- [ ] Auxv, syscalls, ERTS identity, limits, CPU count/affinity, cache/page properties, and image/build receipt contain no contradiction.
- [ ] One-vCPU and four-vCPU profiles report only their actual legal CPUs and reject invalid masks/sizes with the frozen result.
- [ ] No host identity/resource property leaks into the guest.
- [ ] Unsupported query names, fields, flags, writes, or oversized buffers fail explicitly and without partial copyout.
- [ ] A deliberate manifest/runtime mismatch is caught before ERTS launch.

## Verification

* `just test-platform-queries`
* `just verify-platform-identity`
* `just scan-host-leakage`
* `just test-affinity-profiles`

## Evidence

* Reference-Linux shape probes; one/four-vCPU consistency matrix; auxv/query cross-check; host-leak scan across serial/traces/UI; invalid mask/size/limit tests; platform-manifest drift canaries.

## Out of scope

* NUMA, CPU hotplug, cgroups, containers/namespaces, dynamic hostname administration, full `/proc`/`sysfs`, arbitrary rlimits, host pass-through, or production multi-tenant identity.

## Additional context
### Completion rule

Done means every admitted system query describes the guest—not the host—and agrees bit-for-bit with startup auxv, actual initialized resources, and the frozen platform manifest.
### Learning checkpoint

Explain the difference among configured, online, and affinity-allowed CPUs; identify every duplicated platform value that must be reconciled; and show how host leakage is detected.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong child. Keep one generated source of truth and host-leak scan; link auxv/query consistency to RB-T-P014 and RB-T-P202.
