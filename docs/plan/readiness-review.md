---
linear_url: "https://linear.app/robert-guss/document/implementation-readiness-review-and-linear-remediation-bundle-816e754de15f"
title: "Implementation Readiness Review & Linear Remediation Bundle"
kind: "document"
exported_at: "2026-08-31T13:33:41.658Z"
---
# Rust + BEAM Mobile OS POC

## Implementation Readiness Review and Linear Remediation Bundle

**Review date:** August 30, 2026 (America/New_York)
**Linear snapshot:** 109 issues across M0–M6, including 20 high-priority issues added while this audit was underway
**Reviewed:** project brief, architecture/validation document, every current issue, milestone sequencing, gate criteria, labels, parent/child structure, and current primary-source evidence for OTP, Elixir, musl, QEMU, Rust/AArch64, VirtIO, Slint, Linux ABI behavior, and close prior art.

---

# 1. Executive verdict

## Overall decision: **NO-GO for kernel implementation**

The project is **not ready to begin M1 kernel implementation** and is not ready to be handed to autonomous implementation agents as a whole.

## Authorized work: **GO for Phase 0 evidence work only**

The following work may begin now:

 1. repository/evidence scaffolding;
 2. the Linux `runtime_lab` reference application;
 3. exact toolchain/source pinning;
 4. target ERTS static-artifact production and inspection;
 5. authoritative AArch64 Linux execution;
 6. Mix-release pairing;
 7. host-contract discovery;
 8. protocol conformance work;
 9. TCG/HVF device and Slint probes;
10. runner benchmarking and prior-art reproduction.

**GATE-0 has not passed.** It is a real evidence gate, not a documentation checkbox. No M1 work should start until all mandatory Gate 0 conditions have durable artifacts and the human gate records **Authorize M1**.

## Honest quality assessment

This is a strong architecture concept and an unusually thoughtful research plan. It correctly identifies the hardest problem: not “Rust versus Elixir,” but the semantic depth of the musl/ERTS host contract—threads, futexes, signals, VM, file descriptions, readiness, time, entropy, and process teardown.

It is still not implementation-ready because:

* planned tests are not evidence that assumptions hold;
* several issue descriptions and relations contradict one another;
* some fundamental kernel policies remain undecided;
* many tickets are too large to be self-contained implementation units;
* the workflow marks gate-blocked future work as `ready-for-agent`;
* the architecture document has not been reconciled with the audit corrections and new tickets.

A good plan can still be a no-go. In this case, stopping at Gate 0 is exactly what the plan was designed to do.

---

# 2. Readiness by milestone

| Milestone | Readiness | Decision | Principal reason |
| -- | -- | -- | -- |
| M0 — De-risk Artifacts & Contracts | **Executable with repairs** | Start only this milestone | The work is investigative. New P0-14–P0-17 materially improve it, but several issue edits and label changes remain. |
| M1 — Bootable Rust Kernel Spine | **Not ready** | Block | P1-08/P1-14 dependency inversion, missing single-core IRQ/locking contract, undecided user-copy recovery, incorrect EL terminology, and oversized VM/scheduler tickets. |
| M2 — Musl & BEAM Host Contract | **Not ready** | Block | New atomic/SMP/thread/signal/stream/poll/time/entropy children make the decomposition credible, but none is proven; VM splitting, robust-list scope, realtime policy, dependency cleanup, and gate-aware labels remain. |
| M3 — Upstream ERTS Inside Custom OS | **Not ready** | Block | Depends on unproven M0–M2; concurrency proof and memory-stability criteria remain underspecified. |
| M4 — Real Elixir Release & Rust IPC | **Not ready** | Block | Impossible fd-driver criterion, ambiguous “durable” state, protocol bounds, and exact backpressure/acceptance semantics need correction. |
| M5 — Interactive Rust GUI Proof | **Not ready** | Block | No frozen display-surface/present ABI; toolkit decision ownership is duplicated; latency and metrics ownership are ambiguous. |
| M6 — Qualification, Productivity & Decision | **Not ready** | Block | Statistical rules are not frozen; AI exercises can invalidate the canonical image/provenance unless isolated. |

---

# 3. What the current Linear revisions successfully fixed

During this audit, the Linear project gained twenty high-priority issues and multiple appended “readiness-audit” corrections. These additions are substantive, not cosmetic:

* **P0-14** freezes the versioned QEMU/CPU/auxv/HWCAP/cache/atomic baseline.
* **P0-15** proves the actual `no_std` Slint path and forces an explicit license decision.
* **P0-16** benchmarks TCG/KVM/HVF rather than pretending the runners are interchangeable.
* **P0-17** investigates Tyn, the closest current public Rust-kernel/upstream-ERTS prior art.
* **P1-13** adds the missing FP/AdvSIMD context-isolation obligation.
* **P1-14** adds executable-page cache maintenance and single-core TLB coherency.
* **P2-00** adds an explicit AArch64 atomic/memory-ordering foundation.
* **P2-05a–c** split CPU bring-up, SMP scheduling/migration, and acknowledged TLB shootdowns.
* **P2-06a–b** split thread creation from futex-dependent exit/join/reclamation.
* **P2-10a–b** split bounded stream/descriptor lifecycle from `poll`/`ppoll` registration and close/reuse races.
* **P2-09a–c** split signal state/selection, AArch64 frames/`rt_sigreturn`, and interruption/restart/cancellation races.
* **P2-11a–c** split monotonic deadlines/timers, virtio-rng/`AT_RANDOM`, and bounded platform identity/query behavior.

Those changes move the project from “plausible but dangerously incomplete” to “credible research program.” They do **not** make Gate 0 pass, and they do not close the remaining contradictions below.

---

# 4. Critical blocker register

## F-01 — The static ERTS artifact is still an experiment, not an established input

**Status:** Partially corrected in <issue id="8487cc59-d6ea-45c4-a581-dd4a428639dd" href="tasks/p0-05.md">ROB-688</issue>; evidence absent.

“Static `beam.smp`” must mean all of the following for the exact produced artifact:

* no `PT_INTERP`;
* no undeclared `DT_NEEDED`;
* exact `ET_EXEC` versus static-PIE/`ET_DYN` shape recorded;
* all relocations and TLS forms inventoried;
* built-in drivers and statically linked native components inventoried;
* no runtime-loaded application NIF, dynamic driver, or native library;
* release closure inspected for `.so` files and load attempts;
* compiler CPU features, LSE/outline atomics, page size, and HWCAP assumptions match P0-14.

The loader must implement the artifact actually produced. It must not assume a conventional static executable and discover static PIE later.

**Required action:** Keep the appended <issue id="8487cc59-d6ea-45c4-a581-dd4a428639dd" href="tasks/p0-05.md">ROB-688</issue> correction and add a sealed artifact-closure check covering the entire Mix release tree, not only `beam.smp`.

---

## F-02 — Trace equivalence is not contract completeness

**Status:** Partially corrected in <issue id="a0789a32-63c5-4bcb-aea1-adec3fa938be" href="tasks/p0-08.md">ROB-690</issue>; P0-04 remains too happy-path oriented.

Two identical traces prove repeatability for those paths. They do not prove:

* timeout paths;
* cancellation points;
* signal interruption and restart;
* thread-creation rollback;
* thread exit/join races;
* allocation/copy faults;
* close/read/write/poll races;
* malformed boot/release inputs;
* optional ERTS branches;
* rare shutdown/error behavior.

**Required action:** Add source-to-contract coverage and coverage-guided fault scenarios to P0-04/P0-08. Every source-inspected host interaction must be either exercised, proven unreachable by the frozen build, or retained as an explicitly unproven Gate 0 risk.

---

## F-03 — QEMU `virt` is not a stable ABI unless versioned

**Status:** Substantially addressed by P0-14.

The final baseline must pin:

* QEMU binary digest;
* versioned `virt-X.Y`, never bare `virt`;
* accelerator and explicit CPU profile;
* GIC version;
* RAM/vCPU count;
* device list and transports;
* page size, VA/PA policy, counter assumptions;
* auxv/HWCAP/HWCAP2;
* Rust target features and emitted atomic strategy.

**Remaining correction:** P0-14 must not claim that `virtio-gpu-pci` is proven “portable” merely because QEMU recommends it. It is the **default candidate**, subject to explicit TCG and HVF proof.

For reproducible qualification, set QEMU DTB randomness deliberately—normally `dtb-randomness=off`—and provision runtime entropy through the declared entropy path rather than accidental DTB seeds.

---

## F-04 — AArch64 hard-float creates a kernel FP/AdvSIMD obligation

**Status:** Addressed by P1-13, but its gate sequencing is contradictory.

The Rust `aarch64-unknown-none` hard-float target assumes FP/AdvSIMD. Kernel context switching must preserve V0–V31, FPCR, and FPSR before general hard-float EL0 programs are accepted.

**Required relation correction:**

* Gate 1 should require **single-CPU** FP/AdvSIMD isolation.
* Cross-CPU migration evidence belongs to P2-05b/Gate 2.
* Remove CPU migration from P1-13’s Gate 1 completion requirement.
* P1-08 may test parser/loading early with a deliberately no-FP assembly payload, but a normal hard-float Rust process cannot count as complete evidence until P1-13 passes.

---

## F-05 — P1-08 and P1-14 currently form a semantic dependency inversion

**Status:** Open and blocking.

P1-08 says ELF text is staged writable+NX and published RX through P1-14. Yet the current relation has P1-08 **blocking** P1-14.

**Required relation correction:**

1. Remove `P1-14 blocked by P1-08`.
2. Make P1-14 depend on P1-05 only.
3. Make P1-14 block the execute/publish portion of P1-08.
4. Prefer splitting P1-08:
   * **P1-08a — Parse, validate, allocate, and stage a static AArch64 ELF**
   * **P1-08b — Publish executable segments and enter the isolated EL0 process**
5. P1-08b is blocked by P1-08a, P1-13, and P1-14.

A cache-maintenance API can be tested with copied code pages without needing the full ELF loader first.

---

## F-06 — M1 lacks a single-core IRQ/preemption/locking contract

**Status:** Open and blocking.

P2-00 correctly defines SMP memory ordering, but M1 already has:

* timer interrupts;
* preemption;
* wait queues;
* allocator/VM state;
* process exit;
* user-copy faults;
* tracing.

M1 needs explicit rules for:

* IRQ nesting;
* preemption-disable nesting;
* interrupt-safe versus task-only locks;
* lock ordering;
* sleeping while locked;
* allocation in IRQ context;
* exception/IRQ stack ownership and guards;
* scheduler reentrancy;
* compiler ordering on single CPU;
* wake-before-sleep linearization.

**Required action:** Create P1-00 from the paste-ready issue in section 8.

---

## F-07 — User-copy safety names the problem but does not select a mechanism

**Status:** Open and blocking.

P1-09 must lock one design. The recommended POC design is:

* validate user range and access intent;
* hold an address-space lifetime/read lock across the copy;
* use an architecture exception-fixup table or guarded copy primitive that converts EL1 data aborts during approved copy sites into `EFAULT`;
* define exact partial-copy behavior;
* forbid arbitrary kernel pointer dereference of user addresses;
* forbid sleeping unless the address-space lifetime protocol explicitly allows it;
* serialize teardown/unmap against copies;
* test unmap/protect/exit races.

Page pinning is unnecessary for ordinary bounded copies if the address-space lock and fault-fixup discipline are correct. It may be added later for asynchronous I/O.

---

## F-08 — SMP ordering, scheduling, and shootdowns are now much better—but remain gate-blocked

**Status:** Substantially addressed by P2-00 and P2-05a–c.

These new issues should remain. Required refinements:

* P2-00 must not be used as a reason to defer M1’s single-core IRQ/locking rules.
* P2-05c must block every multi-threaded operation that can unmap, reprotect, destroy, or reuse address spaces.
* ASID wrap/reuse must be tested with a deliberately small test ASID space.
* failed shootdowns must fail safe; never free/reuse the affected frame, page table, or ASID.

---

## F-09 — Thread lifecycle decomposition is now credible

**Status:** Substantially addressed by P2-06a/P2-06b.

Required relation refinements:

* P2-08 robust-list cleanup must be explicitly blocked by P2-06b or integrated as its required cleanup hook.
* Gate 2 must require robust-list behavior only if the pinned musl/ERTS contract actually registers or depends on it.
* Unsupported `clone` modes must fail before partial state becomes visible.
* Exact musl version/source and call layout are the oracle; do not implement generic Linux `clone`.

---

## F-10 — Signal work is now credibly decomposed

**Status:** Substantially addressed by P2-09a/P2-09b/P2-09c.

The new children correctly separate:

1. process/thread signal dispositions, masks, pending state, and target selection;
2. AArch64 signal frames, alternate stacks, FPSIMD context, synchronous faults, and `rt_sigreturn`;
3. interruption, restart, cancellation, deadline, partial-I/O, futex, and poll race semantics.

**Required refinements:**

* child dependencies should point to completed implementation children rather than relying only on tracking-parent completion;
* P2-09b must depend on the corrected executable/EL0 entry ticket P1-08b after P1-08 is split;
* every signal/flag/frame extension not in the pinned contract must fail closed;
* Gate 2 must require byte-level AArch64 fixtures, forged-frame negative tests, and one-terminal-outcome conservation.

## F-11 — Time, entropy, and platform queries are now mostly decomposed

**Status:** Substantially addressed by P2-11a/P2-11b/P2-11c.

P2-11a correctly centralizes absolute monotonic deadlines and timer cancellation. P2-11b now supplies an explicit virtio-rng/`AT_RANDOM` path and separates deterministic test mode from production/qualification. P2-11c centralizes guest identity and prevents host leakage.

**Remaining correction:**

* If the frozen ERTS/musl release actually requests `CLOCK_REALTIME`, P2-11a must name and test one source—preferably the QEMU `virt` PL031 RTC or an explicitly provisioned immutable boot epoch. It may not quietly derive civil time from monotonic elapsed time.
* Freeze QEMU DTB randomness deliberately. Production entropy comes from P2-11b; deterministic test mode is structurally rejected by production/qualification preflight.
* Ensure P2-10b and P2-09c depend on the **completed P2-11a child**, not merely a tracking parent whose entropy/query children are unrelated to each wait deadline.
* Missing entropy remains fail-closed and never falls back to timer-derived bytes.

## F-12 — VirtIO use needs a protocol-compliance contract, not only a crate choice

**Status:** Open and blocking.

Patch P0-11, P0-12, and P5-01 to require:

* exact transport and VirtIO version;
* device-status state machine and reset;
* feature negotiation and `FEATURES_OK` verification;
* disposition of `VIRTIO_F_VERSION_1`;
* queue size/alignment/descriptor validation;
* memory and DMA ordering;
* interrupt acknowledgement;
* device error/reset/timeout behavior;
* pinned pages and device ownership;
* process/device teardown;
* malformed/unexpected device response tests.

Do not infer protocol conformance from `virtio-drivers` compiling. Audit the pinned crate/version and patch, replace, or narrow if required behavior is absent.

---

## F-13 — P4-06 contains an impossible “no linked-in driver” requirement

**Status:** Open and directly incorrect.

`Port.open({:fd, In, Out}, ...)` is provided by the upstream built-in fd port driver. Therefore “no linked-in driver” contradicts the chosen design.

**Replace with:**

> The final artifact uses the unchanged upstream built-in fd port driver. It loads no project-specific or dynamically loaded port driver, NIF, or native extension.

Also configure and test:

* `{packet, 4}`;
* `{packet_size, 65536}` or the exact frozen limit;
* bounded port/message-queue busy limits;
* port ownership and lifecycle;
* closure in either direction;
* busy/backpressure behavior;
* no duplicate framing layer.

The kernel transports bounded bytes. It does not parse ETF or add another packet prefix.

---

## F-14 — The display surface and present ABI is missing

**Status:** Open and blocking M5.

The plan says the renderer “draws and presents,” but does not decide how pixels cross the process/kernel/device boundary.

**Recommended POC lock:**

* kernel allocates two page-backed BGRA/RGBA surfaces;
* surfaces are mapped writable+NX into the renderer only;
* kernel owns virtio resources, queues, DMA/pinning, scanout, interrupts, and reset;
* renderer writes only the buffer it currently owns;
* `display_present(surface, generation, frame_seq, dirty_rect)` validates bounds and ownership;
* kernel performs transfer/flush and signals completion;
* ownership states are explicit: `free → rendering → queued → displayed/released`;
* renderer cannot overwrite a queued buffer;
* ERTS receives no display mapping;
* renderer crash or device reset quiesces queues before backing pages are reclaimed.

Create P5-00 from section 8 and make it block P5-01/P5-03.

---

## F-15 — ETF “safe” decoding is necessary but not sufficient

**Status:** Partially addressed; strengthen P0-09/P0-10/P4-05/P4-07.

The v1 protocol must define:

* exactly one 4-byte length prefix per direction;
* 64 KiB maximum framed size;
* compressed terms rejected, or declared uncompressed size bounded before allocation;
* maximum nesting depth;
* tuple/list/map arity;
* binary/string lengths;
* integer bounds;
* atom allowlist with no new atom creation;
* trailing-byte policy;
* unsupported tags;
* canonical version/envelope shape;
* sequence wrap/reconnect behavior;
* schema validation after ETF decoding;
* maximum state/card/action counts;
* fuzz and differential tests against Erlang.

`binary_to_term(..., [safe])` protects some runtime resources. It does not validate application meaning.

---

## F-16 — “Accepted action” and metrics ownership are ambiguous

**Status:** Open.

Define **accepted** as:

> The event is durably admitted into the bounded Elixir application transition path for the current protocol session and will produce exactly one terminal response: applied, rejected, failed, or unresolved-by-disconnect.

A write into a pipe or enqueue in the renderer is not “accepted.”

For metrics, use two namespaces:

* Elixir is authoritative for **feature/application state**.
* Renderer/kernel are authoritative for **native telemetry and heartbeat**.

The renderer may compose these for display, but kernel metrics should not be sent to Elixir merely to be echoed back unless Elixir policy actually consumes them. Prevent two sources of truth and telemetry feedback loops.

---

## F-17 — “Event-to-pixel” is an overclaim

**Status:** Open.

Guest timestamps can ordinarily prove:

* input received;
* Elixir transition;
* renderer model applied;
* redraw complete;
* virtio transfer/flush/present command completed.

They do not prove when the human-visible host window emitted the pixel.

Rename the core metric to **event-to-present-completion**. A host-observed event-to-visible metric is optional and must include host capture instrumentation, clock correlation, and a stated error bound.

The 50 ms p95 / 100 ms p99 goals should remain provisional product targets until P0-16 calibrates the exact Mac, resolution, display frontend, QEMU profile, instrumentation overhead, and completion proxy.

---

## F-18 — “Memory stabilizes” and “no unexplained outliers” are not executable criteria

**Status:** Open across P3-09, P5-11, P6-01, P6-02, and P6-03.

Before qualification, P6-01 must freeze:

* warm-up duration;
* sample interval;
* observation windows;
* discrete resource exactness;
* memory slope estimator;
* confidence interval;
* acceptable projected growth;
* outlier rule;
* invalid-run classification;
* retry policy;
* host interruption policy;
* first-failure preservation.

Recommended policy:

* exact equality for tasks, descriptors, handles, ports, queues, waiters, and mappings after each completed cleanup cycle unless a named cache is designed to remain;
* memory assessed after a frozen warm-up with a robust slope and confidence interval;
* any statistically supported positive slope that projects beyond the frozen budget is a failure;
* outliers are investigated and classified, never deleted;
* no automatic retry converts a failed run to pass.

---

## F-19 — AI exercises can invalidate canonical qualification and provenance

**Status:** Open in M6.

Freeze one canonical qualification commit/image in P6-01.

Exercises A, B, and C must run in isolated branches/worktrees from that commit and produce independent image/build IDs. They do not mutate the canonical result.

If an exercise change is retained:

1. merge it explicitly;
2. freeze a new canonical image;
3. rerun P6-05 reproducibility/SBOM/license checks;
4. rerun every qualification whose behavior or artifact changed.

---

## F-20 — Workflow labels contradict the gate model

**Status:** Open and operationally dangerous.

Nearly every future issue is labeled `ready-for-agent` even though the project explicitly says later milestones remain blocked by human gates.

**Required label policy:**

* `ready-for-agent`: dependencies complete and current gate authorizes execution;
* `spec-complete`: self-contained specification exists but execution is not authorized;
* `gate-blocked`: prior human gate not passed;
* `tracking`: parent/roll-up issue; never delegated as implementation;
* `ready-for-human`: gate/review/decision.

Apply `gate-blocked` + `spec-complete` to M1–M6 now. Remove `ready-for-agent` from those issues. After each gate, promote only the next dependency-ready slice.

---

## F-21 — AArch64 privilege-transition wording is wrong in repeated learning checkpoints

**Status:** Open.

Bulk replace:

> Explain reset-to-EL0 control flow...

with:

> Explain the possible QEMU boot entry at EL1 or EL2, normalization into EL1, and the later exception return from EL1 into an isolated EL0 process.

The kernel does not “reset to EL0.” EL0 is entered later for userspace.

---

## F-22 — Several issues remain too large for safe AI implementation

**Status:** Open.

Continue the successful P2-05/P2-06/P2-09/P2-10/P2-11 tracking/child pattern for:

* P1-05 VM/address spaces;
* P1-06 timer/preemption/wait queues;
* P2-04 VMA/mapping syscalls;
* P5-01 virtio GPU;
* P5-03 renderer/capabilities/display ABI.

Recommended child split titles are in section 9.

---

# 5. Exact architecture-document corrections

The architecture document is still the original proposed plan. Append or incorporate the following normative corrections.

## 5.1 Status and authorization

Replace:

> Status: Proposed architecture

with:

> Status: Audited research architecture. Phase 0 investigation is authorized. Kernel implementation remains blocked until GATE-0 records Authorize M1.

## 5.2 Candidate versions

Clarify that current OTP/Elixir/Rust/QEMU/musl releases are **candidate inputs**, not compatibility proof. Exact tags, source hashes, compiler outputs, generated configuration, QEMU binary digest, and release closure become frozen only after P0 probes pass.

## 5.3 Static runtime wording

Replace broad “statically linked upstream `beam.smp`” claims with:

> An exact inspected AArch64-musl ERTS artifact with no dynamic interpreter or unapproved runtime-loaded native dependency. Its ELF type, relocations, TLS model, built-in drivers/native components, and full release closure are frozen in the Gate 0 evidence.

## 5.4 Host-contract discovery

Add:

> Trace equivalence is not completeness. Contract discovery combines dynamic traces, frozen-build source inspection, fault-injected error paths, and generated positive/negative/concurrency tests. Every source-visible host interaction is exercised, proven unreachable, or retained as an explicit gate risk.

## 5.5 Platform baseline

Replace unversioned `virt` with a versioned machine contract and distinguish semantic profiles:

* Linux TCG;
* Linux AArch64 KVM, when available;
* macOS Apple Silicon HVF.

Do not treat performance or liveness conclusions as interchangeable across them.

## 5.6 Kernel foundations

Add these explicit M1/M2 obligations:

* single-core IRQ/preemption/locking/exception-stack contract;
* FP/AdvSIMD context isolation;
* executable-page D/I cache publication;
* single-core TLB/ASID lifecycle;
* AArch64 atomic/memory-ordering foundation;
* deterministic secondary-CPU/GIC bring-up;
* SMP scheduler/wakeup/migration invariants;
* acknowledged cross-CPU TLB shootdowns.

## 5.7 User-copy

State the selected fault-fixup plus address-space lifetime/locking design and exact partial-copy semantics.

## 5.8 Time and entropy

State separate monotonic, realtime, and entropy sources. Disable accidental QEMU DTB randomness in deterministic profiles and provide `AT_RANDOM` from the declared entropy source.

## 5.9 VirtIO

Add an explicit feature/status/reset/queue/barrier/DMA/error conformance layer around the pinned crate.

## 5.10 fd port

State that the standard built-in upstream fd port driver is intentionally used. Ban project-specific/dynamic drivers and NIFs.

## 5.11 Demo-state wording

Replace “durable demo state” with **supervisor-resilient in-memory demo state**. It survives the intentional worker restart but resets on release/BEAM/OS restart. The reset boundary must be visible and tested.

## 5.12 Display ABI

Add the double-buffered mapped-surface/present-completion model from F-14.

## 5.13 Metrics and latency

Separate application state from native telemetry. Rename the guest metric to event-to-present-completion unless host-visible evidence exists.

## 5.14 Qualification

Add the frozen statistical and invalid-run rules from F-18 and canonical-image isolation from F-19.

## 5.15 Schedule estimate

Treat the “18–48 month” statement as a rough, non-commitment heuristic. Re-estimate only after Gate 1 using measured throughput, defect discovery, and available runner capacity.

## 5.16 Evidence ledger

Replace the non-reproducible claim “454 returned Exa search results” as the practical audit basis with a machine-readable source/claim ledger containing:

* source title;
* source URL/repository/tag/commit;
* access date;
* source hash where practical;
* exact claim supported;
* primary/secondary/self-reported classification;
* issue/ADR that consumes the claim;
* known limitation or disagreement.

---

# 6. Exact relation and workflow mutations

## 6.1 Dependency changes

1. <issue id="30a7e6c4-fe50-4866-8f9e-a8e75d38a5e6" href="tasks/p1-14.md">ROB-782</issue>
   * remove `blocked by ROB-704`;
   * retain `blocked by ROB-701 and ROB-777`;
   * make it block the executable/publish half of <issue id="1f4b9992-06e3-4adc-9bc7-d165d1070e41" href="https://linear.app/robert-guss/issue/ROB-704/p1-08-load-a-static-aarch64-elf-into-an-isolated-el0-process">ROB-704</issue>.
2. <issue id="1f4b9992-06e3-4adc-9bc7-d165d1070e41" href="https://linear.app/robert-guss/issue/ROB-704/p1-08-load-a-static-aarch64-elf-into-an-isolated-el0-process">ROB-704</issue>
   * split into 08a/08b, or add hard completion dependencies on <issue id="6252fe60-2d67-45fa-8e6b-1d7676c5b76f" href="tasks/p1-13.md">ROB-781</issue> and <issue id="30a7e6c4-fe50-4866-8f9e-a8e75d38a5e6" href="tasks/p1-14.md">ROB-782</issue>;
   * preliminary parser/staging work may proceed earlier, but “runs native Rust process” cannot complete first.
3. <issue id="6252fe60-2d67-45fa-8e6b-1d7676c5b76f" href="tasks/p1-13.md">ROB-781</issue>
   * Gate 1 acceptance: single-CPU task switch/fault/reuse only;
   * migration acceptance moves to <issue id="18c87017-a773-4df7-9c02-263b0d961774" href="tasks/p2-05b.md">ROB-785</issue>/Gate 2.
4. <issue id="e8abae24-4299-4747-b88c-c9f86919a480" href="tasks/p2-08.md">ROB-719</issue>
   * add `blocked by ROB-788`;
   * block P2-12/P2-13/Gate 2 only when robust-list use is admitted by the frozen contract.
5. <issue id="b19dcf10-3e88-49f5-8264-9c34f1332bf4" href="tasks/p2-11.md">ROB-716</issue> **/** <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue> **/** <issue id="7c62097b-c0d3-49de-8f20-1977351e31d5" href="tasks/p2-11b.md">ROB-795</issue> **/** <issue id="c54813fe-6009-4a4f-9886-6ef219de7e24" href="tasks/p2-11c.md">ROB-796</issue>
   * keep <issue id="b19dcf10-3e88-49f5-8264-9c34f1332bf4" href="tasks/p2-11.md">ROB-716</issue> as tracking only;
   * wait/deadline users depend directly on <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue>;
   * startup/auxv entropy users depend directly on <issue id="7c62097b-c0d3-49de-8f20-1977351e31d5" href="tasks/p2-11b.md">ROB-795</issue>;
   * CPU count/affinity/platform identity users depend directly on <issue id="c54813fe-6009-4a4f-9886-6ef219de7e24" href="tasks/p2-11c.md">ROB-796</issue>;
   * all three children block P2-12/P2-13/Gate 2 where their behavior is admitted.
6. <issue id="7101c1b4-a2a0-4df5-ac65-3cf1ff65aa10" href="tasks/p0-15.md">ROB-778</issue> **/** <issue id="9abecb77-11a0-472b-aed7-222667e5fa9d" href="https://linear.app/robert-guss/issue/ROB-748/p5-04-freeze-the-toolkit-neutral-uibackend-and-slint-license-decision">ROB-748</issue>
   * <issue id="7101c1b4-a2a0-4df5-ac65-3cf1ff65aa10" href="tasks/p0-15.md">ROB-778</issue> owns the toolkit/license decision;
   * rename <issue id="9abecb77-11a0-472b-aed7-222667e5fa9d" href="https://linear.app/robert-guss/issue/ROB-748/p5-04-freeze-the-toolkit-neutral-uibackend-and-slint-license-decision">ROB-748</issue> to “Verify and integrate the frozen UiBackend/toolkit/license decision”;
   * <issue id="9abecb77-11a0-472b-aed7-222667e5fa9d" href="https://linear.app/robert-guss/issue/ROB-748/p5-04-freeze-the-toolkit-neutral-uibackend-and-slint-license-decision">ROB-748</issue> may replace the toolkit only through a new human-approved ADR.
7. **New P5-00**
   * blocked by P0-11, P0-12, P1-07, and the native VM/handle primitives;
   * blocks P5-01 and P5-03.
8. **Qualification**
   * P6-05 runs against the canonical image after all retained changes;
   * AI exercises are independent branches, not prerequisites that mutate that image.

## 6.2 Label/status changes

* Keep <issue id="fe0297d9-02f5-4bf6-bd2f-009d1830eb00" href="tasks/p0-02.md">ROB-683</issue>, <issue id="b4946023-20dd-42eb-9602-8ad05ff6d505" href="tasks/p0-01.md">ROB-684</issue>, <issue id="74423d8a-8cce-4677-a5fa-c6ce3659f423" href="tasks/p0-03.md">ROB-685</issue> and other dependency-ready M0 work as `ready-for-agent`.
* Mark all M1–M6 implementation issues `spec-complete` + `gate-blocked`.
* Mark <issue id="c8ecfa82-2154-483e-9572-32c3383bdfe7" href="tasks/p2-06.md">ROB-714</issue> and <issue id="6a078ebc-b32b-4169-aa5f-74b1a36878ba" href="tasks/p2-05.md">ROB-715</issue> `tracking`, not `ready-for-agent`.
* Keep gate issues `ready-for-human`.
* Promote future issues only when their gate and direct dependencies are complete.

---

# 7. Exact high-impact issue-description edits

## <issue id="ec32ea87-c5cc-4357-84ba-69994eebf60d" href="tasks/p0-04.md">ROB-686</issue> / <issue id="a0789a32-63c5-4bcb-aea1-adec3fa938be" href="tasks/p0-08.md">ROB-690</issue> — host-contract completeness

Append:

> Dynamic traces are necessary but not sufficient. Build a source-to-contract inventory for the exact frozen musl/ERTS configuration. Exercise fault-injected allocation, copy, timeout, cancellation, signal, close, thread-start, thread-exit, and shutdown paths. Every inventoried interaction must be traced, proven unreachable by configuration, or recorded as unresolved Gate 0 risk. Two equal happy-path traces do not establish completeness.

## <issue id="760ef061-bde7-4e22-92e2-a620d09a4e55" href="tasks/p0-11.md">ROB-696</issue> / <issue id="8a611583-4865-4e56-a285-2ee7f72d2dbf" href="tasks/p0-12.md">ROB-694</issue> / <issue id="74e3ebd6-dfb7-49b3-afe6-d1f4d9f8e427" href="https://linear.app/robert-guss/issue/ROB-751/p5-01-integrate-the-selected-virtio-gpu-transport-into-the-kernel">ROB-751</issue> — VirtIO contract

Append:

> Freeze and test the complete VirtIO device-status, reset, feature-negotiation, FEATURES_OK, VERSION_1, queue, descriptor, barrier, DMA, interrupt, error, timeout, and teardown semantics for the pinned crate/device/transport. Compilation is not conformance evidence. A missing required feature or incorrect reset/error path blocks the device decision.

## <issue id="3abb66fe-a088-485e-ade5-3444da5cf81c" href="https://linear.app/robert-guss/issue/ROB-700/p1-06-implement-the-generic-timer-interrupt-driven-preemption-and-wait">ROB-700</issue> — timer/preemption/waits

Convert to a tracking issue or append:

> This issue is blocked by P1-00. Define the task-state machine, preemption-disable rules, IRQ nesting, lock classes/order, scheduler reentrancy, wait-object ownership, wake publication/linearization, timeout cancellation, and no-sleep/no-allocation contexts before implementation. Split timer/IRQ, scheduler/preemption, and wait queues into separate child issues.

## <issue id="df49d497-185e-43fb-9b45-740fd1c84588" href="tasks/p1-09.md">ROB-705</issue> — user copy

Append:

> Use the frozen POC user-copy mechanism: address-space lifetime/read lock plus architecture exception-fixup guarded copy sites. Convert approved EL1 copy faults to EFAULT, define exact partial-copy behavior, and serialize unmap/protect/exit against copies. No kernel subsystem may dereference a user pointer directly. Test copy-versus-unmap, copy-versus-exit, guard crossing, integer overflow, zero length, and fault on each page boundary.

## <issue id="b19dcf10-3e88-49f5-8264-9c34f1332bf4" href="tasks/p2-11.md">ROB-716</issue> / <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue> / <issue id="7c62097b-c0d3-49de-8f20-1977351e31d5" href="tasks/p2-11b.md">ROB-795</issue> / <issue id="c54813fe-6009-4a4f-9886-6ef219de7e24" href="tasks/p2-11c.md">ROB-796</issue> — time/random/system queries

The parent is now correctly a tracking issue. Keep the three children. Add an explicit PL031/immutable-epoch choice to <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue> if realtime is admitted, and link wait users directly to <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue> rather than the tracking parent.

## <issue id="402dd64d-c4d0-4e23-988a-ce5e70bb366c" href="tasks/p2-09.md">ROB-724</issue> / <issue id="89beab3f-83f8-4aeb-85f4-fb650aac7e54" href="tasks/p2-09a.md">ROB-791</issue> / <issue id="32394ed7-20e7-411a-9bbc-38da9a016273" href="tasks/p2-09b.md">ROB-792</issue> / <issue id="149128b1-6459-49ce-beef-4f94977ba57c" href="tasks/p2-09c.md">ROB-793</issue> — signals

The parent is now correctly a tracking issue and the children are strong. Correct child dependencies after P1-08 is split and require the complete byte-level frame, forged-return, and one-terminal-outcome evidence at Gate 2.

## <issue id="e3500601-1aad-4498-a4be-3b5457830c39" href="tasks/p2-10.md">ROB-722</issue> / <issue id="90c2d00c-1514-4541-a5fa-b74275a31a1c" href="tasks/p2-10a.md">ROB-789</issue> / <issue id="d8900819-9d6b-4729-ac14-515171580562" href="tasks/p2-10b.md">ROB-790</issue> — streams, descriptors, and poll

The parent is now correctly a tracking issue. The children cover bounded streams, descriptor generations, readiness registration, close/reuse races, and timeouts well. Ensure open-file-description sharing (`dup`, offsets, shared status flags) is explicit whenever admitted, and link signal interruption through <issue id="149128b1-6459-49ce-beef-4f94977ba57c" href="tasks/p2-09c.md">ROB-793</issue>.

## <issue id="be5f618d-ea32-42bb-860a-8040a7664f7b" href="tasks/p3-06.md">ROB-732</issue> — ERTS concurrency proof

Replace “two schedulers execute tagged work” with:

> Use a barrier-synchronized CPU-bound workload that cannot complete on one scheduler within the measured overlap window. Correlate ERTS scheduler identity, OS thread identity, vCPU execution intervals, and reductions/work completion. Scheduler threads merely existing or being online is not concurrency proof.

## <issue id="818117b5-a6fe-48f1-88de-d0524d320ad5" href="tasks/p3-09.md">ROB-733</issue> / <issue id="5f18d9b1-a204-4e15-9536-ef815ec67445" href="tasks/p6-03.md">ROB-762</issue> — memory stability

Replace qualitative “stabilizes” language with the P6-01-frozen warm-up, slope, confidence, and resource-exactness policy.

## <issue id="7cbdc8ec-ef1b-445a-a871-65c488298ec4" href="https://linear.app/robert-guss/issue/ROB-739/p4-03-implement-final-runtime-lab-supervision-and-restart-persistent">ROB-739</issue> / <issue id="9cfadd24-e836-4672-adb3-9a180564766a" href="tasks/p5-09.md">ROB-752</issue> — state

Rename “durable” to “supervisor-resilient in-memory.” Add an acceptance test proving preservation across the worker crash and intentional reset across BEAM/OS restart.

## <issue id="a4f0c083-dab2-4057-990c-38611d085681" href="tasks/p4-04.md">ROB-740</issue> / <issue id="d70e5cf2-a0e2-4659-a820-b100ba17b52b" href="tasks/p4-06.md">ROB-746</issue> — fd stream/port

Add `{packet_size, frozen_limit}` and busy limits. Correct the built-in fd-driver wording from F-13.

## <issue id="c9120fc3-99a5-408b-beb7-06fb5b34eab4" href="tasks/p4-05.md">ROB-743</issue> / <issue id="473e284a-c4e5-40b4-b5a8-fafe08e69b4f" href="tasks/p4-07.md">ROB-745</issue> — ETF and action semantics

Add all F-15 bounds and F-16’s terminal action outcomes.

## <issue id="9abecb77-11a0-472b-aed7-222667e5fa9d" href="https://linear.app/robert-guss/issue/ROB-748/p5-04-freeze-the-toolkit-neutral-uibackend-and-slint-license-decision">ROB-748</issue>

Rename to:

> P5-04 — Verify and integrate the frozen UiBackend, toolkit, and license decision

The decision is owned by P0-15.

## <issue id="e314449d-9901-43aa-b10b-6f6e095c157c" href="tasks/p5-08.md">ROB-756</issue>

Separate `application_state` from `native_telemetry`; eliminate telemetry echo loops.

## <issue id="adeb9424-74cc-4388-8346-8d91b6178835" href="https://linear.app/robert-guss/issue/ROB-760/p5-11-instrument-event-to-pixel-latency-frame-cadence-freezes-and">ROB-760</issue> / <issue id="14465095-5b0b-469f-9ce5-dea9b6ff618a" href="tasks/p5-13.md">ROB-759</issue>

Rename event-to-pixel/visible measurements to event-to-present-completion unless a host observer exists. Make thresholds profile-calibrated provisional targets.

## <issue id="2e654860-ede7-498a-b157-2c18eebea534" href="tasks/p6-01.md">ROB-761</issue>

Add the objective statistics policy and canonical-image/worktree policy.

## <issue id="cf195cde-2b49-4c81-a5f2-e679f7facd72" href="tasks/p6-05.md">ROB-766</issue> / <issue id="4ee27d08-7520-43e6-893d-76a538962e90" href="tasks/p6-06.md">ROB-768</issue> / <issue id="3d832396-ae2e-4120-b5bc-a67a71fc763c" href="tasks/p6-07.md">ROB-771</issue> / <issue id="f031c483-208b-48f1-9c20-306baec49d25" href="tasks/p6-08.md">ROB-763</issue>

State that exercises use isolated branches/images. Any retained result forces a new canonical image and reruns affected reproducibility/qualification.

## <issue id="f49e44df-274c-42aa-9a33-0679bd6a31f5" href="tasks/p6-10.md">ROB-770</issue>

Resolve the scoring vocabulary contradiction. H1–H6 scores are `Pass`, `Conditional`, or `Fail`; “Promising” may be explanatory text for H5 but is not a fourth score.

---

# 8. Paste-ready missing Linear issues

## New issue: P1-00 — Freeze single-CPU IRQ, preemption, locking, and exception-stack invariants

### Goal

Define and prove the kernel execution-context rules that every M1 interrupt, scheduler, allocator, VM, wait-queue, tracing, process-exit, and user-copy path depends on.

### Why this is a blocker

Phase 1 already introduces timer IRQs, preemption, blocking, faults, and shared kernel state. P2’s SMP memory model cannot retroactively make M1’s single-core reentrancy safe. Without a frozen IRQ/preemption/locking contract, implementation agents can independently choose incompatible rules that appear to work until a timer interrupt lands in the wrong critical section.

### What to build

* Define exception/IRQ entry stacks, guard pages, nesting limit, saved context, and current-task/per-CPU access.
* Define IRQ-disable and preemption-disable nesting, ownership, restoration, and assertions.
* Define lock classes: IRQ-safe spin lock, task-only spin/mutex where applicable, and waitable objects.
* Define lock ordering and prohibit sleeping, user copy, or blocking allocation while holding non-sleepable locks.
* Define whether allocation/logging is permitted in IRQ or panic context and provide bounded emergency paths where needed.
* Define scheduler-entry/reentrancy rules and the task-state transition linearization points.
* Define the single-CPU sleep/wakeup publication invariant and compiler-ordering requirements.
* Instrument violations with structured, non-recursive failure records.
* Add a machine-readable lock/context inventory linked to callers.

### Acceptance criteria

* Nested IRQ/preemption-disable state restores exactly and never enables interrupts early.
* Timer IRQ at every injected critical boundary cannot corrupt allocator, VM, handle, wait, or task state.
* Sleep-in-IRQ, sleep-while-spinlocked, lock inversion, recursive scheduler entry, and blocking allocation in forbidden context fail deterministically.
* Exception and IRQ stacks cannot overlap user/kernel task stacks and guard faults are classified.
* Every M1 lock/context use appears in the inventory and names its order and context rule.
* Negative canaries prove the harness detects early-enable, lost wake, lock inversion, and stack-overrun defects.

### Tests/evidence

* Model tests for context/lock nesting and wait/wake state.
* Guest fault/preemption injection at every annotated boundary.
* Lock-order and forbidden-context assertions.
* Stack guard and nested-exception tests.
* Structured trace replay.

### Dependencies

Blocked by P1-02 and P1-03.
Blocks P1-06, P1-09, P1-12, and GATE-1.

### Out of scope

SMP ordering, cross-CPU locks/IPIs, NUMA, production real-time guarantees, or lock-free optimization.

### Completion rule

Done means every M1 execution context and synchronization primitive has one explicit invariant, linearization point, forbidden-operation rule, negative test, and diagnostic path.

---

## New issue: P5-00 — Freeze the display-surface, buffer-ownership, and present-completion ABI

### Goal

Lock the exact protected boundary by which the renderer writes pixels and requests presentation while the kernel retains exclusive VirtIO/DMA/device ownership.

### Why this is a blocker

“Renderer draws and presents through a display handle” is not an implementation contract. Copy syscalls, shared surfaces, direct queue access, and unrestricted mapped device memory have very different performance, isolation, lifetime, and fault behavior.

### Locked POC decision

Use two kernel-owned page-backed software-rendering surfaces mapped writable and execute-never into the renderer only. The kernel owns VirtIO resources, queues, DMA/pinning, scanout, interrupts, reset, and reclamation.

### What to build

* Freeze pixel format, dimensions, stride, alignment, maximum bytes, and dirty-rectangle rules.
* Create generation-safe display/surface handles with explicit rights.
* Define buffer states: free, rendering, queued, displayed/released, failed.
* Map only the renderer-owned surface writable+NX; ERTS and unrelated processes receive no mapping.
* Define `display_present(handle, generation, frame_seq, dirty_rect)` validation and completion.
* Prevent renderer writes to queued buffers and prevent kernel/device reuse before completion.
* Define transfer/flush command completion as the guest-side present-completion proxy.
* Define resize as out of scope or a versioned surface replacement.
* Define renderer crash, device timeout/reset, stale completion, malformed rect, and kernel shutdown behavior.
* Quiesce/detach device backing before pages are unmapped or reclaimed.
* Bound outstanding frames and expose queue/completion telemetry.

### Acceptance criteria

* Renderer can draw and present continuously without direct MMIO, VirtIO queue, or DMA authority.
* ERTS/unrelated processes cannot map or present the surface.
* Invalid/stale handle, generation, buffer state, frame sequence, or rectangle is rejected without device action.
* No queued/displayed page is reclaimed or remapped before safe completion/reset.
* Renderer crash and device reset leak no resource and cannot corrupt another process.
* Event-to-present-completion is measurable and explicitly not called host-visible pixel time.
* Double-buffer ownership survives stress, delayed/duplicate completion, and forced reset.

### Tests/evidence

* Capability-denial and mapping tests.
* Buffer-state model/property tests.
* Delayed/duplicate/stale completion injection.
* Renderer crash/device reset/restart tests.
* DMA/page-lifetime audit and trace replay.
* TCG/HVF probe using the frozen device transport.

### Dependencies

Blocked by P0-11, P0-12, P1-05, P1-07, and P1-14.
Blocks P5-01, P5-03, P5-04, and all renderer integration.

### Out of scope

GPU acceleration, direct userspace VirtIO, arbitrary resolution changes, third-party processes, shared BEAM framebuffer access, or physical display hardware.

### Completion rule

Done means pixel memory, device authority, buffer ownership, present completion, reset, and reclamation form one versioned capability ABI with model and guest evidence.

---

# 9. Recommended tracking/child splits

| Parent | Convert parent to | Children |
| -- | -- | -- |
| P1-05 | Tracking | P1-05a page-table primitives/reference model; P1-05b kernel/user virtual layout and address-space lifecycle; P1-05c single-core map/protect/unmap/ASID teardown |
| P1-06 | Tracking | P1-06a generic timer/GIC IRQ; P1-06b preemptive scheduler/task state; P1-06c sleep queues/timeouts/wakeup linearization |
| P1-08 | Tracking | P1-08a ELF validation/staging; P1-08b executable publication/initial stack/EL0 entry |
| P2-04 | Tracking | P2-04a VMA model, `brk`, anonymous mapping; P2-04b `mprotect`/`munmap`, splitting/merge/rollback; P2-04c file-backed read-only mappings if actually admitted |
| P5-01 | Tracking | P5-01a VirtIO transport/status/features/reset; P5-01b GPU 2D resource/backing/scanout; P5-01c transfer/flush/fence/error qualification |
| P5-03 | Tracking | P5-03a renderer process/capability bootstrap; P5-03b mapped surfaces/present client; P5-03c event/render loop and IPC/backpressure |

Each child must have a bounded observable behavior, invariants, negative tests, and one verification command. Parent tracking issues should not be delegated as code tasks.

---

# 10. Ticket-by-ticket disposition matrix

Legend:

* **KEEP** — coherent specification; remains gate-blocked until dependencies pass.
* **AMEND** — description or acceptance criteria require the stated correction.
* **RELATION** — dependency graph must change.
* **SPLIT/TRACK** — convert to tracking parent and create smaller children.
* **TRACKING** — correctly a roll-up issue; never delegate as code.
* **GATE** — human evidence decision; never an implementation task.

## M0

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="fe0297d9-02f5-4bf6-bd2f-009d1830eb00" href="tasks/p0-02.md">ROB-683</issue> — P0-02 — Build the Linux reference runtime_lab Mix application | **KEEP** | Good reference workload. Ensure no native Hex dependency, include deterministic crash/stress/shutdown cases, and emit workload version/seed. |
| <issue id="b4946023-20dd-42eb-9602-8ad05ff6d505" href="tasks/p0-01.md">ROB-684</issue> — P0-01 — Create the repository, evidence model, and reproducible build shell | **AMEND** | Add machine-readable source/claim ledger, sealed dependency/source mirror policy, checksums, and gate-aware label automation. |
| <issue id="74423d8a-8cce-4677-a5fa-c6ce3659f423" href="tasks/p0-03.md">ROB-685</issue> — P0-03 — Pin the complete host and target toolchain with build receipts | **AMEND** | Pin exact source and binary digests after probes; include QEMU machine types, cross compiler/sysroot, linker, Rust target flags, and offline/sealed rebuild. |
| <issue id="ec32ea87-c5cc-4357-84ba-69994eebf60d" href="tasks/p0-04.md">ROB-686</issue> — P0-04 — Trace and document the reference ERTS workload on Linux | **AMEND** | Add source-to-contract coverage and fault/error/cancellation/timeout/exit scenarios; repeat traces alone are insufficient. |
| <issue id="74286a8a-0043-4329-bf5b-abeed170b067" href="tasks/p0-09.md">ROB-687</issue> — P0-09 — Specify ETF UI protocol v1 and conformance fixtures | **AMEND** | Freeze one framing owner, compressed-term policy, atom allowlist, depth/arity/size limits, trailing bytes, sequence/reconnect rules, and differential fixtures. |
| <issue id="8487cc59-d6ea-45c4-a581-dd4a428639dd" href="tasks/p0-05.md">ROB-688</issue> — P0-05 — Cross-build static non-JIT AArch64-musl upstream ERTS | **KEEP** | The appended audit correction is strong. Extend closure inspection across the complete release tree and runtime load attempts. |
| <issue id="98c3c525-b06f-4f2c-9757-134015d632e9" href="tasks/p0-10.md">ROB-689</issue> — P0-10 — Implement and stress Linux-hosted Rust↔Elixir protocol endpoints | **AMEND** | Use exact port packet/packet_size/busy limits, terminal action ledger, malformed compressed input, queue saturation, and disconnect-at-every-stage tests. |
| <issue id="a0789a32-63c5-4bcb-aea1-adec3fa938be" href="tasks/p0-08.md">ROB-690</issue> — P0-08 — Freeze the exact AArch64 BEAM host contract revision 1 | **KEEP** | The appended correction is strong. Add explicit unreachable-source-path proof and error-path coverage report. |
| <issue id="096905ea-8f1b-4a74-b35c-a82e066e3359" href="tasks/p0-13.md">ROB-691</issue> — P0-13 — Freeze Phase 0 ADRs, licenses, hypotheses, and evidence index | **AMEND** | Make P0-15 the toolkit/license owner; include source/claim ledger, unresolved-risk register, and exact evidence coverage with no orphan claim. |
| <issue id="24259af1-bbeb-4a57-9cdb-f66230f85e26" href="tasks/p0-07.md">ROB-692</issue> — P0-07 — Pair a genuine Mix release with the target ERTS | **KEEP** | Correct gate. Inventory all native artifacts and prove direct beam launch, config loading, read-only operation, and clean shutdown. |
| <issue id="2af8ae81-9e36-4561-b564-99804af0675d" href="tasks/p0-06.md">ROB-693</issue> — P0-06 — Run the target ERTS artifact on AArch64 Linux | **AMEND** | Authoritative evidence must use native AArch64 or full-system AArch64 Linux. qemu-user is smoke-only. Repeat startup/thread/signal/shutdown and capture full artifact closure. |
| <issue id="8a611583-4865-4e56-a285-2ee7f72d2dbf" href="tasks/p0-12.md">ROB-694</issue> — P0-12 — Prove the display/input path under Apple Silicon HVF and select MMIO or PCI | **AMEND** | Freeze exact Mac/QEMU frontend/device commands and semantic parity; separate transport, GPU protocol, and display/input frontend decisions. |
| <issue id="43469151-2127-4c4b-aa61-41c010ff6e2a" href="gates/gate-0.md">ROB-695</issue> — GATE-0 — Decide whether the Rust-kernel/standard-BEAM POC may enter kernel implementation | **GATE** | Strong corrected gate. It is currently unmet; authorize M1 only with all evidence and explicit human approval. |
| <issue id="760ef061-bde7-4e22-92e2-a620d09a4e55" href="tasks/p0-11.md">ROB-696</issue> — P0-11 — Prove bare-metal virtio display and pointer input under Linux TCG | **AMEND** | Add full VirtIO feature/status/reset/queue/barrier/DMA/error contract and audit the pinned crate’s VERSION_1 behavior. |
| <issue id="6444be9e-b65a-48c4-b235-59cde0aee94f" href="tasks/p0-14.md">ROB-777</issue> — P0-14 — Freeze the versioned QEMU machine, CPU, auxv/HWCAP, page-size, cache, and atomics baseline | **AMEND** | Keep. Change PCI wording from proven portable to default candidate pending TCG/HVF proof; freeze DTB randomness and entropy policy. |
| <issue id="7101c1b4-a2a0-4df5-ac65-3cf1ff65aa10" href="tasks/p0-15.md">ROB-778</issue> — P0-15 — Prove the no_std Slint renderer path and freeze the toolkit/license decision | **KEEP** | Excellent missing gate. Keep final license decision human-reviewed; process separation is not assumed to alter license obligations. |
| <issue id="16294855-9131-4ca5-b9de-063b3da7b9d9" href="tasks/p0-16.md">ROB-779</issue> — P0-16 — Benchmark and freeze feasible TCG, KVM, and HVF qualification runner profiles | **KEEP** | Excellent. Preserve semantic/performance distinctions and first-failure evidence. |
| <issue id="a927064b-f115-42f4-b88f-121f9fb8e479" href="tasks/p0-17.md">ROB-780</issue> — P0-17 — Reproduce and disposition current BEAM-on-custom-kernel prior-art risks | **KEEP** | Excellent. Classify Tyn claims as self-reported unless reproduced; compare architecture differences and prohibit wait-semantic workarounds. |

## M1

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="f05b5e88-799d-4488-878a-3d208bb49c81" href="tasks/p1-01.md">ROB-698</issue> — P1-01 — Scaffold the no_std kernel, linker layout, and direct QEMU runner | **AMEND** | Fix EL terminology; consume the versioned platform manifest and fail on runner drift. No implementation before Gate 0. |
| <issue id="4be808a0-9dda-4488-863f-c55739ba462a" href="tasks/p1-02.md">ROB-699</issue> — P1-02 — Implement EL normalization, UART, and QEMU device-tree discovery | **AMEND** | Replace reset-to-EL0 wording; define EL2→EL1/EL1 entry, SCTLR/HCR state, DTB validation, UART bounds, and malformed-DTB failure. |
| <issue id="89d80ed3-13ae-4fd1-be58-9f770ddbb104" href="tasks/p1-03.md">ROB-702</issue> — P1-03 — Install AArch64 exception vectors, IRQ dispatch, and structured panic records | **AMEND** | Add guarded exception/IRQ stacks, nesting/reentrancy policy, full ESR/FAR/register classification, and dependency on P1-00 design. |
| <issue id="f1266149-04ba-41c0-bb11-06903b89f86b" href="tasks/p1-04.md">ROB-697</issue> — P1-04 — Build the physical page allocator and bounded kernel heap | **AMEND** | Define no-allocation/limited emergency allocation contexts, metadata self-hosting, double-free/use-after-free canaries, and deterministic OOM behavior. |
| <issue id="9eefac4d-6a57-4905-8ad1-1f32841d5457" href="https://linear.app/robert-guss/issue/ROB-701/p1-05-implement-kernel-virtual-memory-and-isolated-user-page-tables">ROB-701</issue> — P1-05 — Implement kernel virtual memory and isolated user page tables | **SPLIT/TRACK** | Use three children. Keep appended ASID/W^X corrections; remove ad hoc TLBI and fix learning-checkpoint terminology. |
| <issue id="3abb66fe-a088-485e-ade5-3444da5cf81c" href="https://linear.app/robert-guss/issue/ROB-700/p1-06-implement-the-generic-timer-interrupt-driven-preemption-and-wait">ROB-700</issue> — P1-06 — Implement the generic timer, interrupt-driven preemption, and wait queues | **SPLIT/TRACK** | Block on new P1-00; split timer IRQ, scheduler/preemption, and wait queues. Define state/lock/wakeup invariants first. |
| <issue id="1ea0618c-d34f-4ec0-87d7-a09dd45c52b4" href="tasks/p1-07.md">ROB-703</issue> — P1-07 — Define native ABI v1 and capability-scoped handle tables | **AMEND** | Define generation-safe handles, rights attenuation, close/wait races, process teardown, ABI versioning, and exact copy rules. |
| <issue id="1f4b9992-06e3-4adc-9bc7-d165d1070e41" href="https://linear.app/robert-guss/issue/ROB-704/p1-08-load-a-static-aarch64-elf-into-an-isolated-el0-process">ROB-704</issue> — P1-08 — Load a static AArch64 ELF into an isolated EL0 process | **RELATION + SPLIT** | Split validation/staging from publish/execute. P1-14 must block execution; general hard-float process requires P1-13. |
| <issue id="df49d497-185e-43fb-9b45-740fd1c84588" href="tasks/p1-09.md">ROB-705</issue> — P1-09 — Harden user-copy paths and contain EL0 memory faults | **AMEND** | Lock address-space lifetime + exception-fixup mechanism, partial-copy semantics, teardown serialization, and copy-vs-unmap/exit tests. |
| <issue id="41e99e70-a406-4e5a-8e8e-c4636dee9af0" href="tasks/p1-10.md">ROB-707</issue> — P1-10 — Build the immutable system archive and manifest-driven boot plan | **AMEND** | Freeze archive format, path normalization, duplicate/collision rules, hash coverage, parser limits, capability compilation, and malformed-image behavior. |
| <issue id="dc5cc039-460c-4a26-81c2-703690f9224c" href="tasks/p1-11.md">ROB-706</issue> — P1-11 — Establish structured tracing, GDB/QMP control, and machine-readable test completion | **AMEND** | Define bounded/non-recursive trace behavior, overflow accounting, panic-safe path, host/guest clock domains, and artifact schema/version. |
| <issue id="f4b3ab0f-2fe6-414e-a066-b0ad0bd54aff" href="tasks/p1-12.md">ROB-709</issue> — P1-12 — Qualify the kernel spine with 1,000 boots and randomized memory/scheduler tests | **KEEP** | The appended correction is strong. Add P1-00 and fixed P1-08b relations; correct EL terminology. |
| <issue id="4f149cdf-b330-4b02-82c9-fed37e36e5be" href="gates/gate-1.md">ROB-708</issue> — GATE-1 — Decide whether the kernel spine is trustworthy enough for the musl contract | **GATE** | Strong corrected gate. Require single-CPU FP evidence; migration belongs to Gate 2. Add P1-00 and fix EL wording. |
| <issue id="6252fe60-2d67-45fa-8e6b-1d7676c5b76f" href="tasks/p1-13.md">ROB-781</issue> — P1-13 — Implement and prove EL0 FP/AdvSIMD context isolation | **AMEND** | Keep eager save/restore. Move cross-CPU migration completion to P2-05b/Gate 2; Gate 1 proves single-CPU preemption/fault/reuse. |
| <issue id="30a7e6c4-fe50-4866-8f9e-a8e75d38a5e6" href="tasks/p1-14.md">ROB-782</issue> — P1-14 — Implement executable-page cache maintenance and page-table/TLB coherency | **RELATION** | Remove dependency on P1-08. Block P1-08b instead. Negative canary may use architecture model/instrumentation if an emulator does not manifest stale code. |

## M2

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="765cc185-ea7f-4440-881c-ef0cedf1a77d" href="tasks/p2-01.md">ROB-712</issue> — P2-01 — Create the ERTS compatibility personality and executable syscall contract | **AMEND** | Keep Linux-shaped ABI isolated to ERTS; generate dispatch/tests from contract; fail unsupported calls/flags before side effects; include coupled state machines. |
| <issue id="155d5702-f829-4a2a-baf4-0dd6fb4f578e" href="tasks/p2-02.md">ROB-710</issue> — P2-02 — Boot a static musl process with correct initial stack, auxv, TLS, and errno | **AMEND** | Use exact frozen auxv/HWCAP/AT_RANDOM, program headers, stack alignment, TLS model, and failure cases; block normal hard-float execution on P1-13. |
| <issue id="d80bf35a-f222-44bc-870e-46593e614722" href="tasks/p2-03.md">ROB-711</issue> — P2-03 — Implement the read-only VFS and admitted file/path syscalls | **AMEND** | Model open-file descriptions, shared offsets/status flags, per-fd CLOEXEC, dup semantics, /dev/null, release path probes, and directory/stat errno precedence. |
| <issue id="d9a8cbd5-d426-4b5e-a812-286bf5b754f9" href="https://linear.app/robert-guss/issue/ROB-713/p2-04-implement-brk-mmap-mprotect-munmap-and-vm-area-accounting">ROB-713</issue> — P2-04 — Implement brk, mmap, mprotect, munmap, and VM-area accounting | **SPLIT/TRACK** | Split VMA/brk/anonymous mapping, protect/unmap/splitting/rollback, and only admitted file mappings. Block SMP completion on P2-05c. |
| <issue id="6a078ebc-b32b-4169-aa5f-74b1a36878ba" href="tasks/p2-05.md">ROB-715</issue> — P2-05 — TRACKING: Complete SMP CPU, scheduler, and TLB safety | **TRACKING** | Correct conversion. Remove ready-for-agent; parent closes only when 05a–c pass. |
| <issue id="c8ecfa82-2154-483e-9572-32c3383bdfe7" href="tasks/p2-06.md">ROB-714</issue> — P2-06 — Implement clone, native thread lifecycle, TLS, and child-TID semantics | **TRACKING** | Convert title/label consistently to tracking. Children 06a/06b own implementation. |
| <issue id="0adfa44e-c7f3-462f-96b4-ff45fed21ad4" href="tasks/p2-07.md">ROB-718</issue> — P2-07 — Implement futex wait, wake, timeout, and required bitset semantics | **AMEND** | Derive exact ops/clocks/flags from pinned musl/ERTS; define atomic compare-and-block, unmap/exit races, interruption, timeout, and waiter lifetime. |
| <issue id="e8abae24-4299-4747-b88c-c9f86919a480" href="tasks/p2-08.md">ROB-719</issue> — P2-08 — Implement robust-list and thread-exit synchronization cleanup | **RELATION + AMEND** | Block on P2-06b. Implement only if admitted; exact owner-death/list-walk/fault semantics and bounded traversal. |
| <issue id="402dd64d-c4d0-4e23-988a-ce5e70bb366c" href="tasks/p2-09.md">ROB-724</issue> — P2-09 — TRACKING: Complete bounded signal state, AArch64 frames, and wait interruption | **TRACKING** | Correct conversion. Remove ready-for-agent; children 09a–c own implementation. Fix P1-08b/direct-child dependencies. |
| <issue id="e3500601-1aad-4498-a4be-3b5457830c39" href="tasks/p2-10.md">ROB-722</issue> — P2-10 — TRACKING: Complete streams, descriptor lifecycle, and poll readiness | **TRACKING** | Correct conversion. Remove ready-for-agent; children 10a–b own implementation. Keep signal-interruption integration in P2-09c. |
| <issue id="b19dcf10-3e88-49f5-8264-9c34f1332bf4" href="tasks/p2-11.md">ROB-716</issue> — P2-11 — TRACKING: Complete clocks/deadlines, entropy, and platform queries | **TRACKING** | Correct conversion. Remove ready-for-agent; children 11a–c own implementation. Wait users should depend directly on 11a. |
| <issue id="584902bc-3708-457f-916b-d52c9bc56a36" href="tasks/p2-12.md">ROB-723</issue> — P2-12 — Build the complete static-musl conformance suite from the host contract | **KEEP** | Strong. Generate positive/negative/race/error tests from contract and publish behavior-level coverage, not syscall-name coverage. |
| <issue id="e8ac06f9-b301-43a8-ab33-f3a669c2256f" href="tasks/p2-13.md">ROB-717</issue> — P2-13 — Run one-hour four-vCPU contention and randomized preemption qualification | **AMEND** | Run only on P0-16-approved semantic profiles; define exact liveness/watchdog/resource criteria and preserve first failure. |
| <issue id="5898c161-ea16-49fa-8a0c-33640d648891" href="tasks/p2-14.md">ROB-720</issue> — P2-14 — Audit and freeze the bounded BEAM host contract revision 2 | **AMEND** | Define boundedness by semantic state-machine depth, code/test/unsafe surface, and excluded families—not merely syscall count. |
| <issue id="05803b21-860c-4b52-b7f8-429ed3782f9f" href="gates/gate-2.md">ROB-721</issue> — GATE-2 — Decide whether the ERTS host contract is bounded and trustworthy | **GATE** | Add hard blockers for unexplained wait workaround, signal-frame uncertainty, time/entropy substitution, fd/poll lifetime gap, or shootdown failure. |
| <issue id="0bb42463-1fbb-4af4-9855-81763312d45c" href="tasks/p2-00.md">ROB-783</issue> — P2-00 — Prove the AArch64 atomic and memory-ordering foundation for SMP | **KEEP** | Excellent. Do not use it to defer M1 IRQ/locking policy. Keep negative litmus/model evidence and emitted-instruction audit. |
| <issue id="a9b709e2-77b4-4f42-b42b-69da97161c0c" href="tasks/p2-05a.md">ROB-784</issue> — P2-05a — Bring up secondary CPUs, per-CPU state, timers, and GIC routing | **KEEP** | Strong, self-contained child. Ensure platform drift and failed CPU start remain explicit failures. |
| <issue id="18c87017-a773-4df7-9c02-263b0d961774" href="tasks/p2-05b.md">ROB-785</issue> — P2-05b — Make scheduling, blocking, wakeups, and task migration SMP-correct | **KEEP** | Strong. It owns P1-13’s deferred migration tests and exact task-conservation evidence. |
| <issue id="69230028-97d5-4d02-aca3-ac1d140f8d85" href="tasks/p2-05c.md">ROB-786</issue> — P2-05c — Implement acknowledged cross-CPU TLB shootdowns and concurrent VM safety | **KEEP** | Strong. Ensure all VM/address-space destruction and reuse paths are dependency-linked. |
| <issue id="49a8d73e-a114-4b9d-98dd-b4d471af0bb3" href="tasks/p2-06a.md">ROB-787</issue> — P2-06a — Implement the admitted clone/thread-start and TLS contract | **KEEP** | Strong. Exact pinned musl call pattern and pre-publication rollback are appropriate. |
| <issue id="a95535f6-c35f-4942-8c53-209c7300210f" href="tasks/p2-06b.md">ROB-788</issue> — P2-06b — Implement thread exit, clear-child-TID wake, join/detach, and reclamation | **KEEP** | Strong. Add explicit relation to P2-08 and prove last-thread process teardown. |
| <issue id="90c2d00c-1514-4541-a5fa-b74275a31a1c" href="tasks/p2-10a.md">ROB-789</issue> — P2-10a — Implement bounded byte streams and descriptor lifecycle semantics | **KEEP** | Strong child. Confirm exact open-file-description/dup sharing whenever admitted; preserve generation-safe close/reuse and bounded byte/object accounting. |
| <issue id="d8900819-9d6b-4729-ac14-515171580562" href="tasks/p2-10b.md">ROB-790</issue> — P2-10b — Implement poll/ppoll registration, readiness, timeout, close, and reuse races | **KEEP** | Strong child. Depend directly on P2-11a for deadlines and P2-09c for signal interruption; preserve check/register/recheck proof. |
| <issue id="89beab3f-83f8-4aeb-85f4-fb650aac7e54" href="tasks/p2-09a.md">ROB-791</issue> — P2-09a — Implement signal dispositions, masks, pending state, and target selection | **KEEP** | Strong child. Replace tracking-parent dependencies with completed implementation children where practical; keep exact admitted signal subset. |
| <issue id="32394ed7-20e7-411a-9bbc-38da9a016273" href="tasks/p2-09b.md">ROB-792</issue> — P2-09b — Implement AArch64 signal frames, alternate stack, FPSIMD context, faults, and rt_sigreturn | **KEEP** | Excellent security-critical child. After P1-08 split, depend on P1-08b; retain forged-frame and unsupported-context fail-closed tests. |
| <issue id="149128b1-6459-49ce-beef-4f94977ba57c" href="tasks/p2-09c.md">ROB-793</issue> — P2-09c — Integrate signal interruption, restart, cancellation, and wait-race semantics | **KEEP** | Strong child. Depend directly on P2-11a rather than tracking parent; retain one-terminal-outcome conservation and absolute deadlines. |
| <issue id="dc25a9b4-432c-48dc-b94b-d3f084c1009d" href="tasks/p2-11a.md">ROB-794</issue> — P2-11a — Implement counter-based clocks, absolute deadlines, sleeps, and timer cancellation | **AMEND** | Strong child. If realtime is admitted, freeze PL031 or immutable boot epoch explicitly; timed wait users depend directly on this child. |
| <issue id="7c62097b-c0d3-49de-8f20-1977351e31d5" href="tasks/p2-11b.md">ROB-795</issue> — P2-11b — Implement boot entropy, virtio RNG, AT_RANDOM, and bounded getrandom semantics | **KEEP** | Strong child. Audit exact VirtIO VERSION_1/status/reset/DMA path; production/qualification must structurally reject deterministic mode. |
| <issue id="c54813fe-6009-4a4f-9886-6ef219de7e24" href="tasks/p2-11c.md">ROB-796</issue> — P2-11c — Implement bounded platform identity, limits, CPU-count, and affinity queries | **KEEP** | Strong child. Keep one generated source of truth and host-leak scan; link auxv/query consistency to P0-14 and P2-02. |

## M3

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="db243d4d-5f34-4285-a4a9-910dff24bdcf" href="tasks/p3-01.md">ROB-728</issue> — P3-01 — Package and load the pinned upstream beam.smp inside the guest | **AMEND** | Revalidate exact ELF/release closure at image time; no alternate artifact, host helper, dynamic object, or undeclared environment. |
| <issue id="f9746200-20c9-4a53-94c4-07a3da6c4403" href="tasks/p3-02.md">ROB-727</issue> — P3-02 — Reach ERTS pre-initialization and report the pinned runtime identity | **KEEP** | Good incremental milestone. Include last progress event, thread/map/syscall snapshot, and deterministic abort evidence. |
| <issue id="0ad1f35d-019e-4981-baed-49e1f5ddf4b5" href="tasks/p3-03.md">ROB-725</issue> — P3-03 — Boot kernel and stdlib in embedded noninteractive mode | **AMEND** | Clarify dependency with P3-04: either combine module-loader bootstrap with this ticket or define a minimal independently testable loader milestone. |
| <issue id="7f27417e-2d0f-4707-b07c-fbcfb2879b79" href="tasks/p3-04.md">ROB-726</issue> — P3-04 — Validate ERTS module loading against the immutable release tree | **AMEND** | Specify executable fault injection through malformed/missing/corrupt BEAM and path cases without requiring a boot state that already assumes success. |
| <issue id="1ad4c47c-9147-40ce-9f9e-e551cd1a1f6c" href="tasks/p3-05.md">ROB-734</issue> — P3-05 — Exercise Erlang processes, messages, timers, ETS, binaries, and GC | **KEEP** | Good workload. Bound memory and include failure/cleanup assertions, not only successful operations. |
| <issue id="be5f618d-ea32-42bb-860a-8040a7664f7b" href="tasks/p3-06.md">ROB-732</issue> — P3-06 — Bring ERTS to the final two-scheduler SMP profile | **AMEND** | Use barrier-synchronized CPU work and overlapping per-vCPU/OS-thread evidence. Online threads are not concurrency proof. |
| <issue id="3299c224-adba-422a-b6fc-8771995aa293" href="tasks/p3-07.md">ROB-729</issue> — P3-07 — Close ERTS-discovered host-contract defects without semantic runtime patches | **KEEP** | Correct repair seam. Every new syscall/flag is a contract change requiring tests and human review. |
| <issue id="7a02f35d-a034-44f1-9631-62ee80b32fa9" href="tasks/p3-08.md">ROB-730</issue> — P3-08 — Qualify 100 boots and 10,000 Erlang-process lifecycle | **AMEND** | Separate boot reliability and process lifecycle ledgers; preserve first failure, cleanup exactness, and runner classification. |
| <issue id="818117b5-a6fe-48f1-88de-d0524d320ad5" href="tasks/p3-09.md">ROB-733</issue> — P3-09 — Run the 12-hour ERTS stress and memory-stability qualification | **AMEND** | Replace qualitative stability with pre-frozen warm-up/slope/confidence/resource rules and runner capacity. |
| <issue id="a463f0fa-624b-434a-a2d8-03f87023b3d6" href="tasks/p3-10.md">ROB-731</issue> — P3-10 — Audit upstream integrity and publish the central feasibility evidence | **KEEP** | Strong central evidence ticket. Include complete native/release closure and all accepted exceptions. |
| <issue id="fe106509-2398-4890-8a86-5d6e7738e1af" href="gates/gate-3.md">ROB-735</issue> — GATE-3 — Decide whether standard upstream ERTS on the custom OS is proven | **GATE** | Continue only with objective SMP, memory, boot, upstream-diff, and unknown-call evidence. |

## M4

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="01bcb96d-9882-471b-9210-3c72eeea7bb1" href="tasks/p4-01.md">ROB-736</issue> — P4-01 — Extend system.toml and the boot plan for renderer/BEAM IPC resources | **AMEND** | Define capability/resource IDs, limits, duplicate/conflict rules, compile-time validation, build-plan hash, and exact fd/handle provisioning. |
| <issue id="b69fcb9a-d0b1-4a12-afa0-a8cd870efbf0" href="tasks/p4-02.md">ROB-741</issue> — P4-02 — Boot the genuine runtime_lab Mix release inside the custom OS | **KEEP** | Strong. Ensure exact P0 payload/ERTS pairing and zero host shell/exec/native dependency. |
| <issue id="7cbdc8ec-ef1b-445a-a871-65c488298ec4" href="https://linear.app/robert-guss/issue/ROB-739/p4-03-implement-final-runtime-lab-supervision-and-restart-persistent">ROB-739</issue> — P4-03 — Implement the final runtime_lab supervision and durable demo-state model | **AMEND** | Rename to supervisor-resilient in-memory state; document and test reset on BEAM/OS restart. |
| <issue id="a4f0c083-dab2-4057-990c-38611d085681" href="tasks/p4-04.md">ROB-740</issue> — P4-04 — Implement kernel-provisioned bounded UI streams and ERTS fd mapping | **AMEND** | Kernel is bounded byte stream only; freeze capacity/atomicity/close/poll behavior and exact fd numbers; no second packet prefix. |
| <issue id="c9120fc3-99a5-408b-beb7-06fb5b34eab4" href="tasks/p4-05.md">ROB-743</issue> — P4-05 — Implement the bounded Rust ETF codec and packet framing | **AMEND** | Add compressed-term policy, atom allowlist, depth/arity/binary/integer/trailing-byte limits, allocation accounting, and differential fuzzing. |
| <issue id="d70e5cf2-a0e2-4659-a820-b100ba17b52b" href="tasks/p4-06.md">ROB-746</issue> — P4-06 — Connect Elixir to fixed descriptors with an fd port | **AMEND** | Allow unchanged upstream built-in fd port driver; prohibit project/dynamic drivers/NIFs. Add packet_size and busy limits. |
| <issue id="473e284a-c4e5-40b4-b5a8-fafe08e69b4f" href="tasks/p4-07.md">ROB-745</issue> — P4-07 — Implement protocol handshake, sequencing, snapshots, patches, events, and metrics | **AMEND** | Define current-session sequence semantics, terminal action outcomes, application-state/native-telemetry namespaces, and reconnection wrap/reset. |
| <issue id="643387ad-424e-4991-922a-b49e94d7f9b9" href="tasks/p4-08.md">ROB-738</issue> — P4-08 — Enforce UI backpressure, disconnect, reconnect, and last-valid-model behavior | **KEEP** | Good. Add exact queue counts/bytes, producer blocking policy, replacement/coalescing eligibility, and fairness. |
| <issue id="1523729a-103f-4c98-808d-31e9abf1943f" href="tasks/p4-09.md">ROB-742</issue> — P4-09 — Qualify the Rust loopback service with one million messages and malformed input | **AMEND** | Use mixed sizes/directions, saturation, closure, reconnect, malformed/decompression bombs, resource slopes, and sequence conservation. |
| <issue id="dbf652fb-c382-4cb8-846a-c139e12dc2df" href="tasks/p4-10.md">ROB-744</issue> — P4-10 — Qualify 1,000 supervised crashes and restart-intensity escalation | **KEEP** | Good. Distinguish feature restart, supervisor escalation, release exit, and state reset. |
| <issue id="ce7f6763-1751-4a62-9248-aa9a0ee50d21" href="gates/gate-4.md">ROB-737</issue> — GATE-4 — Decide whether the Elixir release and Rust IPC boundary are ready for GUI work | **GATE** | Require corrected fd-driver policy, protocol bounds, terminal action ledger, and objective leak/backpressure evidence. |

## M5

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="74e3ebd6-dfb7-49b3-afe6-d1f4d9f8e427" href="https://linear.app/robert-guss/issue/ROB-751/p5-01-integrate-the-selected-virtio-gpu-transport-into-the-kernel">ROB-751</issue> — P5-01 — Integrate the selected virtio GPU transport into the kernel device layer | **SPLIT/TRACK** | Split transport/status/features/reset, 2D resource/scanout, and transfer/flush/fence/error. Block on P5-00. |
| <issue id="4abe03e0-2d22-47c7-9468-03c5be4d6583" href="tasks/p5-02.md">ROB-747</issue> — P5-02 — Integrate virtio pointer input and normalize semantic pointer events | **AMEND** | Freeze exact QEMU input frontend/device mapping, coordinate transform, press/release conservation, coalescing, reset, and hot-loss behavior. |
| <issue id="e19bcf37-bd3d-4e05-866d-c0c9810cc7be" href="https://linear.app/robert-guss/issue/ROB-754/p5-03-build-the-isolated-native-rust-renderer-process-and-device">ROB-754</issue> — P5-03 — Build the isolated native Rust renderer process and device capabilities | **SPLIT/TRACK** | Split process/capability bootstrap, display-surface client, and render/event/IPC loop. Block on P5-00. |
| <issue id="9abecb77-11a0-472b-aed7-222667e5fa9d" href="https://linear.app/robert-guss/issue/ROB-748/p5-04-freeze-the-toolkit-neutral-uibackend-and-slint-license-decision">ROB-748</issue> — P5-04 — Freeze the toolkit-neutral UiBackend and Slint license decision | **AMEND** | Rename to verify/integrate the P0-15-frozen decision. No duplicate decision authority. |
| <issue id="ba439449-281d-4135-9d15-45568b36309c" href="tasks/p5-05.md">ROB-753</issue> — P5-05 — Implement the opinionated Runtime Lab shell, theme, fonts, and native heartbeat | **AMEND** | Enforce single renderer-thread Slint rule, bundled font determinism, bounded layout, local heartbeat independent of BEAM and protocol queues. |
| <issue id="4ec344df-eb41-4c9d-a22e-617a71a0241e" href="tasks/p5-06.md">ROB-750</issue> — P5-06 — Render Elixir-controlled cards and apply snapshots/patches safely | **AMEND** | Keep feature state authoritative in Elixir; overlay native telemetry separately; validate full next state before atomic swap. |
| <issue id="be93867a-58d8-4364-88ef-deb310a0f688" href="tasks/p5-07.md">ROB-755</issue> — P5-07 — Connect pointer actions through Rust, kernel IPC, ERTS port, and Elixir | **AMEND** | Define accepted/terminal outcomes, current-session sequence, disabled/pending behavior, and disconnect at each stage. |
| <issue id="e314449d-9901-43aa-b10b-6f6e095c157c" href="tasks/p5-08.md">ROB-756</issue> — P5-08 — Expose runtime identity, kernel metrics, and bounded stress controls | **AMEND** | Separate native telemetry from feature model; pin sources/units/staleness and avoid telemetry echo loop. |
| <issue id="9cfadd24-e836-4672-adb3-9a180564766a" href="tasks/p5-09.md">ROB-752</issue> — P5-09 — Implement the Crash Feature flow and visible supervised recovery | **AMEND** | Replace durable with supervisor-resilient in-memory state; define state reset and whole-release-exit behavior. |
| <issue id="b72c3a78-d49b-4269-a904-87f8835206b6" href="tasks/p5-10.md">ROB-749</issue> — P5-10 — Implement BEAM disconnect, reconnect, resnapshot, and last-valid-view UX | **KEEP** | Strong. Add session-generation invalidation and exact resource baseline after repeated cycles. |
| <issue id="adeb9424-74cc-4388-8346-8d91b6178835" href="https://linear.app/robert-guss/issue/ROB-760/p5-11-instrument-event-to-pixel-latency-frame-cadence-freezes-and">ROB-760</issue> — P5-11 — Instrument event-to-pixel latency, frame cadence, freezes, and memory | **AMEND** | Rename to event-to-present-completion unless host observer exists; freeze clock domains/error, sample policy, and observer-effect bound. |
| <issue id="e8b2b717-96cf-4a9e-a3d8-35dba7fa8b67" href="tasks/p5-12.md">ROB-758</issue> — P5-12 — Build QMP screenshot and visual-regression checks | **KEEP** | Good paired semantic/visual evidence. Treat QMP capture timing as visual evidence, not precise host-visible latency. |
| <issue id="14465095-5b0b-469f-9ce5-dea9b6ff618a" href="tasks/p5-13.md">ROB-759</issue> — P5-13 — Run the interactive Apple Silicon HVF acceptance demonstration | **AMEND** | Calibrate provisional thresholds to frozen Mac/QEMU/resolution/instrumentation; report guest completion proxy and human-visible observations separately. |
| <issue id="290b468f-1acc-4df1-80c8-df209810365c" href="gates/gate-5.md">ROB-757</issue> — GATE-5 — Decide whether the interactive Rust/Elixir vertical slice is worth qualifying | **GATE** | Require P5-00, corrected metrics, calibrated thresholds, exact action ledger, and explicit UI/license compliance. |

## M6

| Issue | Action | Required correction / disposition |
| -- | -- | -- |
| <issue id="2e654860-ede7-498a-b157-2c18eebea534" href="tasks/p6-01.md">ROB-761</issue> — P6-01 — Freeze the final qualification contract and runner profiles | **AMEND** | Freeze objective statistics and canonical commit/image; define isolated worktrees for exercises and invalid-run/retry policy. |
| <issue id="0c6cc41f-c0e5-4c3d-8b18-0d0c13c8680d" href="tasks/p6-02.md">ROB-764</issue> — P6-02 — Qualify 100 clean boots of the complete image | **AMEND** | Define outlier classification before run; all 100 must pass without retried-away failures; discrete cleanup exactness. |
| <issue id="5f18d9b1-a204-4e15-9536-ef815ec67445" href="tasks/p6-03.md">ROB-762</issue> — P6-03 — Run the 12-hour complete-system mixed stress qualification | **AMEND** | Use frozen warm-up/slope/confidence/resource criteria and deterministic workload schedule; classify host/runner invalidity separately. |
| <issue id="ac59e550-b296-402e-ad34-c0175de05220" href="tasks/p6-04.md">ROB-765</issue> — P6-04 — Qualify 10,000 scripted UI actions with complete sequence accounting | **KEEP** | Strong. Terminal outcomes must use the F-16 definition and event metric must use present completion. |
| <issue id="cf195cde-2b49-4c81-a5f2-e679f7facd72" href="tasks/p6-05.md">ROB-766</issue> — P6-05 — Prove reproducible image builds, provenance, SBOM, and license completeness | **AMEND** | Run against canonical image after retained changes; include vendored/checksummed sources and complete native/release/assets closure. |
| <issue id="4ee27d08-7520-43e6-893d-76a538962e90" href="tasks/p6-06.md">ROB-768</issue> — P6-06 — Run AI exercise A: add a high-level scheduler-utilization card | **AMEND** | Pin exact OTP metric/API/flags, scheduler classes, sampling formula and overhead; run in isolated branch/image. |
| <issue id="3d832396-ae2e-4120-b5bc-a67a71fc763c" href="tasks/p6-07.md">ROB-771</issue> — P6-07 — Run AI exercise B: add a cross-boundary page-pressure capability | **AMEND** | Run in isolated branch/image; define exact metric formula and capability; retained changes force new canonical qualification. |
| <issue id="f031c483-208b-48f1-9c20-306baec49d25" href="tasks/p6-08.md">ROB-763</issue> — P6-08 — Run AI exercise C: change theme and feature composition by rebuilding the image | **AMEND** | Use isolated variant receipts; do not mutate canonical qualification image; prove disabled resources absent. |
| <issue id="7d6b059f-23ab-4e78-81a4-a610ff20a11b" href="tasks/p6-09.md">ROB-767</issue> — P6-09 — Conduct the final security-boundary, fault-model, dependency, and upstream audit | **AMEND** | Include platform/HWCAP, FP, cache/TLB, VirtIO, display-surface, user-copy, release-native closure, source ledger, and prior-art claim audit. |
| <issue id="f49e44df-274c-42aa-9a33-0679bd6a31f5" href="tasks/p6-10.md">ROB-770</issue> — P6-10 — Score H1–H6 and publish the final POC evidence report | **AMEND** | Use only Pass/Conditional/Fail; treat Promising as narrative. Cite both confirming and falsifying evidence and every exception. |
| <issue id="a060e17f-3f48-463a-9fc8-816249950496" href="gates/gate-6.md">ROB-769</issue> — GATE-6 — Choose Continue, Pivot, Narrow, or Stop after the completed POC | **GATE** | Good final investment gate. Require canonical evidence and no phone/production-security overclaim. |

---

# 11. Corrected gate criteria

## GATE-0 — Authorize M1 only if

* exact target ERTS/release artifact closure is static and declared;
* authoritative AArch64 Linux runs pass;
* Mix pairing and direct launch pass read-only;
* host contract covers source + trace + error paths;
* machine/CPU/HWCAP/atomics/device baseline is frozen;
* TCG/HVF display, input, and Slint probes pass;
* Slint/replacement license is explicitly approved;
* VirtIO conformance obligations are understood and tractable;
* runner campaigns are feasible and preflighted;
* prior-art liveness failures are dispositioned;
* no semantic ERTS workaround, unknown syscall, or unexplained trace gap remains;
* user explicitly records **Authorize M1**.

## GATE-1 — Authorize M2 only if

* platform identity cannot drift;
* single-core exception, IRQ, preemption, lock, wait, and user-copy invariants pass;
* physical/virtual memory and process teardown reconcile exactly;
* ELF staging/publication, W^X, D/I cache, TLB, and ASID reuse pass;
* EL0 FP/AdvSIMD is isolated on single CPU;
* 1,000 boots and high-switch tests pass without retries hiding failure;
* no unclassified fault or unchecked unsafe obligation remains.

## GATE-2 — Authorize ERTS integration only if

* P2-00 atomics/order and P2-05a–c SMP/shootdowns pass;
* clone/TLS/exit/join/robust cleanup match pinned musl;
* futex compare-and-block/wake/timed/interruption semantics pass;
* signals including AArch64 frame/FP/rt_sigreturn/restart/cancellation pass;
* fd/open-file-description/pipe/poll/close semantics pass;
* monotonic/realtime/entropy/AT_RANDOM paths pass;
* generated contract conformance has no orphan behavior;
* one-hour contention shows forward progress and exact cleanup;
* no semantic workaround or broad Linux scope expansion is accepted.

---

# 12. Recommended execution order now

 1. <issue id="b4946023-20dd-42eb-9602-8ad05ff6d505" href="tasks/p0-01.md">ROB-684</issue> repository/evidence shell.
 2. <issue id="fe0297d9-02f5-4bf6-bd2f-009d1830eb00" href="tasks/p0-02.md">ROB-683</issue> reference Mix application.
 3. <issue id="74423d8a-8cce-4677-a5fa-c6ce3659f423" href="tasks/p0-03.md">ROB-685</issue> toolchain/source pinning.
 4. In parallel after those foundations:
    * <issue id="ec32ea87-c5cc-4357-84ba-69994eebf60d" href="tasks/p0-04.md">ROB-686</issue> reference trace/source inventory;
    * <issue id="8487cc59-d6ea-45c4-a581-dd4a428639dd" href="tasks/p0-05.md">ROB-688</issue> target ERTS build/closure;
    * <issue id="74286a8a-0043-4329-bf5b-abeed170b067" href="tasks/p0-09.md">ROB-687</issue> protocol spec;
    * <issue id="a927064b-f115-42f4-b88f-121f9fb8e479" href="tasks/p0-17.md">ROB-780</issue> prior-art audit/reproduction.
 5. <issue id="2af8ae81-9e36-4561-b564-99804af0675d" href="tasks/p0-06.md">ROB-693</issue> authoritative AArch64 Linux run.
 6. <issue id="24259af1-bbeb-4a57-9cdb-f66230f85e26" href="tasks/p0-07.md">ROB-692</issue> Mix release pairing.
 7. <issue id="a0789a32-63c5-4bcb-aea1-adec3fa938be" href="tasks/p0-08.md">ROB-690</issue> contract revision 1.
 8. <issue id="98c3c525-b06f-4f2c-9757-134015d632e9" href="tasks/p0-10.md">ROB-689</issue> protocol endpoint stress.
 9. <issue id="760ef061-bde7-4e22-92e2-a620d09a4e55" href="tasks/p0-11.md">ROB-696</issue> then <issue id="8a611583-4865-4e56-a285-2ee7f72d2dbf" href="tasks/p0-12.md">ROB-694</issue> device probes.
10. <issue id="6444be9e-b65a-48c4-b235-59cde0aee94f" href="tasks/p0-14.md">ROB-777</issue> platform baseline.
11. <issue id="7101c1b4-a2a0-4df5-ac65-3cf1ff65aa10" href="tasks/p0-15.md">ROB-778</issue> Slint/license proof.
12. <issue id="16294855-9131-4ca5-b9de-063b3da7b9d9" href="tasks/p0-16.md">ROB-779</issue> runner qualification.
13. <issue id="096905ea-8f1b-4a74-b35c-a82e066e3359" href="tasks/p0-13.md">ROB-691</issue> evidence/ADR freeze.
14. <issue id="43469151-2127-4c4b-aa61-41c010ff6e2a" href="gates/gate-0.md">ROB-695</issue> human Gate 0.

Do not create kernel code merely because an implementation agent is available. The first kernel task is <issue id="f05b5e88-799d-4488-878a-3d208bb49c81" href="tasks/p1-01.md">ROB-698</issue> **only after** Gate 0 explicitly authorizes it.

---

# 13. Source-verification conclusions

The audit’s technical conclusions are grounded in current official documentation/source and close primary prior art:

* Current OTP supports cross compilation and build-time exclusion/disable options, but nonstandard targets are not equivalent to a supported custom kernel; the exact build must be experimentally proven.
* Mix releases are target architecture/OS/ABI sensitive and can include or point to an exact ERTS installation; pairing is a real Gate 0 risk.
* QEMU Arm `virt` has versioned machine types and accelerator/CPU behavior that differs between TCG and HVF/KVM; bare `virt` and `-cpu max` are not a durable ABI.
* Rust’s `aarch64-unknown-none` hard-float target assumes FP/AdvSIMD, creating an OS context obligation.
* The pinned VirtIO implementation must be audited against the VirtIO specification; crate support labels are not conformance proof.
* ERTS fd ports are an upstream built-in port-driver facility, so banning all linked-in drivers contradicts the chosen boundary.
* ETF safe decoding does not replace schema, atom, size, depth, and decompression limits.
* Slint’s `no_std` software-renderer path has a real single-thread safety contract and a material distribution-license decision.
* Tyn is meaningful feasibility evidence for a small Rust kernel hosting upstream ERTS, but its own reported futex/thread-progress and TCG history is warning evidence, not proof for this AArch64/HVF design.
* Linux ABI details such as open-file descriptions, clear-child-TID/futex join, robust lists, signal frames, restart behavior, and poll/close races are coupled protocols, not isolated syscall stubs.

---

# 14. Final decision statement

The architecture is worth testing. It is **not yet justified to build the kernel**.

The correct next move is not to abandon the project and not to start M1. It is to execute M0 rigorously, let Gate 0 kill or narrow bad assumptions cheaply, and only then authorize the custom-kernel investment.

This review should be considered superseded only by:

1. an updated architecture document incorporating these corrections;
2. corrected Linear descriptions/relations/labels;
3. actual M0 evidence;
4. a human-approved Gate 0 decision.
