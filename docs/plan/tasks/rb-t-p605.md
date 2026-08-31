---
schema: "repo-plan/v1"
id: "RB-T-P605"
title: "Prove reproducible image builds, provenance, SBOM, and license completeness"
type: "task"
state: "open"
priority: "P3"
milestone: "RB-M-M6"
parent: null
depends_on:
  - "RB-T-P601"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P6-05"
x_linear_id: "ROB-766"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-766/p6-05-prove-reproducible-image-builds-provenance-sbom-and-license"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P605: Prove reproducible image builds, provenance, SBOM, and license completeness

## Goal

Show that AI-assisted composition produces traceable, byte-reproducible system images rather than opaque snowflakes.

## Context

[Architecture & Validation Plan](<../architecture.md>)

This milestone qualifies the completed emulator POC; it does not add new product scope. The exact guest remains AArch64 QEMU `virt`, built in reproducible Linux environments and evaluated interactively on Apple Silicon/HVF.

Blocked by: RB-T-P601.

## Deliverables

* Build the complete image twice from clean independent Linux environments using the same pinned inputs and no shared output cache.
* Compare kernel, renderer, ERTS, release, archive, boot plan, and final image digests; localize any mismatch.
* Generate provenance/build receipts, dependency/source hashes, patch inventory, SPDX-style SBOM, and license bundle.
* Remove timestamps, paths, ordering, random IDs, and other nondeterminism rather than excluding them casually.

## Acceptance criteria

- [ ] Two clean builds produce the same final image digest.
- [ ] Every binary and packaged file traces to declared source/input and build command.
- [ ] SBOM and license bundle cover Rust crates, musl, OTP, Elixir, Slint, fonts/assets, tools packaged in the image, and project code.
- [ ] The OTP diff and UI-license decisions match prior approved ADRs.
- [ ] No undeclared network download occurs during the sealed build.

## Verification

* `just build-sealed`
* `just verify-reproducible-image`
* `just sbom-check`
* `just license-check`

## Evidence

* Run two clean sealed builds and component-level binary diff on mismatch.
* Validate SBOM/licenses/provenance links.
* Publish the reproducibility report and image digest.

## Out of scope

* New kernel/runtime/UI features not required by qualification.
* JIT, second hardware target, networking, persistent writable storage, update slots, phone drivers, or production security.
* Hiding failed runs, retroactively weakening thresholds, or presenting the emulator POC as a daily-driver phone OS.

## Additional context
### Completion rule

Done requires the frozen qualification contract, exact image/build provenance, raw and summarized evidence, and honest classification of every failure or exception.
### Learning checkpoint

Explain what the evidence proves, what it does not prove, one source of measurement bias, and the strongest fact that could justify stopping or pivoting.
### Implementation-readiness disposition — 2026-08-30

**Action:** AMEND

Run against canonical image after retained changes; include vendored/checksummed sources and complete native/release/assets closure.
### Normative readiness correction — 2026-08-30

Run reproducibility, provenance, SBOM, and license checks against the canonical image after all retained changes. Include vendored/checksummed sources and the complete native, release, and asset closure.
