---
schema: "repo-plan/v1"
id: "RB-E-P211"
title: "TRACKING: Complete clocks/deadlines, entropy, and platform queries"
type: "epic"
state: "open"
priority: "P3"
milestone: "RB-M-M2"
parent: null
depends_on:
  - "RB-T-P211B"
  - "RB-T-P211C"
  - "RB-T-P211A"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-11"
x_linear_id: "ROB-716"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-716/p2-11-tracking-complete-clocksdeadlines-entropy-and-platform-queries"
x_labels:
  - "gate-blocked"
  - "tracking"
---
# RB-E-P211: TRACKING: Complete clocks/deadlines, entropy, and platform queries

## Goal

Complete the low-complexity host queries needed by musl/ERTS without leaking host assumptions into the kernel.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Only processes declared with `abi = "linux-aarch64-beam-v1"` may see this compatibility personality. It is an adapter over project-native objects, not the public API for Rust services. Implement only the exact pinned static-musl/ERTS workload contract.

Blocked by: RB-T-P201, RB-E-P205.

## Deliverables

* Implement contracted monotonic/realtime clock queries, relative/absolute sleep behavior, and timer conversions from the generic counter.
* Provide deterministic test-mode and virtio-RNG-backed production-mode randomness with explicit seed provenance.
* Implement only admitted identity, page-size, limits, `uname`, CPU-count/affinity, and related system queries from the contract.
* Define overflow, invalid clock, interrupted sleep, deadline-in-past, partial random read, and unavailable-device behavior.

## Acceptance criteria

- [ ] Monotonic time never moves backward and sleep deadlines satisfy declared tolerance.
- [ ] Timeout calculations used by futex and poll share one audited monotonic deadline model.
- [ ] Production runs never silently use a deterministic entropy seed; tests record theirs.
- [ ] System queries return stable values consistent with the configured guest and contract.
- [ ] Unsupported queries return explicit errors and traces.

## Verification

* `just test-time`
* `just test-random`
* `just test-system-queries`

## Evidence

* Run clock progression, wrap/overflow model, sleep, interruption, random, and query probes.
* Compare admitted query shapes with reference Linux.
* Record timer frequency/calibration and RNG device evidence.

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

* RB-T-P211A owns counter-based clocks, absolute deadlines, sleep, timer queues, cancellation, and timed-wait races.
* RB-T-P211B owns virtio RNG, production/test entropy separation, process `AT_RANDOM`, admitted random reads, and fail-closed device behavior.
* RB-T-P211C owns stable guest identity, limits, CPU counts/affinity, page/cache properties, and cross-source consistency.

Do not implement new code directly under this parent. It is Done only when all children pass and the combined values agree with RB-T-P014, RB-T-P202 startup state, the actual initialized platform, and every runtime query.

Additional parent acceptance:

- [ ] All futex, poll, sleep, and signal-restart timeouts use one absolute monotonic deadline model.
- [ ] Production/qualification cannot boot with deterministic or unavailable entropy; test seeds remain reproducible and unmistakable.
- [ ] `AT_RANDOM`, HWCAP/HWCAP2, page size, CPU count/affinity, cache geometry, limits, and `uname` have no contradiction or host leakage.
- [ ] Device/timer/query faults are bounded, observable, and cannot silently degrade into plausible-looking values.
- [ ] TCG, KVM, and HVF timing measurements are classified separately while semantic monotonicity/order remains identical.
### Implementation-readiness disposition — 2026-08-30

**Action:** TRACKING

Correct conversion. Remove ready-for-agent; children 11a–c own implementation. Wait users should depend directly on 11a.
