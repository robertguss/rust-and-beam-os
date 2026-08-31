defmodule ToolchainSmokeTest do
  use ExUnit.Case, async: true

  test "runs the exact frozen candidate pair" do
    assert ToolchainSmoke.identity() == %{otp: "29.0.5", elixir: "1.20.4"}
    assert ToolchainSmoke.identity_line() == "otp=29.0.5 elixir=1.20.4"
  end
end
