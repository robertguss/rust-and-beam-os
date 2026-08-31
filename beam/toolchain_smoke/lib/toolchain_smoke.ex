defmodule ToolchainSmoke do
  @moduledoc "Dependency-free compatibility probe for the P003 runtime pair."

  @spec identity() :: %{elixir: String.t(), otp: String.t()}
  def identity do
    otp_version =
      :code.root_dir()
      |> List.to_string()
      |> Path.join("releases/#{:erlang.system_info(:otp_release)}/OTP_VERSION")
      |> File.read!()
      |> String.trim()

    %{elixir: System.version(), otp: otp_version}
  end

  @spec identity_line() :: String.t()
  def identity_line do
    identity = identity()
    "otp=#{identity.otp} elixir=#{identity.elixir}"
  end
end
