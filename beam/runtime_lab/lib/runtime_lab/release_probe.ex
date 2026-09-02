defmodule RuntimeLab.ReleaseProbe do
  @moduledoc false

  alias RuntimeLab.Event

  @artifact_build_id "otp-29.0.5-erts-17.0.5-beam-sha256-54ea7bc1953eb19908817ed243f63ddfabb7d8d9eefdb9d88f15ef4fe3577201"

  @spec run() :: :ok
  def run do
    {:ok, started_applications} = Application.ensure_all_started(:runtime_lab)
    identity = RuntimeLab.identity()
    config = Application.fetch_env!(:runtime_lab, RuntimeLab.Supervisor)
    artifact_build_id = System.fetch_env!("RB_ERTS_ARTIFACT_BUILD_ID")

    true = artifact_build_id == @artifact_build_id
    true = identity.elixir == "1.20.4"
    true = identity.otp == "29.0.5"
    true = identity.erts == "17.0.5"
    true = identity.emulator_flavor == :emu
    true = identity.schedulers == 2
    true = identity.schedulers_online == 2
    true = identity.dirty_cpu_schedulers == 1
    true = identity.dirty_cpu_schedulers_online == 1
    true = identity.dirty_io_schedulers == 1
    true = identity.thread_pool_size == 1
    true = config_loaded?(config)

    7 = RuntimeLab.increment(7)
    before = RuntimeLab.snapshot()
    crash = RuntimeLab.crash_once()
    after_restart = RuntimeLab.snapshot()
    true = crash.restarted
    true = after_restart.counter == 7
    true = after_restart.generation == before.generation + 1

    workloads = RuntimeLab.run(:all, seed: RuntimeLab.default_seed())
    true = workloads_passed?(workloads)

    release_root = :code.root_dir() |> List.to_string()
    write_result = File.write(Path.join(release_root, ".rb-write-probe"), "forbidden\n")
    {:error, :erofs} = write_result

    Event.emit(:target_release_result,
      application_ensure_all_started: true,
      artifact_build_id: artifact_build_id,
      config_loaded: true,
      elixir: identity.elixir,
      otp: identity.otp,
      read_only_error: :erofs,
      release_root: release_root,
      started_applications: started_applications,
      status: :pass,
      supervision: true,
      workloads: true
    )
  end

  defp config_loaded?(config) do
    config[:max_restarts] == 3 and
      config[:max_seconds] == 5 and
      config[:metric_interval_ms] == 1_000 and
      config[:max_metric_samples] == 32
  end

  defp workloads_passed?(workloads) do
    workloads.process_churn.completed == 32 and
      workloads.process_churn.exited == 32 and
      workloads.timers.fired == 16 and
      workloads.binaries.bytes == 65_536 and
      workloads.ets.remaining == 171 and
      workloads.garbage_collection.collection_completed and
      workloads.garbage_collection.objects == 2_048 and
      workloads.crash_once.restarted and
      workloads.crash_storm.attempted_crashes == 4 and
      workloads.crash_storm.max_restarts == 3 and
      not workloads.crash_storm.state_survived_escalation
  end
end
