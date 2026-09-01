defmodule RuntimeLab.DemoState do
  @moduledoc """
  In-memory state that survives only an intentional feature-worker restart.

  The process is supervised before the worker, so the `rest_for_one` strategy
  leaves it alive for a worker crash. No file, external store, or process outside
  the application owns this state.
  """

  use GenServer

  alias RuntimeLab.Event

  @type server :: GenServer.server()

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(options) do
    name = Keyword.get(options, :name, __MODULE__)
    start_options = if name == nil, do: [], else: [name: name]
    GenServer.start_link(__MODULE__, options, start_options)
  end

  @spec snapshot(server()) :: map()
  def snapshot(server \\ __MODULE__), do: GenServer.call(server, :snapshot)

  @spec increment(server(), integer()) :: non_neg_integer()
  def increment(server \\ __MODULE__, amount)
      when is_integer(amount) and amount > 0 do
    GenServer.call(server, {:increment, amount})
  end

  @spec worker_started(server(), pid()) :: pos_integer()
  def worker_started(server, worker), do: GenServer.call(server, {:worker_started, worker})

  @spec worker_crashing(server(), pos_integer(), atom()) :: :ok | :stale
  def worker_crashing(server, generation, category) do
    GenServer.call(server, {:worker_crashing, generation, category})
  end

  @spec record_metric(server(), map()) :: :ok
  def record_metric(server, sample), do: GenServer.call(server, {:record_metric, sample})

  @spec record_workload(server(), atom()) :: :ok
  def record_workload(server \\ __MODULE__, workload) do
    GenServer.call(server, {:record_workload, workload})
  end

  @impl true
  def init(options) do
    {:ok,
     %{
       counter: 0,
       generation: 0,
       last_worker_reason: :initial,
       max_metric_samples: Keyword.fetch!(options, :max_metric_samples),
       metric_samples: [],
       pending_worker_reason: :initial,
       restart_count: 0,
       revision: 0,
       worker_pid: nil,
       workloads: %{}
     }}
  end

  @impl true
  def handle_call(:snapshot, _from, state) do
    snapshot = state |> Map.delete(:pending_worker_reason) |> Map.delete(:max_metric_samples)
    {:reply, %{snapshot | metric_samples: Enum.reverse(snapshot.metric_samples)}, state}
  end

  def handle_call({:increment, amount}, _from, state) do
    counter = state.counter + amount
    revision = state.revision + 1
    next = %{state | counter: counter, revision: revision}
    Event.emit(:demo_state_changed, counter: counter, revision: revision)
    {:reply, counter, next}
  end

  def handle_call({:worker_started, worker}, _from, state) do
    generation = state.generation + 1
    restarted = state.generation > 0
    restart_count = state.restart_count + if(restarted, do: 1, else: 0)
    revision = state.revision + 1

    next = %{
      state
      | generation: generation,
        last_worker_reason: state.pending_worker_reason,
        pending_worker_reason: :running,
        restart_count: restart_count,
        revision: revision,
        worker_pid: worker
    }

    Event.emit(:feature_worker_started,
      generation: generation,
      reason: next.last_worker_reason,
      restart_count: restart_count,
      revision: revision,
      worker: worker
    )

    {:reply, generation, next}
  end

  def handle_call({:worker_crashing, generation, category}, _from, state) do
    if generation == state.generation do
      revision = state.revision + 1
      next = %{state | pending_worker_reason: category, revision: revision}

      Event.emit(:feature_worker_crashing,
        generation: generation,
        reason: category,
        revision: revision
      )

      {:reply, :ok, next}
    else
      {:reply, :stale, state}
    end
  end

  def handle_call({:record_metric, sample}, _from, state) do
    samples = [sample | state.metric_samples] |> Enum.take(state.max_metric_samples)
    {:reply, :ok, %{state | metric_samples: samples}}
  end

  def handle_call({:record_workload, workload}, _from, state) do
    workloads = Map.update(state.workloads, workload, 1, &(&1 + 1))
    {:reply, :ok, %{state | workloads: workloads}}
  end
end
