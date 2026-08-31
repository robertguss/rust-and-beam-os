---
schema: "repo-plan/v1"
id: "RB-T-P504"
title: "Verify and integrate the frozen UiBackend, toolkit, and license decision"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M5"
parent: null
depends_on:
  - "RB-T-P500"
  - "RB-T-P015"
  - "RB-E-P503"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P5-04"
x_linear_id: "ROB-748"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-748/p5-04-verify-and-integrate-the-frozen-uibackend-toolkit-and-license"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P504: Verify and integrate the frozen UiBackend, toolkit, and license decision

## Goal

Adopt a productive POC UI toolkit without coupling device/kernel interfaces or silently imposing an unwanted project license.

## Context

[Architecture & Validation Plan](<../architecture.md>)

The kernel owns virtio setup, DMA, interrupts, and exclusive device authorization. The isolated Rust renderer draws and presents through native capabilities. Elixir owns dynamic feature state/behavior. The native heartbeat must not depend on BEAM.

Blocked by: RB-E-P503.

## Deliverables

* Define a project-owned `UiBackend` trait for framebuffer access, dimensions/format, monotonic time, redraw requests, pointer dispatch, presentation, and error/reset state.
* Implement the chosen Slint `no_std` custom platform and software-renderer adapter behind that trait.
* Record the exact Slint version/features, GPLv3 open-source path, distribution implications, process boundary, generated-code treatment, and replacement seam in an ADR.
* Create a minimal alternate/mock backend used by host tests so protocol/domain tests do not require Slint.

## Acceptance criteria

- [ ] No Slint type crosses the native kernel ABI or Rust↔BEAM protocol.
- [ ] Renderer business/protocol state can be tested through the mock backend.
- [ ] A basic Slint component renders through the software renderer in the guest.
- [ ] The license ADR is explicit, reviewed by the user, and consistent with an open-source POC.
- [ ] If GPLv3 is rejected, this issue selects a replacement before downstream UI work starts.

## Verification

* `just test-ui-backend`
* `just render-ui-minimal`
* `just license-check`

## Evidence

* Run mock-backend tests and guest minimal-component rendering.
* Inspect dependency/license/SBOM output.
* Review the toolkit replacement boundary in a fresh session.

## Out of scope

* GPU acceleration, browser/web runtime, Android UI compatibility, networking, writable storage, audio/camera/sensors, and physical phone hardware.
* Sending drawing commands or executable UI code from Elixir.
* Moving virtio queues, DMA, or unrestricted MMIO into the renderer.

## Additional context
### Completion rule

Done requires both semantic and visual evidence from the exact guest. A screenshot alone cannot prove correctness; every state must correlate with protocol, runtime, and kernel evidence.
### Learning checkpoint

Explain device-versus-renderer ownership, the click-to-pixel path, the failure boundary this slice demonstrates, and what measurement would falsify the design.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Rename to verify/integrate the RB-T-P015-frozen decision. No duplicate decision authority.
### Normative readiness correction — 2026-08-30

RB-T-P015 owns the toolkit and license decision. This issue only verifies and integrates that frozen decision. Replacing it requires a new human-approved ADR.
