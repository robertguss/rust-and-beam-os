---
schema: "repo-plan/v1"
id: "RB-E-P209"
title: "TRACKING: Complete bounded signal state, AArch64 frames, and wait interruption"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P209A"
  - "RB-T-P209C"
  - "RB-T-P209B"
  - "RB-E-P206"
  - "RB-E-P205"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-09"
x_linear_id: "ROB-724"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-724/p2-09-tracking-complete-bounded-signal-state-aarch64-frames-and-wait"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P209: TRACKING: Complete bounded signal state, AArch64 frames, and wait interruption

## Goal

Support required process/thread signal semantics without claiming complete POSIX signal compatibility.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-E-P205, RB-E-P206.

## Deliverables

* Implement contracted `rt_sigaction`, masks, pending state, thread-directed delivery, alternate stack, synchronous user faults, and signal return frames.
* Define selection/delivery points, mask inheritance, default actions, ignored signals, nested-delivery limits, restart/interruption behavior, and process-vs-thread termination.
* Validate every user-provided action, mask, stack, trampoline/return frame, and restored register value.
* Integrate signals with blocked syscalls, futex/poll waits, thread exit, and fault containment.

## Acceptance criteria

- [ ] Probes pass for action install/query, mask changes/inheritance, targeted delivery, pending signals, alternate stack, synchronous fault handling, and return.
- [ ] A forged signal frame cannot restore privileged state or kernel addresses.
- [ ] Delivery and timeout/wakeup races yield only documented outcomes.
- [ ] Unsupported signal features fail explicitly rather than being approximated.
- [ ] A signal to one ERTS-native test thread does not corrupt unrelated threads.

## Verification

* `just test-signals`
* `just run-signal-race-matrix`

## Evidence

* Run positive, negative, forged-frame, nesting, and race matrices.
* Differentially compare admitted semantics with AArch64 Linux.
* Audit all exception-to-signal and signal-to-wait transitions.

## Out of scope

* General POSIX/Linux compatibility, networking, fork/exec, dynamic linking, writable filesystems, JIT, GUI, and phone hardware.
* Silent approximation of unsupported flags or semantics.
* ERTS source changes; this phase validates the host beneath ERTS.

## Additional context
### Completion rule

Done requires contract-linked positive, negative, boundary, error, and concurrency evidence. Unknown behavior must fail loudly. A rare race is a blocker, not an acceptable flake.
### Learning checkpoint

Explain the relevant Linux/musl contract, the kernel invariant beneath it, the dangerous race or memory-ordering edge, and how the conformance evidence proves the chosen behavior.
### Readiness-audit implementation split — 2026-08-30

This issue is now a **tracking/integration issue**, not an agent-sized implementation ticket:

* RB-T-P209A owns dispositions, masks, pending state, process/thread target selection, and default/ignore actions.
* RB-T-P209B owns the exact AArch64 user frame, alternate stack, synchronous user-fault conversion, FPSIMD context, and fail-closed `rt_sigreturn`.
* RB-T-P209C owns interface-specific `EINTR`/restart/partial-result/cancellation behavior and every race between delivery, wait completion, timeout, close, unmap, or exit.

Do not implement new code directly under this parent. It is Done only when all three children pass and their combined state machine is differentially validated against the exact pinned AArch64 Linux/musl workload.

Additional parent acceptance:

- [ ] Every admitted signal has an exact default/ignore/catch policy and bounded pending representation.
- [ ] Signal-frame delivery/return preserves integer, TLS, mask, alternate-stack, and FP/AdvSIMD state and cannot restore privileged, kernel, unsupported, or stale state.
- [ ] SVE, SME, MTE, GCS, and other unimplemented contexts are neither advertised nor accepted.
- [ ] Every blocking interface has an evidence-linked table for restart, `EINTR`, partial result, and remaining-time behavior.
- [ ] Each signal and wait operation reaches one terminal outcome; trace/accounting shows no duplicate delivery, lost pending signal, stranded waiter, or reclaimed-live object.
- [ ] The complete signal/wait race suite passes on four vCPUs with exact failing-seed replay and no accepted flake.
### Implementation-readiness disposition — 2026-08-30

**Action:** TRACKING

Correct conversion. Remove ready-for-agent; children 09a–c own implementation. Fix RB-T-P108B/direct-child dependencies.
