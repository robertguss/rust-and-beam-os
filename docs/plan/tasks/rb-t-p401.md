---
schema: "repo-plan/v1"
id: "RB-T-P401"
title: "Extend system.toml and the boot plan for renderer/BEAM IPC resources"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M4"
parent: null
depends_on:
  - "RB-G-GATE3"
  - "RB-T-P110"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P4-01"
x_linear_id: "ROB-736"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-736/p4-01-extend-systemtoml-and-the-boot-plan-for-rendererbeam-ipc"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P401: Extend system.toml and the boot plan for renderer/BEAM IPC resources

## Goal

Make process artifacts, compatibility personalities, capabilities, descriptors, limits, and IPC topology deterministic image-build inputs.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This phase boots a genuine Mix release inside the custom guest. Rust and BEAM remain separate EL0 processes. The boundary is two kernel-created bounded streams, fixed ERTS descriptors, a standard fd port, four-byte packet framing, and the approved ETF subset.

Blocked by: RB-G-GATE3, RB-T-P110.

## Deliverables

* Finalize the `system.toml` schema for process images, ABI selection, arguments/environment, memory limits, native handles, ERTS fd mappings, read-only roots, and named bounded streams.
* Validate unique process/resource names, endpoint direction, rights, capacities, fd collisions, memory totals, file existence/hash, and unsupported ABI/resource combinations.
* Compile the manifest into a compact immutable boot plan consumed by the kernel; never parse permissive configuration in privileged boot code.
* Generate a human-readable image inventory and capability graph from the same validated model.

## Acceptance criteria

- [ ] The manifest declares separate `renderer` and `beam` processes and exactly two directional bounded UI streams.
- [ ] The renderer receives display, pointer, clock, log, assets, and UI channel capabilities; BEAM receives only its release tree and declared descriptors.
- [ ] Invalid capacities, rights, paths, hashes, fd reuse, missing endpoints, or memory totals fail the host build.
- [ ] Two identical inputs produce the same boot plan and inventory digest.

## Verification

* `just test-system-manifest`
* `just image`
* `just inspect-image`

## Evidence

* Run schema/property/negative tests and deterministic-build comparison.
* Review the generated capability graph against the security model.
* Save example valid/invalid manifests and the composition ADR.

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

### Separate qualification and renderer manifests

* Define two immutable profile instances from one typed schema. The M4 `ipc_probe` profile contains `beam` plus a native qualification service with only log, monotonic-clock, and the two UI stream endpoints. The M5 `renderer` profile replaces that artifact and adds display, pointer, and immutable-asset capabilities only after Gate 4. RB-T-P409 evidence cannot be misrepresented as evidence for the final renderer.
* Declare exactly two unidirectional stream objects: `beam_to_ui` and `ui_to_beam`. For each, freeze capacity, atomic/partial write contract, endpoint owner, descriptor or typed-handle mapping, generation, rights, EOF/last-reader/last-writer behavior, and process-exit cleanup.
* The BEAM process receives distinct fixed input and output descriptors with exact direction and no collision with serial/logger/runtime descriptors. The manifest records whether any descriptor is duplicated, who owns closure, and that no fd-port owner restart/reopen guarantee exists.
* Boot order is deterministic: create streams and endpoints; validate/allocate all process resources; install BEAM descriptors/native handles; launch the native service/renderer; launch BEAM or the explicitly frozen alternative; then permit protocol handshake. Define failure rollback at each step so a half-launched image cannot retain an endpoint or process.

### Validate the complete capability and budget model

* Every artifact, release tree, asset bundle, platform profile, process manifest, and protocol contract is content-addressed. Artifact substitution, valid-but-wrong hash, descriptor drift, or capability-profile mismatch fails before EL0 execution.
* Sum committed-page limits plus page tables, kernel stacks, per-CPU memory, stream buffers, descriptor/port state, traces, GPU/input/RNG queues, framebuffer resources, immutable-image mappings, and required safety reserve. Virtual reservations and committed pages are reported separately.
* Cap process/task/thread/descriptor/port/stream/waiter/timer/mapping/queue counts. Validate low/high watermarks against stream/frame size so the configuration cannot deadlock permanently or require an impossible packet to fit.
* Generate both capability graph and **information-flow graph**. The UI process cannot access the BEAM release tree; BEAM cannot access display/input/assets; neither can enumerate ambient processes, streams, devices, or another process's handles.
* Reject duplicate names/IDs, dangling endpoints, direction mismatch, zero/overflow capacities, frame larger than usable channel capacity, invalid fixed descriptor, reserved-fd collision, impossible memory sum, capability escalation, cross-profile artifact mismatch, and unknown schema fields.
* The kernel consumes a compact length-delimited/checksummed/versioned boot-plan format with exhaustive parsing, checked arithmetic, hard element limits, and no string/path interpretation. The host-side compiler is the only permissive textual parser.
* Deterministic output includes normalized ordering and a declared build epoch; host paths, timestamps, map iteration, archive metadata, and machine identity cannot perturb the digest.

### Lifecycle boundary

The boot plan does **not** imply a general service manager. Worker-process restart and logical protocol reset are supported inside the living processes. Unexpected BEAM VM, fd-port owner, native service/renderer, or stream-endpoint loss is a terminal POC state requiring system reboot unless a separate future gate adds process relaunch and capability rebinding.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Define capability/resource IDs, limits, duplicate/conflict rules, compile-time validation, build-plan hash, and exact fd/handle provisioning.
