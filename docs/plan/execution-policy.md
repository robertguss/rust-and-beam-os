# Plan execution policy

## Task selection

A task may start only when `repo_plan.py ready` returns it. The ready query
proves that:

- its type is `task` and its actor is `agent`;
- its state is `open`;
- its milestone is initially authorized or has an approved human gate decision;
- every `depends_on` record is `done`;
- its `defer_until` date has passed, when present.

An agent starting work sets `state: in_progress` and records `owner`. Ownership is
advisory across disconnected Git clones, so parallel work must still be assigned
by an orchestrator or coordinated through pushed commits.

## Status vocabulary

- `open`: eligible for readiness evaluation.
- `in_progress`: actively owned work; `owner` is required.
- `done`: acceptance criteria, verification, and durable evidence all pass.
- `cancelled`: intentionally removed from execution while retained for history.

`ready` and `blocked` are derived graph states, not stored statuses. Epics organize
children and are never returned as executable work. Represent an external
blocker as a task or gate dependency; use `defer_until` only for a time hold.

## Completing a task

1. Run every verification command named by the task or record why a command is not yet available.
2. Store durable evidence in the repository-defined evidence location once that structure exists.
3. Add repository evidence paths to the task's `evidence` list.
4. Set `state: done` only when every acceptance criterion is evidenced and every dependency remains done.
5. Store only forward `depends_on` edges; reverse `blocks` relationships are generated.
6. Run `python3 scripts/repo_plan.py build --root docs/plan`, then `python3 scripts/repo_plan.py check --root docs/plan`.
7. Commit the task, implementation, evidence, and generated views as one reviewable result.

## Human gate procedure

Only a human may pass a gate.

1. Review the gate and every required repository evidence path.
2. Generate exactly one decision record with `repo_plan.py new decision` and fill in its evidence, residual risks, approver, and authorizing commit.
3. Set the gate to `state: done` only when the decision is complete.
4. Run `build` and `check` and commit the gate, decision, and projections together.

An approved decision authorizes the milestone that names the gate. A rejected
decision completes the gate without authorizing that milestone. No agent may
infer authorization from implementation progress, passing tests, or an
available runner.
