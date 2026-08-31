# RB-T-P017 evidence

The source audit pins Tyn commit `105c4946c756a6f3d23d1c41b9e8139352ddc115` and
the corresponding GitHub archive SHA-256 in `docs/prior-art/tyn.lock.json`. The
audit report separates facts inspected in that source and its committed ERTS ELF
from Tyn-author reports and this project's observations. `tyn-reproduction.json`
records the fresh archive verification, 17 source-file checks, committed ERTS
artifact inspection, and successful kernel rebuild. The orb had neither
`/dev/kvm` nor `qemu-system-x86_64`, so the required x86_64/KVM boot was
explicitly blocked; TCG was not substituted, and no boot or reliability rate is
claimed.

`thread-progress.txt` records one healthy Linux run and five deliberate fault
injections. The probe exercises compare-before-block, futex wait/wake, signal
interruption with `EINTR`, explicit clone parent/child TID publication,
`CLONE_CHILD_CLEARTID` plus futex join, four ERTS-like scheduler workers, and
800 progress handoffs. Its negative oracles detect a skipped wake, missing
startup registration, premature blocking, scheduler progress loss, and a thread
that does not reach exit/join.

The governing invariant is that a waiter only sleeps after an atomic value
check, every required transition has a wake/progress path, and thread exit
clears and wakes its join word before reclamation. A spin/yield valve or boot
marker can make a runtime appear live while violating that invariant. The
injected-fault results distinguish a working oracle from a happy-path demo,
while the explicit KVM prerequisite result prevents source inspection or a
successful build from being mislabeled as a reproduced Tyn boot.
