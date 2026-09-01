defmodule RuntimeLab.MixProject do
  use Mix.Project

  def project do
    [
      app: :runtime_lab,
      version: "0.1.0",
      elixir: "== 1.20.4",
      elixirc_options: [warnings_as_errors: true],
      start_permanent: Mix.env() == :prod,
      deps: [],
      releases: [
        runtime_lab: [
          include_erts: false,
          runtime_config_path: false
        ]
      ]
    ]
  end

  def application do
    [
      extra_applications: [:logger],
      mod: {RuntimeLab.Application, []}
    ]
  end
end
