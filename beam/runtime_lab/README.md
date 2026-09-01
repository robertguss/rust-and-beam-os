# runtime_lab

`runtime_lab` is the dependency-free Linux reference application for the Rust +
BEAM OS POC. It runs only against the pinned OTP 29.0.5 / Elixir 1.20.4 pair and
does not contain an application NIF or Hex dependency.

## State ownership

“Durable” here means restart-persistent in-memory state across the intentionally
crashing feature worker only. There is no writable persistence.

| Boundary                       | Counter and demo state | Worker generation |
| ------------------------------ | ---------------------- | ----------------- |
| Feature-worker restart         | Preserved              | Incremented       |
| Application-supervisor restart | Reset                  | Reset to 1        |
| BEAM VM restart                | Reset                  | Reset to 1        |
| Complete image/system reboot   | Reset                  | Reset to 1        |

`RuntimeLab.DemoState` starts before `RuntimeLab.FeatureWorker` under a
`rest_for_one` supervisor. A worker crash therefore leaves the state owner
alive. Exceeding three restarts in five seconds terminates that supervisor and
its state, making escalation observably different from worker recovery.

## Commands

Every workload has a fixed default seed (`20260901`) and bounded inputs. Run a
finite workload with:

```sh
mix run -e 'RuntimeLab.Command.main(System.argv())' -- process-churn --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- timers --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- binaries --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- ets --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- gc --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- crash-once --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- crash-storm --seed 20260901
mix run -e 'RuntimeLab.Command.main(System.argv())' -- all --seed 20260901
```

Run the long-lived reference application with `mix run --no-halt`. Boot,
identity, worker lifecycle, state changes, workloads, and shutdown use canonical
`runtime_lab_event` lines rather than depending on Logger report prose.

## Release inputs

`mix.exs`, `config/config.exs`, and the source tree are the complete Mix release
inputs. The `runtime_lab` release sets `include_erts: false` and
`runtime_config_path: false`: RB-T-P007 will pair this payload with the target
ERTS and must not introduce a host runtime or writable runtime-config path.
