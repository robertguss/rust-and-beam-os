---
schema: "repo-plan/v1"
id: "RB-T-ORBSETUP"
title: "Prepare Amp orb setup and resume lifecycle"
type: "task"
state: "done"
priority: "P3"
milestone: "RB-M-M0"
parent: null
depends_on: []
related: []
actor: "agent"
owner: null
defer_until: null
evidence:
  - "docs/evidence/phase-0/RB-T-ORBSETUP/evidence.json"
---

# RB-T-ORBSETUP: Prepare Amp orb setup and resume lifecycle

## Goal

Make fresh Amp orbs install the repository's candidate Phase 0 toolchain and
dependencies once, then expose them to later non-interactive login shells.

## Context

- [Development bootstrap](../../development.md)
- [Orb lifecycle documentation](https://ampcode.com/docs/orbs)

This is repository development-environment work only. It does not freeze the
P003 toolchain contract or authorize kernel implementation.

## Deliverables

- [x] Add idempotent `.agents/setup` and fast `.agents/resume` lifecycle
      scripts.
- [x] Reuse the pinned repository bootstrap instead of duplicating tool
      versions.
- [x] Persist Cargo/Rust/`just` availability for non-interactive login shells.
- [x] Ignore generated orb portal metadata without hiding tracked service
      config.

## Acceptance criteria

- [x] Setup succeeds twice in the current orb and the warm run avoids
      reinstalls.
- [x] A clean non-interactive login shell finds Rust 1.89.0, Cargo 1.89.0, and
      `just` 1.42.4 from `$HOME/.cargo/bin`.
- [x] Resume succeeds in under 10 seconds and performs no installation or
      network work.
- [x] `just check` passes after lifecycle setup and no service or secret is
      required.

## Verification

```sh
bash -n .agents/setup .agents/resume
.agents/setup
.agents/setup
.agents/resume
env -i HOME="$HOME" USER="$USER" PATH=/usr/bin:/bin /bin/bash -lc \
  'cd /home/user/workspace/repo && rustc --version && cargo --version && just --version'
just check
```

## Evidence

- [Execution receipt](../../evidence/phase-0/RB-T-ORBSETUP/evidence.json)
- [Fresh setup transcript](../../evidence/phase-0/RB-T-ORBSETUP/setup-fresh.txt)
- [Warm setup transcript](../../evidence/phase-0/RB-T-ORBSETUP/setup-warm.txt)
- [Resume transcript](../../evidence/phase-0/RB-T-ORBSETUP/resume.txt)
- [Login-shell transcript](../../evidence/phase-0/RB-T-ORBSETUP/login-shell.txt)
- [Final repository checks](../../evidence/phase-0/RB-T-ORBSETUP/final-check.txt)
- [Environment and timing receipt](../../evidence/phase-0/RB-T-ORBSETUP/environment.json)

## Out of scope

Do not install future OTP, Elixir, musl, QEMU, or target build dependencies that
have not yet been selected by their owning ready tasks. Do not add services,
credentials, environment secrets, or project-setting scripts.
