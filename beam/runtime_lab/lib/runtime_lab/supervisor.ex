defmodule RuntimeLab.Supervisor do
  @moduledoc "Supervision boundary that preserves demo state across worker restarts."

  use Supervisor

  alias RuntimeLab.{DemoState, FeatureWorker, MetricSampler}

  @spec start_link(keyword()) :: Supervisor.on_start()
  def start_link(options \\ []) do
    name = Keyword.get(options, :name, __MODULE__)
    start_options = if name == nil, do: [], else: [name: name]
    Supervisor.start_link(__MODULE__, options, start_options)
  end

  @impl true
  def init(options) do
    defaults = Application.get_env(:runtime_lab, __MODULE__, [])
    settings = Keyword.merge(defaults, options)
    state_name = Keyword.get(settings, :state_name, DemoState)
    worker_name = Keyword.get(settings, :worker_name, FeatureWorker)
    metric_name = Keyword.get(settings, :metric_name, MetricSampler)

    children = [
      {DemoState,
       name: state_name, max_metric_samples: Keyword.fetch!(settings, :max_metric_samples)},
      {FeatureWorker, name: worker_name, state_name: state_name}
    ]

    children =
      case Keyword.fetch!(settings, :metric_interval_ms) do
        :disabled ->
          children

        interval_ms ->
          children ++
            [
              {MetricSampler, name: metric_name, state_name: state_name, interval_ms: interval_ms}
            ]
      end

    Supervisor.init(children,
      strategy: :rest_for_one,
      max_restarts: Keyword.fetch!(settings, :max_restarts),
      max_seconds: Keyword.fetch!(settings, :max_seconds)
    )
  end
end
