---
schema: "repo-plan/v1"
id: "RB-T-P500"
title: "Freeze the display-surface, buffer-ownership, and present-completion ABI"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P114"
  - "RB-T-P107"
  - "RB-E-P105"
  - "RB-T-P012"
  - "RB-T-P011"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-00"
x_linear_id: "ROB-802"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-802/p5-00-freeze-the-display-surface-buffer-ownership-and-present"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P500: Freeze the display-surface, buffer-ownership, and present-completion ABI

## Goal

Lock the exact protected boundary by which the renderer writes pixels and requests presentation while the kernel retains exclusive VirtIO/DMA/device ownership.

## Context

Blocked by RB-T-P011, RB-T-P012, RB-E-P105, RB-T-P107, and RB-T-P114.
Blocks RB-E-P501, RB-E-P503, RB-T-P504, and all renderer integration.

## Deliverables

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

## Acceptance criteria

* Renderer can draw and present continuously without direct MMIO, VirtIO queue, or DMA authority.
* ERTS/unrelated processes cannot map or present the surface.
* Invalid/stale handle, generation, buffer state, frame sequence, or rectangle is rejected without device action.
* No queued/displayed page is reclaimed or remapped before safe completion/reset.
* Renderer crash and device reset leak no resource and cannot corrupt another process.
* Event-to-present-completion is measurable and explicitly not called host-visible pixel time.
* Double-buffer ownership survives stress, delayed/duplicate completion, and forced reset.

## Verification

* Capability-denial and mapping tests.
* Buffer-state model/property tests.
* Delayed/duplicate/stale completion injection.
* Renderer crash/device reset/restart tests.
* DMA/page-lifetime audit and trace replay.
* TCG/HVF probe using the frozen device transport.

## Evidence

* Capability-denial and mapping tests.
* Buffer-state model/property tests.
* Delayed/duplicate/stale completion injection.
* Renderer crash/device reset/restart tests.
* DMA/page-lifetime audit and trace replay.
* TCG/HVF probe using the frozen device transport.

## Out of scope

GPU acceleration, direct userspace VirtIO, arbitrary resolution changes, third-party processes, shared BEAM framebuffer access, or physical display hardware.

## Additional context
### Why this is a blocker

“Renderer draws and presents through a display handle” is not an implementation contract. Copy syscalls, shared surfaces, direct queue access, and unrestricted mapped device memory have very different performance, isolation, lifetime, and fault behavior.
### Locked POC decision

Use two kernel-owned page-backed software-rendering surfaces mapped writable and execute-never into the renderer only. The kernel owns VirtIO resources, queues, DMA/pinning, scanout, interrupts, reset, and reclamation.
### Completion rule

Done means pixel memory, device authority, buffer ownership, present completion, reset, and reclamation form one versioned capability ABI with model and guest evidence.
