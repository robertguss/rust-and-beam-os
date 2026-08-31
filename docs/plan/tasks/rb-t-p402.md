---
schema: "repo-plan/v1"
id: "RB-T-P402"
title: "Boot the genuine runtime_lab Mix release inside the custom OS"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-T-P303"
  - "RB-T-P007"
  - "RB-T-P401"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-02"
x_linear_id: "ROB-741"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-741/p4-02-boot-the-genuine-runtime-lab-mix-release-inside-the-custom-os"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P402: Boot the genuine runtime_lab Mix release inside the custom OS

## Goal

Move from minimal Erlang to a normal Mix-generated Elixir/OTP application inside the guest.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-T-P401, RB-T-P007, RB-T-P303.

## Deliverables

* Package the exact Mix release payload proven in Phase 0 with the pinned guest ERTS and compiled boot manifest.
* Supply root directory, boot script, code paths, release/config data, VM flags, arguments, and environment directly to `beam.smp`.
* Start `runtime_lab` through normal OTP release boot and route Elixir Logger output to the serial descriptor.
* Emit structured runtime identity and `Application.started_applications/0` evidence.

## Acceptance criteria

- [ ] The guest boots the real Mix-generated release and starts `runtime_lab` under its application supervisor.
- [ ] Reported application, Elixir, OTP, ERTS flavor, scheduler profile, and build IDs match pinned artifacts.
- [ ] Normal configuration loading and clean shutdown work without shell scripts or guest `exec`.
- [ ] All files are read from the immutable release tree and zero unknown syscalls occur.

## Verification

* `just test-elixir-release-guest`
* `just inspect-release-guest`

## Evidence

* Run ten clean boot/shutdown cycles.
* Inventory applications/modules/files and compare with the Phase 0 target release.
* Save release provenance and boot logs.

## Out of scope

* GUI rendering, JIT, sockets/distribution, NIFs, dynamic drivers, networking, writable storage, and phone hardware.
* Shared memory or in-process Rust code inside ERTS.
* Unbounded queues or dynamic atoms from protocol input.

## Additional context
### Completion rule

Done requires guest evidence through the final process-isolated path. Host-only tests support development but cannot satisfy acceptance. Preserve bounded failure states and resource accounting.
### Learning checkpoint

Explain OTP supervision ownership, the port/descriptor boundary, one backpressure or lifecycle race, and how the evidence separates feature failure from ERTS or kernel failure.
### Readiness-audit correction — 2026-08-30

### Exact immutable release boot

* Package and boot the exact RB-T-P007 release artifact/hash with `runtime_config_path: false`. Use build-time `sys.config`, boot script, code path, VM arguments, and environment only. `Config.Provider`, `Config.Reader` runtime-provider output, generated mutable config, shell scripts, `erlexec`, guest `exec`, host environment expansion, and writable overlays remain forbidden.
* Set `ERL_CRASH_DUMP_SECONDS=0` and `ERL_CRASH_DUMP_BYTES=0` or the exact pinned equivalent so a runtime failure cannot attempt an unbounded write to `erl_crash.dump`. Preserve structured serial/kernel evidence instead and prove no crash-dump file open is attempted.
* Invoke the pinned `beam.smp` directly through the immutable process manifest. Capture the complete byte-exact `argv`/environment, root/code paths, descriptor table, personality, memory/thread/port limits, production entropy, platform identity, and artifact/release hashes.
* Verify every application/module/native object/driver actually started or loaded against the expected release inventory. A genuine Mix release does not imply every packaged OTP application is allowed to start.
* Logger uses a bounded serial handler/configuration with truncation/rate policy and no file backend, SASL disk log, rotating log, console shell, or host sink. Semantic acceptance must never depend on parsing Logger prose.
* The release tree is mounted read-only and no undeclared path access is tolerated: temp/home/cwd/config-provider/crash-dump/locale/timezone/NSS/proc/sys or dynamic code/native paths are explicit failures.

### Boot and shutdown evidence

* A boot oracle includes nonce, artifact/release/image/platform identities, application start order, supervision root identity, scheduler profile, exact loaded module hashes, descriptor/port inventory, production entropy mode, and a structured ready event emitted by the application.
* Clean shutdown requires application stop callbacks, port close/flush semantics, ERTS halt, OS-process exit, stream EOF/peer observation, address-space/TLB cleanup, and exact kernel resource baseline. A successful ready line followed by a shutdown hang or leak fails.
* Run fresh full-system launches, not snapshots. Preserve every attempt; no retry may replace a failed boot. Negative cases cover immutable-config write, missing/corrupt config/boot/module, unexpected application/native object, descriptor collision, wrong hash, unknown path/call, logger saturation, crash-dump attempt, startup timeout, and cleanup drift.
* Any target-host behavior not present in the Gate-3-authorized contract reopens M2/Gate 2 and then M3/Gate 3; it cannot be added ad hoc because Elixir now needs it.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong. Ensure exact P0 payload/ERTS pairing and zero host shell/exec/native dependency.
