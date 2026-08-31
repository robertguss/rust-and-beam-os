---
linear_url: "https://linear.app/robert-guss/project/rust-beam-mobile-os-poc-9976f5ac2dba"
title: "Rust + BEAM Mobile OS POC"
kind: "project"
exported_at: "2026-08-31T13:33:41.658Z"
---
# Mission

> **Implementation readiness — 2026-08-30:** Phase 0 evidence work only is authorized. M1–M6 implementation is gate-blocked. GATE-0 has not passed and must explicitly record **Authorize M1** before kernel work begins.

Build and falsify a proof-of-concept mobile-oriented operating system with a project-owned Rust kernel, standard upstream Erlang/OTP and Elixir, and one interactive Rust-rendered/Elixir-controlled GUI.

# Locked target

* Guest CPU/platform: AArch64 QEMU using a Gate-0-frozen versioned `virt-X.Y` machine, explicit CPU/GIC/device profile, and separate TCG/KVM/HVF evidence
* Build hosts: reproducible remote Linux VMs; x86_64 or AArch64
* Interactive host: Apple Silicon Mac using QEMU/HVF
* Kernel: project-owned modular monolithic Rust kernel; no Linux, Android, Redox, or other guest kernel
* Runtime: upstream Erlang/OTP running a real Elixir Mix release inside the guest
* Runtime profile: non-JIT first; SMP with two normal BEAM schedulers required for acceptance
* UI: Rust renderer in a separate EL0 process; Elixir owns feature state and behavior
* Interop: bounded, versioned ETF over pre-opened kernel IPC exposed to ERTS as fd ports
* Composition: AI-assisted source/manifest changes produce a new immutable image; no live OS mutation
* Schedule: no deadline; evidence gates control progress

# Completion definition

The POC is complete only when QEMU directly boots the custom kernel, the kernel runs isolated Rust renderer and ERTS processes, ERTS boots a genuine Mix release with SMP, pointer input crosses into Elixir, Elixir updates the view model, and an intentionally crashing supervised worker visibly restarts while the renderer's native animation remains responsive.

A host-side bridge is allowed only as development scaffolding. It does not satisfy acceptance.

# Operating rules

1. Implement one evidence-bounded slice at a time.
2. Every issue is executable without access to the originating conversation.
3. Tests and observability are deliverables, not cleanup.
4. Unknown syscalls and protocol states fail loudly.
5. Prefer zero OTP source patches; semantic runtime patches fail the central hypothesis.
6. Later milestones remain blocked until the preceding gate records Continue, Pivot, Narrow, or Stop.
7. Store commands, hashes, measurements, traces, screenshots, and decision records as durable evidence.
8. Do not introduce networking, writable persistent storage, phone hardware, Android compatibility, dynamic linking, third-party NIFs, or on-device code generation into this POC.

# Project structure

Seven evidence-gated milestones correspond to architecture Phases 0–6. Each phase has implementation-sized issues, an explicit gate issue, measurable acceptance criteria, dependencies, and stop/pivot conditions. The project stays Planned and undated until Phase 0 evidence justifies implementation.
