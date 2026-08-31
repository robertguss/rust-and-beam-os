---
schema: "repo-plan/v1"
id: "RB-T-P012"
title: "Prove the display/input path under Apple Silicon HVF and select MMIO or PCI"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P011"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-12"
x_linear_id: "ROB-694"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-694/p0-12-prove-the-displayinput-path-under-apple-silicon-hvf-and-select"
x_labels:
  - "ready-for-agent"
---
# RB-T-P012: Prove the display/input path under Apple Silicon HVF and select MMIO or PCI

## Goal

Demonstrate that the same AArch64 device strategy works on the required interactive Mac host and freeze the transport decision.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This is Phase 0 of an emulator-first AArch64 OS POC. The deliverable must run against the pinned project artifacts and preserve the own-kernel hypothesis. Host-side programs are scaffolding and evidence only; they do not satisfy the final POC.

Blocked by: RB-T-P011.

## Deliverables

* Run the exact bare-metal probe on Apple Silicon with QEMU/HVF.
* Test the MMIO candidate first; test virtio PCI through ECAM if graphics/input behavior or acceleration requires it.
* Compare device discovery, interrupts, DMA assumptions, display behavior, input behavior, and command-line differences with Linux/TCG.
* Write an ADR selecting MMIO or PCI, including rejected alternative, portability consequences, and exact runner profiles.

## Acceptance criteria

- [ ] The probe renders and accepts pointer input on Apple Silicon/HVF.
- [ ] The selected transport works on both HVF and TCG without conditional assumptions leaking above the platform/device layer.
- [ ] The ADR records exact QEMU commands and reproducible evidence from both hosts.
- [ ] Any accelerator-specific discrepancy has a bounded workaround or blocks RB-G-GATE0.

## Verification

* `just run-virtio-probe-hvf`
* `just test-virtio-probe-hvf`
* `just compare-virtio-probes`

## Evidence

* Run ten HVF boots and the same scripted input sequence used under TCG.
* Compare screenshots and normalized input/frame counters.
* Attach the Mac host/QEMU receipt and selected-transport ADR.

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

* Run with an exact QEMU digest and a versioned `virt-X.Y` machine. Record both a semantic CPU profile and the Apple Silicon/HVF `host` profile; do not pretend `-cpu host` and a TCG CPU model expose identical features.
* Treat `virtio-gpu-pci` as the primary candidate unless the measured HVF result disproves it. A transport is selected only after TCG/HVF feature negotiation, reset, input, screenshot, and present-completion traces agree at the declared semantic level.
* Compare DTB/PCI inventory, GIC behavior, timer/counter behavior, CPU/HWCAP implications, device features, pixel format/stride, and event codes—not screenshots alone.
* Feed results to RB-T-P014, RB-T-P015, and RB-T-P016. If one transport cannot support both intended accelerated runners, freeze separate profiles with explicit portability cost or stop before kernel code depends on it.
* Preserve raw QMP, serial, DTB, PCI, input, frame, and host hardware/macOS evidence for every failed attempt; no manual-only GUI success satisfies the issue.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Freeze exact Mac/QEMU frontend/device commands and semantic parity; separate transport, GPU protocol, and display/input frontend decisions.
### Normative readiness correction — 2026-08-30

Freeze and test the complete VirtIO device-status, reset, feature-negotiation, FEATURES_OK, VERSION_1, queue, descriptor, barrier, DMA, interrupt, error, timeout, and teardown semantics for the pinned crate/device/transport. Compilation is not conformance evidence. A missing required feature or incorrect reset/error path blocks the device decision.
