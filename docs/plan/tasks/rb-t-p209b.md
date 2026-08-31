---
schema: "repo-plan/v1"
id: "RB-T-P209B"
title: "Implement AArch64 signal frames, alternate stack, FPSIMD context, faults, and rt_sigreturn"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P209"
depends_on:
  - "RB-T-P108B"
  - "RB-T-P209A"
  - "RB-T-P113"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-09b"
x_linear_id: "ROB-792"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-792/p2-09b-implement-aarch64-signal-frames-alternate-stack-fpsimd-context"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P209B: Implement AArch64 signal frames, alternate stack, FPSIMD context, faults, and rt_sigreturn

## Goal

Deliver and return from the exact AArch64 Linux-compatible signal frame required by pinned musl/ERTS while preventing a forged frame from restoring privileged or out-of-lifetime state.

## Context

Blocked by: RB-T-P209A, RB-T-P113, RB-E-P108.

## Deliverables

* Derive the exact target `rt_sigframe`/`siginfo_t`/`ucontext_t`/`sigcontext` layout, alignment, trampoline/restorer convention, and context-record format from the pinned AArch64 headers, musl artifact, and reference traces.
* Build user frames containing the admitted signal information, saved mask/alternate-stack state, X0–X30, SP, PC, PSTATE, fault address as applicable, and mandatory FPSIMD context with V0–V31, FPCR, and FPSR.
* Explicitly disable and reject SVE, SME, ZA, MTE, GCS, extra contexts, or any optional state not advertised in RB-T-P014/RB-T-P113. Never accept an unknown context-record magic/size as harmless padding.
* Implement `sigaltstack` subset and bounded nesting, including stack-range/size/alignment validation, current-on-stack rules, overflow detection, guard-page behavior, and restoration.
* Convert only the contracted synchronous EL0 faults into signals with accurate reason/address data; kernel faults remain kernel failures and unsupported user faults terminate explicitly.
* Validate handler/restorer addresses, user stack arithmetic, writable frame range, executable return target policy, PSTATE user-allowed bits, PC/SP alignment and user range, signal mask, alternate-stack state, context record chain, FPSIMD values, and frame ownership/generation on `rt_sigreturn`.
* Restore the complete state atomically only after all validation succeeds. A rejected frame must not partially change registers, mask, FP state, address space, or scheduler state.
* Keep signal frames tied to the originating thread/address-space generation so copied or stale frames cannot be used after thread, stack, or mapping reuse.

## Acceptance criteria

- [ ] Normal and `SA_SIGINFO` handlers receive the correct arguments and return to the exact interrupted user state.
- [ ] Alternate-stack delivery, nested delivery within the declared limit, synchronous fault recovery, and FP/AdvSIMD preservation match the admitted AArch64 Linux behavior.
- [ ] Forged PC, SP, PSTATE, mask, stack, FPSIMD record, context size/magic, frame address, handler/restorer, or generation is rejected without privilege escalation, kernel memory access, partial restore, or cross-thread state disclosure.
- [ ] SVE/SME and every unimplemented context extension are neither advertised nor accepted.
- [ ] A frame cannot cross a guard page or overflow user address arithmetic; failure follows the frozen fatal-signal policy.
- [ ] Repeated delivery/return, fault-on-altstack, and thread migration preserve integer, TLS, FP/SIMD, and mask state exactly.

## Verification

* `just test-aarch64-signal-frames`
* `just test-rt-sigreturn-forgeries`
* `just stress-signal-fpsimd`
* `just test-synchronous-user-faults`

## Evidence

* Byte-level frame fixtures from reference AArch64 Linux; positive handler/return tests; alternate-stack/nesting matrix; synchronous fault matrix; randomized register/FPSIMD patterns; truncation/misalignment/unknown-record/privileged-PSTATE/kernel-address/stale-generation forgeries; frame copyout fault injection at every boundary.
* Disassembly/header provenance and trace comparison for trampoline/restorer and `rt_sigreturn` calling convention.

## Out of scope

* SVE/SME/MTE/GCS, ptrace, core dumps, arbitrary real-time signal payloads, process groups/job control, or production exploit-hardening claims.

## Additional context
### Completion rule

Done means the exact minimal AArch64 signal-frame ABI round-trips all admitted state and fails closed against every malformed, privileged, stale, or unsupported restoration attempt.
### Learning checkpoint

Draw the complete signal frame and delivery/return path, identify every field that can affect privilege or control flow, and explain why FPSIMD state and optional context records cannot be omitted from validation.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Excellent security-critical child. After RB-E-P108 split, depend on RB-T-P108B; retain forged-frame and unsupported-context fail-closed tests.
### Normative readiness correction — 2026-08-30

Gate 2 requires byte-level AArch64 signal-frame fixtures, FPSIMD context coverage, forged-frame and unsupported-extension negative tests, and fail-closed `rt_sigreturn` validation. This issue depends on RB-T-P108B, not the RB-E-P108 tracking parent.
