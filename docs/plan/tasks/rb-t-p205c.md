---
schema: "repo-plan/v1"
id: "RB-T-P205C"
title: "Implement acknowledged cross-CPU TLB shootdowns and concurrent VM safety"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P205"
depends_on:
  - "RB-T-P205B"
  - "RB-T-P114"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-05c"
x_linear_id: "ROB-786"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-786/p2-05c-implement-acknowledged-cross-cpu-tlb-shootdowns-and-concurrent"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P205C: Implement acknowledged cross-CPU TLB shootdowns and concurrent VM safety

## Goal

Make map, unmap, permission changes, address-space destruction, and ASID reuse safe while threads of one process execute on multiple vCPUs.

## Context

Blocked by: RB-T-P205B, RB-E-P204, RB-T-P114.

## Deliverables

* Track which CPUs may hold translations for each address space/ASID generation.
* Extend RB-T-P114's page-table publication API with targeted/broadcast shootdown requests, SGI/IPI delivery, per-request generation/sequence, barrier/TLBI sequence, acknowledgement, timeout, and CPU-offline/failure handling.
* Define the safety point: removed/reprotected physical pages, page tables, handles, or ASIDs cannot be freed/reused until every relevant CPU acknowledges invalidation or is proven unable to execute the address space.
* Serialize or otherwise prove concurrent `mmap`/`munmap`/`mprotect`/fault/address-space-exit operations without deadlock or partial visibility.
* Preserve W^X during concurrent permission transitions and forbid writable/executable aliases across CPUs.
* Add observability for request initiator, target mask, ASID/range/generation, acknowledgement mask, timeout, and reuse event.
* Define bounded fallback for failed shootdowns: fail/terminate safely rather than reuse stale state.

## Acceptance criteria

- [ ] A CPU cannot access a page after acknowledged unmap/protection downgrade, including when it ran the address space immediately before the request.
- [ ] Physical frames, page tables, and ASIDs are never reused before all required acknowledgements.
- [ ] Concurrent map/unmap/protect/fault/exit sequences match a reference model and preserve W^X.
- [ ] Delayed, duplicated, reordered, missing, wrong-generation, and stale shootdown messages are detected and cannot acknowledge the wrong request.
- [ ] Timeout/failure paths preserve safety, retain evidence, and do not silently continue.
- [ ] Shootdown cost and maximum outstanding requests remain bounded for the POC workload.

## Verification

* `just test-tlb-shootdowns`
* `just stress-concurrent-vm`
* `just test-asid-reuse`
* `just audit-vm-reclamation`

## Evidence

* Stale-translation canaries on every CPU; forced preemption/migration around page-table writes; delayed/lost/duplicate IPI injection; ASID wrap/reuse; address-space exit races; randomized concurrent VM model tests.
* Trace replay proving page/ASID reuse occurs only after the acknowledgement set is complete.

## Out of scope

* NUMA optimization, huge pages, swap, copy-on-write fork, JIT aliases, or physical hardware beyond the frozen QEMU POC.

## Additional context
### Completion rule

Done means no translation, frame, page table, or ASID can be observed or reused past its lifetime on any vCPU, with explicit acknowledgement evidence.
### Learning checkpoint

State the shootdown safety invariant, the Arm barrier/TLBI/acknowledgement ordering, and why freeing a frame before remote acknowledgement is a use-after-free even if the page table was already changed.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Ensure all VM/address-space destruction and reuse paths are dependency-linked.
