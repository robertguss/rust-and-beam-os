---
schema: "repo-plan/v1"
id: "RB-T-P011"
title: "Prove bare-metal virtio display and pointer input under Linux TCG"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P003"
  - "RB-T-P001"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-11"
x_linear_id: "ROB-696"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-696/p0-11-prove-bare-metal-virtio-display-and-pointer-input-under-linux"
x_labels:
  - "ready-for-agent"
---
# RB-T-P011: Prove bare-metal virtio display and pointer input under Linux TCG

## Goal

Prove the candidate QEMU display/input path independently of the future kernel and BEAM integration.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P001, RB-T-P003.

## Deliverables

* Create a tiny independent `no_std` AArch64 probe using the pinned `virtio-drivers` crate and QEMU `virt` device tree.
* Discover rather than hard-code device locations.
* Initialize the candidate virtio GPU transport, draw a changing test pattern and cursor, present frames, and receive pointer press/motion events.
* Emit structured serial milestones and input/frame counters; support a headless QMP-driven pass/fail path.

## Acceptance criteria

- [ ] The probe boots under remote Linux with TCG from one documented command.
- [ ] The framebuffer visibly changes and pointer events are recorded with correct coordinates/buttons.
- [ ] QMP can capture a screenshot containing stable landmarks.
- [ ] No semihosting or host framebuffer bridge is used in the acceptance run.
- [ ] The exact QEMU machine, CPU, memory, device, and transport arguments are recorded.

## Verification

* `just run-virtio-probe-tcg`
* `just test-virtio-probe-tcg`

## Evidence

* Run ten TCG boots and scripted input actions.
* Save a screenshot, serial log, device tree, QEMU version, and command.
* Record all crate features and unsafe integration points.

## Out of scope

* Do not implement a Linux or Android guest.
* Do not add networking, writable persistent storage, dynamic linking, third-party NIFs, or phone hardware.
* Do not weaken an acceptance test merely to make the spike pass.

## Additional context
### Completion rule

Do not mark this issue Done until every acceptance item has a linked test, trace, build receipt, ADR, or other durable evidence. If an assumption fails, stop and create or update the relevant decision record instead of silently changing scope.
### Learning checkpoint

Explain the mechanism, its governing invariant, one plausible failure mode, and how the saved evidence distinguishes success from an accidental demo.
### Readiness-audit correction — 2026-08-30

* Use the provisional versioned `virt-X.Y`, explicit AArch64 CPU, explicit GIC, explicit accelerator, and explicit device list from RB-T-P014; never rely on the unversioned `virt` default or the 32-bit default CPU.
* Discover every device address/interrupt/PCI window from the DTB/ECAM. QEMU documents only flash and RAM addresses as safe to hard-code across versions.
* Probe `virtio-gpu-pci` as the primary portable accelerated candidate because QEMU documents it as the recommended Arm `virt` display and the only choice that works correctly with KVM; probe MMIO only as an explicitly separate fallback if it materially simplifies TCG.
* Record negotiated virtio features, queue sizes, DMA/cache/barrier rules, pixel format, dimensions, stride, buffer ownership, input event codes, reset generation, and present completion—not merely a screenshot.
* Include malformed descriptors, queue exhaustion, device reset, interrupt loss/duplication, DMA-bound checks, and non-coherent-memory assumptions in the probe evidence.
* This issue supplies evidence to RB-T-P014/RB-T-P015/RB-T-P016; it does not independently freeze the final platform or toolkit.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Add full VirtIO feature/status/reset/queue/barrier/DMA/error contract and audit the pinned crate’s VERSION_1 behavior.
### Normative readiness correction — 2026-08-30

Freeze and test the complete VirtIO device-status, reset, feature-negotiation, FEATURES_OK, VERSION_1, queue, descriptor, barrier, DMA, interrupt, error, timeout, and teardown semantics for the pinned crate/device/transport. Compilation is not conformance evidence. A missing required feature or incorrect reset/error path blocks the device decision.
