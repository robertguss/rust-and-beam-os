# Plan execution policy

## Task selection

An implementation task may start only when:

- its milestone appears in `state.json` under `authorized_milestones`;
- its status is `ready-for-agent` or `in-progress`;
- every `blocked_by` task is complete;
- it is not a `tracking` parent or a human `gate`;
- its required runner, artifact, and evidence inputs are available.

If any condition fails, record the missing evidence or dependency; do not silently expand the task.

## Status vocabulary

- `gate-blocked`: specified but outside current authorization.
- `ready-for-agent`: authorized, dependency-ready implementation work.
- `in-progress`: actively owned implementation work.
- `blocked`: authorized work with a concrete unresolved blocker recorded in its task file.
- `done`: acceptance criteria, verification commands, and durable evidence all pass.
- `ready-for-human`: a gate or decision awaiting human review.

Tracking parents remain `gate-blocked` until authorized and close only after every required child is `done`; agents implement their children, not the parent.

## Completing a task

1. Run every verification command named by the task or record why a command is not yet available.
2. Store durable evidence in the repository-defined evidence location once that structure exists.
3. Add evidence paths and any accepted exception to the task file.
4. Set status to `done` only when every acceptance criterion is evidenced.
5. Update both ends of every dependency change: `blocked_by` and `blocks` must remain symmetric.
6. Rebuild `index.json`, run the plan validator, and commit the task, evidence, and plan-state change together when they form one reviewable result.

## Human gate procedure

Only a human may pass a gate.

1. Review the gate file using repository evidence and record the decision under `decisions/`.
2. Set the gate status to `done` only when the decision and accepted residual risks are explicit.
3. Add the newly authorized milestone to `state.json` and advance `current_gate`.
4. Promote only the dependency-ready next slice from `gate-blocked` to `ready-for-agent`.
5. Validate the graph and commit the decision, authorization, promotions, and regenerated index as one atomic gate transition.

No agent may infer authorization from implementation progress, passing tests, or an available cloud runner.
