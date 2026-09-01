defmodule RuntimeLab.MetricSampler do
  @moduledoc "Bounded periodic runtime metric sampler."

  use GenServer

  alias RuntimeLab.{DemoState, Event}

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(options) do
    name = Keyword.get(options, :name, __MODULE__)
    start_options = if name == nil, do: [], else: [name: name]
    GenServer.start_link(__MODULE__, options, start_options)
  end

  @impl true
  def init(options) do
    interval_ms = Keyword.fetch!(options, :interval_ms)

    state = %{
      interval_ms: interval_ms,
      sample_number: 0,
      state_name: Keyword.fetch!(options, :state_name)
    }

    Event.emit(:metric_sampler_started, interval_ms: interval_ms)
    {:ok, schedule(state)}
  end

  @impl true
  def handle_info(:sample, state) do
    sample_number = state.sample_number + 1

    sample = %{
      memory_bytes: :erlang.memory(:total),
      process_count: :erlang.system_info(:process_count),
      run_queue: :erlang.statistics(:run_queue),
      sample: sample_number
    }

    :ok = DemoState.record_metric(state.state_name, sample)
    {:noreply, schedule(%{state | sample_number: sample_number})}
  end

  defp schedule(state) do
    Process.send_after(self(), :sample, state.interval_ms)
    state
  end
end
