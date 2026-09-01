defmodule RuntimeLab.FeatureWorker do
  @moduledoc "Intentionally crashable worker whose data is owned by DemoState."

  use GenServer

  alias RuntimeLab.DemoState

  @type server :: GenServer.server()

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(options) do
    name = Keyword.get(options, :name, __MODULE__)
    start_options = if name == nil, do: [], else: [name: name]
    GenServer.start_link(__MODULE__, options, start_options)
  end

  @spec increment(integer()) :: non_neg_integer()
  def increment(amount \\ 1), do: increment(__MODULE__, amount)

  @spec increment(server(), integer()) :: non_neg_integer()
  def increment(server, amount), do: GenServer.call(server, {:increment, amount})

  @spec crash(server(), atom()) :: :ok
  def crash(server \\ __MODULE__, category) when is_atom(category) do
    GenServer.cast(server, {:crash, category})
  end

  @impl true
  def init(options) do
    state_name = Keyword.fetch!(options, :state_name)
    generation = DemoState.worker_started(state_name, self())
    {:ok, %{generation: generation, state_name: state_name}}
  end

  @impl true
  def handle_call({:increment, amount}, _from, state) do
    {:reply, DemoState.increment(state.state_name, amount), state}
  end

  @impl true
  def handle_cast({:crash, category}, state) do
    :ok = DemoState.worker_crashing(state.state_name, state.generation, category)
    {:stop, {:intentional_crash, category}, state}
  end
end
