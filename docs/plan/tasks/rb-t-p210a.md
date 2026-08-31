---
schema: "repo-plan/v1"
id: "RB-T-P210A"
title: "Implement bounded byte streams and descriptor lifecycle semantics"
type: "task"
state: "open"
priority: "P1"
milestone: "RB-M-M2"
parent: "RB-E-P210"
depends_on:
  - "RB-T-P205B"
  - "RB-T-P200"
  - "RB-T-P203"
related: []
actor: "agent"
owner: null
defer_until: null
evidence: []
x_legacy_id: "P2-10a"
x_linear_id: "ROB-789"
x_linear_url: "https://linear.app/robert-guss/issue/ROB-789/p2-10a-implement-bounded-byte-streams-and-descriptor-lifecycle"
x_labels:
  - "spec-complete"
  - "gate-blocked"
---
# RB-T-P210A: Implement bounded byte streams and descriptor lifecycle semantics

## Goal

Build the bounded full-duplex-capable byte-stream primitives and descriptor ownership rules needed by ERTS pipes and the later fixed-fd UI channel, without mixing in poll registration yet.

## Context

Blocked by: RB-T-P203, RB-T-P205B, RB-T-P200.

## Deliverables

* Define the native kernel stream object and the exact Linux-personality pipe/descriptor projection used by the pinned ERTS trace.
* Implement two unidirectional endpoints per pipe/stream direction with fixed bounded capacity, reader/writer reference counts, byte ordering, admitted atomic-write threshold, partial read/write, blocking/nonblocking behavior, EOF, broken-pipe result, and close/half-close semantics.
* Implement only the observed descriptor operations and flags: creation, duplicate/inherit behavior if required, `F_GETFL`/`F_SETFL` subset, `O_NONBLOCK`, vector I/O subset, close-on-exec rejection/handling appropriate to the no-exec POC, and fixed descriptor installation for later boot manifests.
* Define descriptor-table/object generation numbers so close/reuse cannot make a stale blocked operation act on a new endpoint.
* Use RB-T-P200 synchronization and RB-T-P205B blocking/wakeup primitives. Specify object, endpoint, descriptor, buffer, blocked-reader, and blocked-writer lifetimes separately.
* Account and cap buffers, waiters, descriptors, blocked operations, copied bytes, wakeups, closures, and error paths.
* Expose readiness-state query and change-notification hooks for RB-T-P210B, but do not implement poll registrations in this issue.

## Acceptance criteria

- [ ] Blocking and nonblocking reads/writes match the admitted Linux/musl contract for empty, partial, full, EOF, and no-reader states.
- [ ] Writes at or below the admitted atomic threshold are not interleaved; larger writes follow the documented partial/interleaving rules.
- [ ] Closing the last writer makes buffered bytes readable before EOF; closing the last reader wakes/fails writers with the documented result and signal hook.
- [ ] Descriptor close/reuse, process/thread exit, duplicate references, and blocked I/O cannot leak, double-close, or operate on a new generation.
- [ ] Invalid buffers, `iov` arrays, lengths, flags, descriptors, and resource exhaustion return the exact error without partial hidden mutation.
- [ ] Every buffer, descriptor, waiter, and object count remains within a declared bound and returns to baseline after churn.

## Verification

* `just test-byte-streams`
* `just test-descriptor-lifecycle`
* `just stress-stream-io`
* `just audit-stream-accounting`

## Evidence

* Differential C probes for capacity, atomic writes, partial I/O, vector I/O, nonblocking mode, EOF, broken pipe, half-close, duplicate references if admitted, bad pointers/flags, close/reuse, and exit cleanup.
* Model-based stream/reference-count lifecycle tests and four-vCPU producer/consumer/closure stress with forced boundary preemption.
* Generation-reuse negative canary and exact object/byte conservation report.

## Out of scope

* `poll`/`ppoll` waiter registration and timeout engine, sockets, terminals, arbitrary files, process spawning, dynamic descriptor classes, or networking.

## Additional context
### Completion rule

Done means the stream and descriptor lifecycle is independently correct, bounded, generation-safe, and exposes a stable readiness hook for RB-T-P210B.
### Learning checkpoint

Explain the distinction among descriptor, endpoint, and stream-object lifetimes; the atomic-write rule; and the exact last-reader/last-writer transitions.
### Implementation-readiness disposition — 2026-08-30

**Action:** KEEP

Strong child. Confirm exact open-file-description/dup sharing whenever admitted; preserve generation-safe close/reuse and bounded byte/object accounting.
### Normative readiness correction — 2026-08-30

Whenever admitted, define Linux open-file-description sharing explicitly: `dup` aliases share offsets and status flags while descriptor-local flags and generation-safe close/reuse remain distinct. Preserve bounded byte/object accounting and exact lifecycle cleanup.
