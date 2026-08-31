---
schema: "repo-plan/v1"
id: "RB-T-P014"
title: "Freeze the versioned QEMU machine, CPU, auxv/HWCAP, page-size, cache, and atomics baseline"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M0"
parent: null
depends_on:
  - "RB-T-P003"
  - "RB-T-P006"
  - "RB-T-P012"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P0-14"
x_linear_id: "ROB-777"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-777/p0-14-freeze-the-versioned-qemu-machine-cpu-auxvhwcap-page-size-cache"
x_labels:
  - "ready-for-agent"
---
# RB-T-P014: Freeze the versioned QEMU machine, CPU, auxv/HWCAP, page-size, cache, and atomics baseline

## Goal

Eliminate hidden CPU and machine-model variability before the kernel, musl personality, and ERTS host contract are implemented.

## Context

[Architecture & Validation Plan](<../architecture.md>)

Blocked by: RB-T-P003, RB-T-P006, RB-T-P012.

Blocks: RB-T-P008, RB-T-P013, RB-G-GATE0.

## Deliverables

* Select and pin an exact QEMU release and a **versioned** Arm `virt-X.Y` machine type.
* Select explicit CPU models for Linux/TCG and macOS/HVF, or document a deliberately different HVF `host` profile; never treat `-cpu max` as an invariant ABI.
* Freeze GIC version, vCPU count, RAM, page size, counter frequency assumptions, endianness, VA/PA widths used by the POC, and device transports.
* Capture the target AArch64 Linux reference values for `AT_PAGESZ`, `AT_HWCAP`, `AT_HWCAP2`, relevant CPU ID fields, cache-line sizes, and whether LSE atomics are exposed.
* Define the exact subset the custom compatibility personality will advertise. Advertise no feature the kernel cannot safely preserve across context switches and signals.
* Pin Rust `target-cpu`/`target-feature` policy for kernel and native userspace. Record whether kernel code uses `aarch64-unknown-none` or soft-float and why.
* Produce machine-readable `platform-baseline.toml` plus a human-readable ADR and QEMU command manifests.

## Acceptance criteria

- [ ] Every runner uses an exact QEMU binary digest, versioned `virt-X.Y`, explicit accelerator, explicit CPU model, explicit GIC, and explicit device list.
- [ ] The Linux reference auxv/HWCAP values and guest-advertised values are listed bit-for-bit with rationale.
- [ ] `HWCAP_FP`/`HWCAP_ASIMD` are advertised only after the FP/SIMD context obligation is recorded; `HWCAP_ATOMICS` is advertised only if the selected CPU, toolchain, kernel atomics, and ERTS build agree.
- [ ] TCG and HVF differences are explicit; they may be separate semantic/performance profiles but cannot silently share incompatible baselines.
- [ ] A QEMU, machine, CPU, target-feature, page-size, or HWCAP drift causes the build or test harness to fail before guest execution.
- [ ] The chosen display transport follows the selected accelerator evidence; `virtio-gpu-pci` is the default candidate because QEMU documents it as the portable accelerated option.

## Verification

* `just platform-baseline-reference`
* `just platform-baseline-tcg`
* `just platform-baseline-hvf`
* `just verify-platform-baseline`

## Evidence

* Run a reference AArch64 Linux probe that records auxv, CPU features, cache geometry, page size, timers, and atomics.
* Run a minimal bare-metal probe on TCG and HVF and compare the declared platform contract.
* Deliberately change one QEMU machine/CPU/feature and prove the drift guard fails.
* Store exact commands, JSON output, QEMU help output, DTB inventories, binary hashes, and ADR.

## Out of scope

* Supporting multiple guest ABIs, arbitrary QEMU releases, SVE/SME/MTE, heterogeneous CPUs, hotplug, or physical phone hardware.
* Claiming TCG and HVF are performance-equivalent.
* Advertising optional CPU features merely because one host happens to expose them.

## Additional context
### Why this is a blocker

QEMU's unversioned `virt` machine and `-cpu max` may change behavior or exposed features across QEMU releases. AArch64 userspace also selects behavior from the auxiliary vector, including `AT_HWCAP`/`AT_HWCAP2`; the Rust hard-float bare-metal target assumes FP/AdvSIMD. A vague “AArch64 QEMU virt” target is therefore not a reproducible ABI.
### Completion rule

Done means the POC has one reproducible semantic CPU/machine contract and any runner-specific differences are explicit, testable, and unable to drift silently.
### Learning checkpoint

Explain why QEMU machine versioning, auxv/HWCAP, the Rust target ABI, FP/SIMD state, and ERTS/musl code-path selection must be treated as one contract.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Keep. Change PCI wording from proven portable to default candidate pending TCG/HVF proof; freeze DTB randomness and entropy policy.
### Normative readiness correction — 2026-08-30

Treat `virtio-gpu-pci` as the default candidate, not proven portable, until explicit TCG and HVF evidence passes. Freeze QEMU DTB randomness deliberately—normally `dtb-randomness=off`—and source production entropy only through the declared path.
