---
schema: "repo-plan/v1"
id: "RB-T-P303"
title: "Boot kernel and stdlib in embedded noninteractive mode"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M3"
parent: null
depends_on:
  - "RB-T-P302"
  - "RB-T-P304"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P3-03"
x_linear_id: "ROB-725"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-725/p3-03-boot-kernel-and-stdlib-in-embedded-noninteractive-mode"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P303: Boot kernel and stdlib in embedded noninteractive mode

## Goal

Reach a normal minimal OTP boot and execute a deterministic Erlang action inside the custom OS.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase must run the pinned, standard upstream ERTS artifact inside the custom AArch64 OS. Linux-hosted runs are comparison evidence only. The final runtime profile is non-JIT SMP with two normal schedulers on four guest vCPUs.

Blocked by: RB-T-P302, RB-T-P304.

## Deliverables

* Provide the exact boot script, root directory, code path, VM flags, and embedded/noninteractive arguments through the process manifest.
* Support the read-only file and descriptor semantics required to load `kernel`, `stdlib`, and their dependencies.
* Boot initially with `+S 1:1` only as a diagnostic profile and execute an equivalent of `erlang:display(ok), halt().`.
* Capture application/module boot order, file access, process/thread lifecycle, and clean shutdown.

## Acceptance criteria

- [ ] The guest starts `kernel` and `stdlib`, prints the expected Erlang result, and exits cleanly.
- [ ] All loaded modules come from the immutable pinned release tree.
- [ ] No host command, guest shell, `erlexec`, network service, or manual module injection participates.
- [ ] Ten consecutive diagnostic boots produce the same classified milestones and no unknown contract behavior.

## Verification

* `just test-erts-minimal-boot`
* `just inspect-erts-modules`

## Evidence

* Run boot/eval/halt, missing-module, bad-boot-script, and clean-shutdown tests.
* Inventory loaded applications/modules and opened paths.
* Save serial and structured boot evidence.

## Out of scope

* Elixir application integration, GUI, JIT, networking, writable storage, NIFs, and phone hardware.
* Semantic patches to BEAM execution, scheduling, GC, process behavior, or loading.
* Host execution presented as guest success.

## Additional context
### Completion rule

Done requires evidence from the exact guest image and pinned upstream artifact. Any full-runtime defect must be reduced to a smaller contract test when feasible and must preserve the upstream-diff budget.
### Learning checkpoint

Explain how OS native threads relate to BEAM processes/schedulers, which host semantic this issue exercises, and how the evidence rules out a host-side or one-off success.
### Readiness-audit correction — 2026-08-30

* Derive the direct `beam.smp` argument vector from the inspected target release/reference run and pin it byte-for-byte in the immutable process manifest. No `erlexec`, shell script, environment-expanding wrapper, host launcher, or manual console command may participate.
* Use build-time `sys.config`, boot script, code path, and VM arguments only. Runtime config providers and writable generated config remain forbidden; boot the complete release tree read-only.
* Prove that `+S 1:1` is a named diagnostic profile with its own receipt and cannot be confused with final qualification. The image/artifact and all non-scheduler host semantics remain identical to the final profile.
* The deterministic Erlang action must emit a structured begin/result/halt record with nonce/build identity so serial leftovers or a host-side string cannot satisfy the oracle. The harness must verify ERTS reached the action, produced the correct term/result, initiated normal halt, and the OS reclaimed the process.
* Capture loaded applications/modules/hashes, opened image objects, native thread lifecycle, descriptors/waits/timers/signals, and post-halt resource baseline. A printed `ok` without clean shutdown and accounting is not a pass.
* Negative cases include wrong root/code path, missing/corrupt boot file, forbidden writable config attempt, wrong ERTS hash, unexpected module, unknown file access, serial truncation, action not executed, halt hang, and cleanup drift.
* Ten boots are fresh system launches with production entropy, exact platform identity, no snapshot state, and no automatic retry; compare milestone shape but permit only explicitly declared nondeterministic identifiers/timing.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Clarify dependency with RB-T-P304: either combine module-loader bootstrap with this ticket or define a minimal independently testable loader milestone.
