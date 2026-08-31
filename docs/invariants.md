# Project invariants

These invariants apply before kernel-specific invariants are added by their
owning tasks.

## Authorization

1. Only tasks returned by `repo_plan.py ready` or an already-owned `in_progress`
   task may change implementation behavior.
2. M1–M6 implementation remains blocked until the preceding human gate has an
   approved decision record.
3. Placeholder commands fail rather than simulate an unauthorized artifact.

## Reproducibility and evidence

1. Every evidence input and artifact is repository-relative and identified by
   SHA-256.
2. Evidence records identify the full source revision, dirty state, exact
   command, target, environment tools, and terminal result.
3. A record is invalid if a referenced file is missing, escapes the repository,
   is not a regular file, or no longer matches its digest.
4. Candidate inputs are not described as frozen or sealed. A sealed source lock
   is immutable within a build and admits no undeclared network source.
5. Primary-source claims name their consumer and limitation; search snippets or
   recollection are not evidence.

## Scope

1. No Linux, Android, or other guest kernel is introduced.
2. No networking, writable persistent storage, dynamic linking, third-party NIF,
   phone hardware, or on-device mutation enters the POC.
3. Host programs and QEMU-user runs are explicitly labeled scaffolding or smoke
   evidence and cannot satisfy target acceptance.

Kernel memory, scheduling, handle, IPC, signal, cache, TLB, and device
invariants will be added only by their owning plan tasks before implementation.
