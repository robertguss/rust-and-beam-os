# RB-T-P002 evidence

This is **host** evidence for the dependency-free `runtime_lab` reference
application on the pinned x86_64 Linux OTP 29.0.5 / ERTS 17.0.5 / Elixir 1.20.4
pair. It does not prove the later AArch64 target ERTS or custom-kernel path.

`test-runs.txt` records two complete 10-test passes with different ExUnit seeds.
Both ran from an isolated Mix/Hex home with `HEX_OFFLINE=1` inside a fresh Linux
network namespace created by `unshare --user --map-root-user --net`. The suite
tests exact runtime identity, normal bounded workloads, worker restart and state
preservation, restart-intensity escalation, supervisor reset, metric retention,
release options, and absence of dependency/NIF loading declarations.

`reference-boot.txt` is the required `mix run --no-halt` boot. The harness sent
SIGTERM after three seconds, after observing exact identity and initial worker
events; `application_stopped status=normal` proves the application handled the
controlled shutdown. The harness's expected timeout status is not presented as
an application failure.

`workload.txt` retains the canonical structured events for the complete seed
`20260901` workload. It includes process churn, timers, binaries, ETS, garbage
collection, one primary-worker crash/restart, and a four-crash isolated storm
that exceeds the configured three-restart limit. `workload-comparison.json`
records that a second invocation produced the exact same canonical
`command_result` bytes. PIDs and Logger timestamps are diagnostic only and are
not part of that deterministic comparison.

`release-inputs.json` hashes every production Mix input and records the observed
release closure. The Phase 0 payload contains no embedded ERTS directory and no
native library; RB-T-P007 must pair it with the exact target runtime. Its
release contract also disables the writable runtime-config path.

The governing invariant is that `RuntimeLab.DemoState` precedes the intentional
worker under `rest_for_one`: a worker failure increments generation and restart
count without replacing the state owner, while supervisor/application, BEAM, and
image restarts reset all in-memory state. A one-for-all tree, worker-owned
counter, accidental persistent process, or too-high restart intensity could make
a demo appear recovered while violating that boundary. The saved
generation/counter events, isolated escalation, reset test, two seeds, repeated
canonical result, and controlled shutdown distinguish the intended mechanism
from a single accidental boot.
