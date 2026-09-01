defmodule RuntimeLab.SupervisionTest do
  use ExUnit.Case, async: false

  alias RuntimeLab.{DemoState, FeatureWorker, Workloads}

  test "worker crash advances generation and preserves stable demo state" do
    counter = RuntimeLab.increment(7)
    before = RuntimeLab.snapshot()
    old_worker = before.worker_pid

    result = RuntimeLab.crash_once()
    after_restart = RuntimeLab.snapshot()

    assert result.restarted
    assert after_restart.worker_pid != old_worker
    assert after_restart.counter == counter
    assert after_restart.generation == before.generation + 1
    assert after_restart.restart_count == before.restart_count + 1
    assert after_restart.last_worker_reason == :crash_once
  end

  test "crash storm crosses the declared restart intensity and tears down stable state" do
    result = Workloads.run(:crash_storm, max_restarts: 2)

    assert result.attempted_crashes == 3
    assert result.max_restarts == 2
    assert result.supervisor_reason == :shutdown
    refute result.state_survived_escalation
  end

  test "application-supervisor restart resets state while worker restart does not" do
    names = %{
      metric: RuntimeLab.Test.ResetMetricSampler,
      state: RuntimeLab.Test.ResetDemoState,
      supervisor: RuntimeLab.Test.ResetSupervisor,
      worker: RuntimeLab.Test.ResetFeatureWorker
    }

    options = [
      name: names.supervisor,
      state_name: names.state,
      worker_name: names.worker,
      metric_name: names.metric,
      metric_interval_ms: :disabled,
      max_metric_samples: 2,
      max_restarts: 3,
      max_seconds: 5
    ]

    {:ok, first_supervisor} = RuntimeLab.Supervisor.start_link(options)
    assert FeatureWorker.increment(names.worker, 9) == 9
    first_generation = DemoState.snapshot(names.state).generation
    Supervisor.stop(first_supervisor)

    {:ok, second_supervisor} = RuntimeLab.Supervisor.start_link(options)
    reset = DemoState.snapshot(names.state)

    assert reset.counter == 0
    assert reset.generation == first_generation
    assert reset.restart_count == 0
    Supervisor.stop(second_supervisor)

    assert RuntimeLab.state_boundaries() == %{
             application_supervisor_restart: :reset,
             beam_vm_restart: :reset,
             feature_worker_restart: :preserved,
             system_reboot: :reset
           }
  end
end
