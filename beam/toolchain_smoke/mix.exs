defmodule ToolchainSmoke.MixProject do
  use Mix.Project

  def project do
    [
      app: :toolchain_smoke,
      version: "0.1.0",
      elixir: "== 1.20.4",
      start_permanent: false,
      deps: []
    ]
  end

  def application do
    [extra_applications: [:logger]]
  end
end
