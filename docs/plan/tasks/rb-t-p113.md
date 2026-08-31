---
schema: "repo-plan/v1"
id: "RB-T-P113"
title: "Implement and prove EL0 FP/AdvSIMD context isolation"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M1"
parent: null
depends_on:
  - "RB-T-P106B"
  - "RB-T-P014"
  - "RB-T-P103"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P1-13"
x_linear_id: "ROB-781"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-781/p1-13-implement-and-prove-el0-fpadvsimd-context-isolation"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P113: Implement and prove EL0 FP/AdvSIMD context isolation

## Goal

Safely support the FP/AdvSIMD state assumed by the AArch64 hard-float ABI without leaking or corrupting state across EL0 tasks, interrupts, preemption, or CPUs.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-T-P103, RB-E-P106, RB-E-P108, RB-T-P014.

Blocks: RB-T-P112, RB-G-GATE1, RB-T-P201, RB-T-P202.

## Deliverables

* Freeze the POC policy: eager FP/SIMD save/restore for simplicity unless a separately reviewed lazy design proves correct.
* Configure architectural controls so EL0 access matches the advertised `HWCAP_FP`/`HWCAP_ASIMD` contract and unsupported SVE/SME state remains disabled/unadvertised.
* Define the complete per-thread state: V0–V31, FPCR, FPSR, validity/initial-state rules, alignment, ownership, and kernel-use policy.
* Save/restore state on every relevant context switch and migration; handle interrupts/exceptions without corrupting interrupted user state.
* Ensure kernel Rust/assembly code either never uses FP/SIMD or follows a separately explicit save/restore discipline enforced by build/lint policy.
* Add state to diagnostic dumps and later AArch64 signal-frame requirements without exposing another task's registers.
* Account for state allocation, task teardown, fork/clone inheritance semantics, and zeroization/initialization.

## Acceptance criteria

- [ ] Two or more preempted EL0 tasks retain unique randomized V-register/FPCR/FPSR patterns across at least one million context switches.
- [ ] Timer interrupts, synchronous faults, syscalls, task exit/reuse, and CPU migration do not leak or corrupt FP/SIMD state.
- [ ] Newly created tasks receive the specified clean initial state; reused task structures cannot expose prior state.
- [ ] The kernel advertises FP/ASIMD through auxv only when this mechanism is enabled and tested.
- [ ] SVE/SME and any unimplemented extended state are disabled or fail closed and are not advertised.
- [ ] A deliberately omitted register or barrier makes the negative canary fail.

## Verification

* `just test-fpsimd-context`
* `just stress-fpsimd-context`
* `just audit-kernel-fpsimd-use`

## Evidence

* Randomized register-pattern stress with preemption at every save/restore boundary.
* Cross-task confidentiality tests, task-reuse tests, migration tests after SMP exists, and fault/interrupt injection.
* Disassembly/build audit showing whether kernel code emits FP/SIMD instructions.
* Structured traces containing task/CPU/generation identifiers but never secret register contents in normal logs.

## Out of scope

* SVE, SME, MTE, hardware virtualization state, lazy-FP optimization, production side-channel hardening, or JIT.

## Additional context
### Why this is a blocker

Rust's `aarch64-unknown-none` hard-float target assumes FP and AdvSIMD/NEON. Musl and ERTS may also use this state. The existing scheduler/context-switch plan saves only integer/control state; that can yield silent data corruption even when all ordinary task tests pass.
### Completion rule

Done means the exact advertised AArch64 FP/AdvSIMD ABI has complete per-thread isolation evidence under preemption, faults, reuse, and—once available—migration.
### Learning checkpoint

Explain why the hard-float ABI creates a kernel obligation even if application code appears not to use floating point, and enumerate every saved register/control field.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Keep eager save/restore. Move cross-CPU migration completion to RB-T-P205B/Gate 2; Gate 1 proves single-CPU preemption/fault/reuse.
### Normative readiness correction — 2026-08-30

Gate 1 acceptance covers single-CPU task switch, fault, and task-structure reuse. Cross-CPU migration evidence moves to RB-T-P205B and Gate 2; it does not block Gate 1.
