---
schema: "repo-plan/v1"
id: "RB-T-AUDIT0"
title: "Close architecture-readiness blockers before Gate 0"
type: "task"
state: "in_progress"
priority: "P0"
milestone: "RB-M-M0"
parent: null
depends_on: []
related: []
actor: "agent"
owner: "amp:T-01a05912-a43d-754e-84fc-d56536c31a76"
defer_until: null
evidence: []
x_legacy_id: "AUDIT-0"
x_linear_id: "ROB-800"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-800/audit-0-close-architecture-readiness-blockers-before-gate-0"
x_labels:
  - "ready-for-agent"
---

# RB-T-AUDIT0: Close architecture-readiness blockers before Gate 0

## Goal

Complete the outcome named by this record.

## Context

Use the linked project and milestone contracts.

## Deliverables

Produce the artifact named by the goal.

## Acceptance criteria

- [ ] All sections A–M have committed specifications, tests or executable
      probes, and evidence links.
- [ ] No P0-severity unknown remains hidden in prose.
- [ ] Every modified downstream ticket names the frozen contract it consumes.
- [ ] A clean remote Linux runner and the designated Apple Silicon Mac reproduce
      the applicable Gate 0 commands.
- [ ] `RB-G-GATE0` records Continue, Narrow, Pivot, or Stop and lists accepted
      residual risks.
- [ ] The user explicitly approves the Gate 0 decision.

## Verification

Run the verification required by the acceptance criteria.

## Evidence

Record durable repository evidence.

## Out of scope

Work beyond this record's goal and deliverables.

## Additional context

### Decision

This issue is a **hard blocker**. The project may execute Phase 0 feasibility
work, but it is not ready to begin M1 kernel implementation until every item
below is closed with reproducible evidence and Gate 0 explicitly accepts the
residual risk.

### Why this exists

The original plan is strong at the product and milestone level, but it omitted
several contracts that sit below every later ERTS, SMP, IPC, and GUI assumption.
QEMU can make an incomplete implementation appear healthy, so these requirements
must be frozen before kernel work rather than discovered opportunistically.

### A. Freeze the exact emulated platform

Produce a machine-readable platform contract and ADR that pins:

- a versioned QEMU `virt-*` machine, never the moving `virt` alias;
- QEMU binary/version/hash and complete TCG and HVF commands;
- explicit CPU model/properties and lowest-common-denominator feature mask;
- GIC version, PSCI conduit, generic timer, vCPU topology, RAM, physical-address
  width, 4 KiB page size, UART, RTC, RNG, GPU, input, and virtio transports;
- complete DTB dumps and normalized comparison between Linux/TCG and Apple
  Silicon/HVF;
- every intentional difference between the two runner profiles.

`AT_HWCAP` and `AT_HWCAP2` may advertise only features the kernel actually
enables, context-switches, and tests. Explicitly disposition FP/SIMD, LSE
atomics, SVE/SME, PAC/BTI, MTE, and any GNU property found in target ELF files.

### B. Freeze the exact ELF and process-entry contract

Inspect the pinned `beam.smp`, renderer, and C probes and record:

- ELF type (`ET_EXEC` versus static PIE), entry, load ranges, program headers,
  alignments, relocations, `PT_TLS`, `PT_GNU_STACK`, GNU properties, and
  absence/presence of `PT_INTERP`;
- target ABI and compiler feature set;
- complete initial stack layout and every auxv key/value, including `AT_PHDR`,
  `AT_PHENT`, `AT_PHNUM`, `AT_ENTRY`, `AT_PAGESZ`, `AT_RANDOM`, `AT_EXECFN`,
  `AT_SECURE`, IDs, and hardware-capability values;
- deliberate vDSO omission and resulting clock path;
- negative tests that reject unsupported ELF constructs before entering EL0.

The M1 loader must implement the inspected artifact contract, not a guessed
generic static-ELF subset.

### C. Prove the complete AArch64 execution context

Freeze and test the context-switch contract for:

- X0–X30, SP, ELR, SPSR, address-space identity, kernel stack, and preemption
  state;
- `TPIDR_EL0` and all TLS assumptions;
- FP/SIMD enable/trap policy, Q0–Q31, FPSR, and FPCR;
- signal save/restore of all admitted user state;
- a rule forbidding accidental FP/SIMD use in EL1 unless kernel state is
  explicitly managed.

Add alternating-task tests whose integer, TLS, and vector register patterns are
checked across timer preemption, syscall return, faults, signal delivery,
migration, and four-vCPU contention.

### D. Freeze cache and translation coherency

Specify and test:

- executable-page publication: populate while NX, required D-cache clean and
  I-cache invalidation, barriers, permission transition, and translation
  invalidation;
- ASID allocation, rollover/reuse, address-space switch, and stale-translation
  prevention;
- local and remote TLB shootdown for map, unmap, protect, exit, and address
  reuse;
- page-table update locking and the architectural barrier sequence;
- instruction tests that replace/publish code pages and prove every CPU executes
  the new bytes only after publication.

### E. Add the missing demand-paged memory design

Do not assume ERTS virtual reservations can be eagerly backed. Define and test:

- reservation versus committed physical memory;
- demand-zero faults for anonymous `mmap`/`brk`;
- VMA lookup/locking and fault-versus-`munmap`/`mprotect`/exit races;
- guard pages, overcommit policy, per-process commit limits, global no-swap OOM
  behavior, `ENOMEM` precedence, and failure atomicity;
- committed-memory accounting and post-exit conservation;
- the measured reservation/commit pattern of the exact target ERTS workload.

### F. Split and qualify the SMP substrate

Before declaring the scheduler SMP-safe, document and test:

- GIC distributor/redistributor/system-register setup and SGI/IPI delivery;
- memory-ordering model, atomic baseline, lock hierarchy, IRQ/preemption rules,
  and per-CPU ownership;
- secondary-CPU boot, remote enqueue/wakeup, migration, timer programming,
  idle/wakeup, shutdown, and TLB-shootdown IPIs;
- races among block, wake, timeout, signal, exit, migration, and CPU shutdown;
- model-based interleavings plus guest weak-memory stress, not host model tests
  alone.

### G. Add scheduler fairness and resource isolation

Freeze the kernel scheduling policy and observable accounting needed to prove
that ERTS cannot starve the renderer:

- priorities or weights, timeslice rules, migration policy, and runnable-queue
  invariants;
- per-process/thread CPU time, involuntary preemption, run-queue delay, and
  starvation counters;
- explicit tests with two normal BEAM schedulers, all admitted
  dirty/async/auxiliary threads, and a CPU-bound renderer heartbeat;
- a declared maximum renderer scheduling delay under the POC stress profile.

### H. Freeze the exact ERTS launch and native-thread budget

A `+S 2:2` flag is insufficient. The Phase 0 launch receipt must pin:

- complete argv, environment, cwd, boot variables, release root, code paths,
  boot/config files, descriptor table, locale, timezone, HOME/TMP behavior, and
  shutdown path;
- normal/online schedulers, dirty CPU schedulers, dirty IO schedulers, async
  pool, poll/check-I/O threads, timer and other auxiliary native threads;
- scheduler busy-wait settings and their effect on renderer responsiveness;
- disabled distribution/epmd, shell, networking, runtime mutation, writable
  crash dump, dynamic loading, NIFs, and hidden host-file fallbacks;
- twenty reproducible boots of the genuine Mix release on the target AArch64
  Linux reference environment.

Every observed thread and host interaction must map to `beam-host.yaml` and an
owning conformance test.

### I. Prove the no_std renderer/toolkit and license path in Phase 0

Build a real AArch64 no_std probe that exercises allocation, text/font
rendering, layout, hit testing, input dispatch, animation/timers, damage, and
one complete software-rendered frame using the intended toolkit API.

Record crate graph/features, generated code, TLS/libm/allocator/panic
assumptions, binary size, frame time, peak committed memory, and unsupported
features. Attach exact license texts and a written disposition for distribution
on a custom OS. Do not assume a desktop/mobile license grant covers this
platform. Select a permissively licensed fallback if the intended path cannot be
proven or accepted.

M5 must implement a frozen decision, not discover whether the toolkit can
compile.

### J. Freeze IPC sessions, action semantics, and restart ownership

Extend the protocol and kernel resource model with:

- boot ID, connection/session epoch, endpoint identity, monotonic model
  revision, patch base revision, action ID, acknowledgement, deduplication
  window, and resnapshot rules;
- explicit lossless classes for state-changing actions and explicitly
  lossy/coalescible classes for pointer motion and metrics;
- bounded retry/failure semantics without an unsupported exactly-once claim;
- strict ETF limits before allocation; fixed atom allowlist; no compressed
  terms; no untrusted atom creation; rejection of trailing data, partial frames,
  invalid lengths, duplicate fields, stale epochs, and out-of-order revisions;
- one framing owner only: the ERTS `{packet,4}` mechanism or the application
  codec, never both;
- kernel-owned lifecycle that creates a fresh endpoint pair and deterministic fd
  map when the port owner, ERTS process, or renderer dies;
- renderer and ERTS restart matrices proving stale descriptors/registrations
  cannot be reused.

### K. Add virtio DMA and reset safety

Before the GUI gate, define and test:

- DMA page allocation, pinning, ownership, address translation, alignment,
  lifetime, cache/barrier requirements, and cleanup;
- split-ring/packed-ring choice, descriptor-chain validation, queue bounds,
  interrupt suppression, lost interrupt recovery, and polling fallback;
- malformed or duplicate used entries, unexpected lengths, device reset during
  I/O, process death with in-flight buffers, and repeated reinitialization;
- capability separation: the renderer receives bounded display/input operations,
  not raw MMIO or unrestricted DMA authority.

### L. Freeze qualification methodology

Before long runs, define:

- runner matrix, accelerator, exact QEMU/CPU/machine profile, seed policy,
  warm-up, clock domain, sample size, timeout, failure/retry policy, and
  evidence retention;
- guest input-to-frame-flush latency separately from host-observed
  input-to-pixel latency;
- committed-memory envelope and an explicit post-warm-up slope bound instead of
  “no unbounded growth”;
- confidence interpretation for 100/1,000/10,000-trial claims;
- native AArch64/HVF or KVM long-stress runs plus TCG portability smoke, rather
  than treating a 12-hour TCG run as the only qualification;
- separate claims for deterministic image assembly from pinned artifacts and
  reproducible full source rebuilds.

### M. Resolve the Phase 0 dependency contradiction

`RB-T-P003` selects the compatible OTP/Elixir/toolchain set, while `RB-T-P002`
currently builds the reference app without depending on that selection. Resolve
by using a minimal smoke project during toolchain selection, then making the
final `runtime_lab` build and its evidence depend on the selected pair. No
reference trace may be accepted if it was produced by a different pair.

### Required primary-source receipt

The Gate 0 packet must include retrieval date, immutable tag/commit/version
where available, local digest, and the exact conclusion drawn from official
Erlang/OTP, Elixir, Rust target-spec, QEMU, Arm architecture, Linux arm64
UAPI/HWCAP, musl source, virtio, selected Rust crate, UI toolkit/license, SPDX,
and reproducible-build specifications.

Search-engine snippets or model recollection are not evidence.

### Completion rule

Do not close this issue because a design document exists. Close only when the
exact artifacts and probes pass and the downstream graph has been updated to
consume their versions.
