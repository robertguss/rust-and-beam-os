defmodule RuntimeLab.WorkloadsTest do
  use ExUnit.Case, async: false

  alias RuntimeLab.Workloads

  test "normal workloads are deterministic and bounded" do
    options = [
      seed: 42,
      processes: 8,
      timers: 6,
      binary_bytes: 1_024,
      ets_entries: 20,
      gc_objects: 32
    ]

    first =
      for command <- [:process_churn, :timers, :binaries, :ets, :garbage_collection], into: %{} do
        {command, Workloads.run(command, options)}
      end

    second =
      for command <- [:process_churn, :timers, :binaries, :ets, :garbage_collection], into: %{} do
        {command, Workloads.run(command, options)}
      end

    assert first.process_churn == second.process_churn
    assert first.timers == second.timers
    assert first.binaries == second.binaries
    assert first.ets == second.ets
    assert first.garbage_collection.bytes == second.garbage_collection.bytes
    assert first.garbage_collection.collection_completed
    assert first.garbage_collection.objects == second.garbage_collection.objects
    assert first.process_churn == %{checksum: 13_749_101_813, completed: 8, exited: 8}
    assert first.timers == %{fired: 6, first: 1, last: 6}
    assert first.binaries.bytes == 1_024
    assert first.ets.remaining == 14
  end

  test "metric history drops old samples at its fixed bound" do
    name = RuntimeLab.Test.BoundedMetricState
    {:ok, state} = RuntimeLab.DemoState.start_link(name: name, max_metric_samples: 3)

    for sample <- 1..5 do
      :ok = RuntimeLab.DemoState.record_metric(name, %{sample: sample})
    end

    assert RuntimeLab.DemoState.snapshot(name).metric_samples == [
             %{sample: 3},
             %{sample: 4},
             %{sample: 5}
           ]

    GenServer.stop(state)
  end

  test "invalid workload bounds fail instead of allocating without limit" do
    assert_raise ArgumentError, fn -> Workloads.run(:process_churn, processes: 10_001) end

    assert_raise ArgumentError, fn ->
      Workloads.run(:binaries, binary_bytes: 8 * 1_024 * 1_024 + 1)
    end

    assert_raise ArgumentError, fn -> Workloads.run(:timers, seed: 0x1_0000_0000) end
  end
end
