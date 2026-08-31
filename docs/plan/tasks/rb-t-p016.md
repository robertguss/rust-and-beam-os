---
schema: "repo-plan/v1"
id: "RB-T-P016"
title: "Benchmark and freeze feasible TCG, KVM, and HVF qualification runner profiles"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P012"
  - "RB-T-P011"
  - "RB-T-P006"
  - "RB-T-P003"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-16"
x_linear_id: "ROB-779"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-779/p0-16-benchmark-and-freeze-feasible-tcg-kvm-and-hvf-qualification"
x_labels:
  - "ready-for-agent"
---
# RB-T-P016: Benchmark and freeze feasible TCG, KVM, and HVF qualification runner profiles

## Goal

Ensure every planned stress duration, boot campaign, visual test, and interactive threshold is executable on a declared runner—and prevent slow or semantically different emulation from invalidating conclusions.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-T-P003, RB-T-P006, RB-T-P011, RB-T-P012.

Blocks: RB-T-P013, RB-G-GATE0, RB-T-P213, RB-T-P309, RB-T-P601.

## Deliverables

* Define candidate profiles for Linux/TCG, Linux/KVM on native AArch64 when available, and Apple Silicon/HVF.
* Pin host architecture, virtualization availability, QEMU/versioned machine/CPU configuration, vCPU/RAM limits, host load policy, timeouts, watchdogs, display mode, and artifact paths.
* Build representative microbenchmarks for boot, timers, context switching, futex contention, pipe/poll wakeups, memory mapping, trace volume, software rendering, screenshot capture, and deterministic fault injection.
* Measure wall time, guest monotonic time, CPU consumption, variance, watchdog behavior, and trace/screenshot reliability.
* Assign each planned campaign to a runner by purpose: semantic correctness, race/fault exploration, long stress, performance, visual comparison, or interactive acceptance.
* Define a capacity formula and preflight check so a campaign cannot start on a runner that cannot complete it within its frozen validity/timeout envelope.
* State explicitly that performance thresholds are runner-specific and that passing one accelerator does not erase a semantic failure on another.

## Acceptance criteria

- [ ] Each Phase 1–6 verification command maps to at least one feasible runner and evidence purpose.
- [ ] TCG, KVM, and HVF are not treated as interchangeable performance or liveness environments.
- [ ] One-hour and 12-hour campaigns have measured capacity, host-resource requirements, watchdog margins, artifact-volume estimates, and interruption/restart policy.
- [ ] qemu-user is permitted only for fast smoke/differential checks; thread, signal, auxv, and startup-gate evidence comes from native AArch64 Linux or a full-system AArch64 VM.
- [ ] Runner preflight rejects missing acceleration, host overcommit, version drift, incompatible CPU/machine settings, insufficient disk, or an estimated campaign outside the frozen bound.
- [ ] The project has a realistic fallback if native AArch64 KVM is unavailable: narrow the campaign, provision an appropriate VM, or classify the affected evidence as unavailable—not silently substitute TCG performance.

## Verification

* `just benchmark-runners`
* `just runner-preflight --profile linux-tcg`
* `just runner-preflight --profile linux-kvm`
* `just runner-preflight --profile macos-hvf`
* `just runner-coverage`

## Evidence

* Execute the representative benchmark suite on every available candidate runner.
* Deliberately disable acceleration and prove preflight catches it.
* Run shortened stress and screenshot campaigns to validate watchdog and artifact retention.
* Publish per-profile capability/limitation matrix and exact commands.

## Out of scope

* Declaring benchmark results from one host universally representative.
* Hiding simulator/hypervisor defects, relaxing correctness gates because a runner is slow, or using qemu-user as proof of the full Linux userspace contract.

## Additional context
### Why this is a blocker

The plan assigns long SMP and 12-hour qualifications to QEMU/TCG without first measuring whether that runner is fast and stable enough. TCG is valuable for deterministic correctness and architecture portability, but it is not equivalent to KVM or HVF for timing, threading progress, or device behavior. Public BEAM-on-custom-kernel prior art also reports failures that reproduce under TCG but not KVM/Nitro, so “TCG failed” and “the kernel is wrong” cannot be conflated.
### Completion rule

Done means every expensive campaign has an evidence-appropriate, measured, reproducible runner profile and a preflight that prevents invalid substitutions.
### Learning checkpoint

Explain what TCG, KVM, and HVF each prove, which timing/liveness conclusions cannot cross runner boundaries, and why qemu-user is not a full thread/signal/auxv oracle.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Excellent. Preserve semantic/performance distinctions and first-failure evidence.
