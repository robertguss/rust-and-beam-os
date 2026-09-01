import Config

config :runtime_lab, RuntimeLab.Supervisor,
  max_restarts: 3,
  max_seconds: 5,
  metric_interval_ms: 1_000,
  max_metric_samples: 32

config :logger, :default_handler,
  formatter: Logger.Formatter.new(format: "$time $metadata[$level] $message\n")
