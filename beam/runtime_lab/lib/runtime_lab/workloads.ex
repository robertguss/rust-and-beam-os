defmodule RuntimeLab.Workloads do
  @moduledoc "Deterministic process, timer, binary, ETS, GC, and crash workloads."

  alias RuntimeLab.{DemoState, Event, FeatureWorker}

  @type command ::
          :all
          | :binaries
          | :crash_once
          | :crash_storm
          | :ets
          | :garbage_collection
          | :process_churn
          | :timers

  @commands [
    :process_churn,
    :timers,
    :binaries,
    :ets,
    :garbage_collection,
    :crash_once,
    :crash_storm
  ]

  @spec commands() :: [command()]
  def commands, do: [:all | @commands]

  @spec run(command(), keyword()) :: map()
  def run(command, options \\ []) when command in [:all | @commands] do
    seed = bounded_option(options, :seed, RuntimeLab.default_seed(), 0, 0xFFFF_FFFF)
    Event.emit(:workload_started, command: command, seed: seed)
    result = execute(command, seed, options)

    if Process.whereis(DemoState) do
      :ok = DemoState.record_workload(command)
    end

    Event.emit(:workload_completed, command: command, result: result, seed: seed)
    result
  end

  defp execute(:all, seed, options) do
    @commands
    |> Enum.reject(&(&1 == :crash_storm))
    |> Map.new(fn command -> {command, execute(command, seed, options)} end)
    |> Map.put(:crash_storm, execute(:crash_storm, seed, options))
  end

  defp execute(:process_churn, seed, options) do
    count = bounded_option(options, :processes, 32, 1, 10_000)
    parent = self()

    monitors =
      Map.new(1..count, fn index ->
        {pid, reference} =
          spawn_monitor(fn ->
            checksum =
              Enum.reduce(1..64, seed + index, fn value, accumulator ->
                rem(accumulator * 33 + value + index, 4_294_967_291)
              end)

            send(parent, {:runtime_lab_churn, self(), index, checksum})
          end)

        {pid, reference}
      end)

    {checksums, down} = collect_churn(monitors, %{}, %{})

    %{
      checksum: checksums |> Map.values() |> Enum.sum(),
      completed: map_size(checksums),
      exited: map_size(down)
    }
  end

  defp execute(:timers, seed, options) do
    count = bounded_option(options, :timers, 16, 1, 1_000)

    for index <- 1..count do
      delay = rem(seed + index * 17, 5) + 1
      Process.send_after(self(), {:runtime_lab_timer, index}, delay)
    end

    fired = collect_timers(count, []) |> Enum.sort()
    %{fired: length(fired), first: hd(fired), last: List.last(fired)}
  end

  defp execute(:binaries, seed, options) do
    size = bounded_option(options, :binary_bytes, 65_536, 1, 8 * 1_024 * 1_024)

    pattern =
      for index <- 0..255, into: <<>> do
        <<rem(seed + index * 13, 256)>>
      end

    repeats = div(size + byte_size(pattern) - 1, byte_size(pattern))
    binary = pattern |> :binary.copy(repeats) |> binary_part(0, size)
    checksum = for(<<byte <- binary>>, reduce: 0, do: (sum -> rem(sum + byte, 4_294_967_291)))
    %{bytes: byte_size(binary), checksum: checksum}
  end

  defp execute(:ets, seed, options) do
    count = bounded_option(options, :ets_entries, 256, 1, 100_000)
    table = :ets.new(:runtime_lab_workload, [:set, :private])

    try do
      true = :ets.insert(table, for(index <- 1..count, do: {index, seed + index}))

      checksum =
        Enum.reduce(1..count, 0, fn index, total ->
          total + :ets.lookup_element(table, index, 2)
        end)

      deleted =
        Enum.count(1..count, fn index -> rem(index, 3) == 0 and :ets.delete(table, index) end)

      %{checksum: checksum, deleted: deleted, remaining: :ets.info(table, :size)}
    after
      :ets.delete(table)
    end
  end

  defp execute(:garbage_collection, seed, options) do
    count = bounded_option(options, :gc_objects, 2_048, 1, 100_000)
    parent = self()

    {pid, reference} =
      spawn_monitor(fn ->
        payload = for index <- 1..count, do: <<seed::32, index::32, 0::64>>
        gc_worker(parent, payload)
      end)

    receive do
      {:runtime_lab_gc_ready, ^pid, bytes} ->
        send(pid, :collect)

        receive do
          {:runtime_lab_gc_complete, ^pid, before, after_gc} ->
            receive do
              {:DOWN, ^reference, :process, ^pid, :normal} ->
                %{
                  bytes: bytes,
                  collection_completed: is_integer(before) and is_integer(after_gc),
                  objects: count
                }
            after
              5_000 -> raise "garbage-collection worker did not exit"
            end
        after
          5_000 -> raise "garbage-collection worker did not complete"
        end
    after
      5_000 -> raise "garbage-collection worker did not start"
    end
  end

  defp execute(:crash_once, _seed, options) do
    worker_name = Keyword.get(options, :worker_name, FeatureWorker)
    state_name = Keyword.get(options, :state_name, DemoState)
    previous = DemoState.snapshot(state_name)
    old_worker = registered!(worker_name)
    reference = Process.monitor(old_worker)
    :ok = FeatureWorker.crash(worker_name, :crash_once)

    receive do
      {:DOWN, ^reference, :process, ^old_worker, {:intentional_crash, :crash_once}} -> :ok
    after
      5_000 -> raise "feature worker did not crash"
    end

    new_worker = await_new_worker(worker_name, old_worker, 5_000)
    current = DemoState.snapshot(state_name)

    unless current.generation == previous.generation + 1 and current.counter == previous.counter do
      raise "worker restart violated generation or state-preservation invariant"
    end

    %{
      counter: current.counter,
      generation: current.generation,
      previous_generation: previous.generation,
      restarted: new_worker != old_worker,
      restart_count: current.restart_count
    }
  end

  defp execute(:crash_storm, _seed, options) do
    max_restarts = bounded_option(options, :max_restarts, 3, 1, 20)
    names = storm_names()
    ensure_names_free!(Map.values(names))

    {:ok, supervisor} =
      RuntimeLab.Supervisor.start_link(
        name: names.supervisor,
        state_name: names.state,
        worker_name: names.worker,
        metric_name: names.metric,
        metric_interval_ms: :disabled,
        max_metric_samples: 1,
        max_restarts: max_restarts
      )

    Process.unlink(supervisor)
    supervisor_reference = Process.monitor(supervisor)

    try do
      Enum.each(1..(max_restarts + 1), fn _attempt ->
        worker = await_new_worker(names.worker, nil, 5_000)
        reference = Process.monitor(worker)
        :ok = FeatureWorker.crash(names.worker, :crash_storm)

        receive do
          {:DOWN, ^reference, :process, ^worker, {:intentional_crash, :crash_storm}} -> :ok
        after
          5_000 -> raise "crash-storm worker did not terminate"
        end
      end)

      reason =
        receive do
          {:DOWN, ^supervisor_reference, :process, ^supervisor, down_reason} -> down_reason
        after
          5_000 -> raise "crash storm did not exceed supervisor intensity"
        end

      %{
        attempted_crashes: max_restarts + 1,
        max_restarts: max_restarts,
        state_survived_escalation: process_alive?(names.state),
        supervisor_reason: reason
      }
    after
      if Process.alive?(supervisor), do: Supervisor.stop(supervisor)
    end
  end

  defp collect_churn(monitors, checksums, down)
       when map_size(checksums) == map_size(monitors) and map_size(monitors) == map_size(down) do
    {checksums, down}
  end

  defp collect_churn(monitors, checksums, down) do
    receive do
      {:runtime_lab_churn, pid, index, checksum} when is_map_key(monitors, pid) ->
        collect_churn(monitors, Map.put(checksums, index, checksum), down)

      {:DOWN, reference, :process, pid, :normal} ->
        if Map.get(monitors, pid) == reference do
          collect_churn(monitors, checksums, Map.put(down, pid, true))
        else
          collect_churn(monitors, checksums, down)
        end
    after
      5_000 -> raise "process-churn workload timed out"
    end
  end

  defp collect_timers(0, fired), do: fired

  defp collect_timers(remaining, fired) do
    receive do
      {:runtime_lab_timer, index} -> collect_timers(remaining - 1, [index | fired])
    after
      5_000 -> raise "timer workload timed out"
    end
  end

  defp gc_worker(parent, payload) do
    send(parent, {:runtime_lab_gc_ready, self(), :erlang.iolist_size(payload)})

    receive do
      :collect ->
        before = process_memory()
        :erlang.garbage_collect()
        send(parent, {:runtime_lab_gc_complete, self(), before, process_memory()})
    end
  end

  defp process_memory do
    {:memory, bytes} = Process.info(self(), :memory)
    bytes
  end

  defp bounded_option(options, key, default, minimum, maximum) do
    value = Keyword.get(options, key, default)

    if is_integer(value) and value >= minimum and value <= maximum do
      value
    else
      raise ArgumentError, "#{key} must be an integer in #{minimum}..#{maximum}"
    end
  end

  defp await_new_worker(name, previous, timeout_ms) do
    deadline = System.monotonic_time(:millisecond) + timeout_ms
    do_await_new_worker(name, previous, deadline)
  end

  defp do_await_new_worker(name, previous, deadline) do
    case Process.whereis(name) do
      pid when is_pid(pid) and pid != previous ->
        pid

      _other ->
        if System.monotonic_time(:millisecond) >= deadline do
          raise "timed out waiting for #{inspect(name)}"
        end

        Process.sleep(1)
        do_await_new_worker(name, previous, deadline)
    end
  end

  defp registered!(name) do
    case Process.whereis(name) do
      pid when is_pid(pid) -> pid
      nil -> raise "#{inspect(name)} is not running"
    end
  end

  defp storm_names do
    %{
      metric: RuntimeLab.Storm.MetricSampler,
      state: RuntimeLab.Storm.DemoState,
      supervisor: RuntimeLab.Storm.Supervisor,
      worker: RuntimeLab.Storm.FeatureWorker
    }
  end

  defp ensure_names_free!(names) do
    if Enum.any?(names, &(Process.whereis(&1) != nil)) do
      raise "crash-storm supervisor is already running"
    end
  end

  defp process_alive?(name) do
    case Process.whereis(name) do
      nil -> false
      pid -> Process.alive?(pid)
    end
  end
end
