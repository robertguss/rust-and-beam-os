---
schema: "repo-plan/v1"
id: "RB-T-P213"
title: "Run one-hour four-vCPU contention and randomized preemption qualification"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P200"
  - "RB-T-P205C"
  - "RB-T-P205A"
  - "RB-T-P205B"
  - "RB-T-P211C"
  - "RB-T-P211B"
  - "RB-T-P211A"
  - "RB-T-P213A"
  - "RB-T-P016"
  - "RB-T-P212"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-13"
x_linear_id: "ROB-717"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-717/p2-13-run-one-hour-four-vcpu-contention-and-randomized-preemption"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P213: Run one-hour four-vCPU contention and randomized preemption qualification

## Goal

Expose rare scheduler, pthread, futex, signal, VM, and readiness races before ERTS obscures them.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-E-P205, RB-T-P212.

## Deliverables

* Create a deterministic mixed workload that repeatedly creates/exits threads, contends on synchronization, maps/protects/unmaps memory, delivers signals, performs pipe/poll I/O, and uses timeouts.
* Run on four vCPUs for at least one hour with randomized but recorded preemption seeds.
* Continuously reconcile tasks, threads, pages, VMAs, descriptors, waiters, timers, pending signals, and trace overflows.
* Treat timeout, unknown syscall, accounting drift, and unclassified fault as first-class failure artifacts.

## Acceptance criteria

- [ ] The full run completes without deadlock, panic, unknown call, unclassified signal/fault, or monotonic resource leak.
- [ ] Mutual exclusion, condition wakeups, join completion, poll readiness, and memory protections preserve their invariants.
- [ ] Every run can be replayed from build ID, configuration, and seed.
- [ ] Automatic retries do not hide failures.

## Verification

* `just qualify-musl-contract`
* `just replay-seed SEED=<recorded>`

## Evidence

* Run the qualification on the declared remote Linux/TCG profile.
* Replay at least one injected failure seed.
* Publish time-series counters and the final conservation report.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit correction — 2026-08-30

The official run executes **only** the committed RB-T-P213A manifest. This issue may not choose or revise thresholds after observing results.

* Use the RB-T-P016-selected full-duration runner. Replace the original hard-coded “remote Linux/TCG” requirement if capacity/evidence classification selects native AArch64 KVM or another approved profile; retain TCG as a separate semantic/race companion where useful.
* Require preflight success for QEMU/accelerator/machine/CPU/GIC/devices, four online vCPUs, image/build/contract/manifest hashes, host resources/load, entropy mode, clocks, disk/artifact capacity, trace configuration, and watchdogs.
* Satisfy both host-wall and guest-monotonic minimum duration plus every workload-operation floor. A stalled/slow run cannot pass by merely remaining alive for an hour.
* Continuously check task/thread/page/VMA/ASID/descriptor/stream/futex/waiter/timer/signal/registration/object generations, FP/SIMD migration canaries, TLB-shootdown acknowledgements, trace loss, unknown calls/flags, lock-order violations, and progress rates.
* Run quiescent checkpoints at frozen intervals so exact-conservation resources can return to baseline. Apply the preregistered plateau/slope/confidence and absolute-cap rules only to explicitly retained pools/caches.
* Preserve the first failure and stop/continue policy specified by the manifest. A rerun is a separate result linked to the original; it cannot replace, suppress, or average away the failure.
* Report runner validity separately from guest validity. Host interruption, evidence truncation, counter reset, QEMU crash, or preflight drift makes the run invalid—not passed or failed guest evidence.
* Execute and replay the required deliberately injected failure seed before the official clean campaign so evidence capture is proven rather than assumed.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Run only on RB-T-P016-approved semantic profiles; define exact liveness/watchdog/resource criteria and preserve first failure.
