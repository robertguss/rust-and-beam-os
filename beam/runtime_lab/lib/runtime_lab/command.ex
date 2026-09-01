defmodule RuntimeLab.Command do
  @moduledoc "Command-line entry point for repeatable reference workloads."

  alias RuntimeLab.Event

  @commands %{
    "all" => :all,
    "binaries" => :binaries,
    "crash-once" => :crash_once,
    "crash-storm" => :crash_storm,
    "ets" => :ets,
    "gc" => :garbage_collection,
    "process-churn" => :process_churn,
    "timers" => :timers
  }

  @spec main([String.t()]) :: :ok
  def main(arguments) do
    {command, seed} = parse(arguments)
    result = RuntimeLab.run(command, seed: seed)
    Event.emit(:command_result, command: command, result: result, seed: seed)
  end

  defp parse([command]), do: {fetch_command!(command), RuntimeLab.default_seed()}

  defp parse([command, "--seed", seed]) do
    {fetch_command!(command), String.to_integer(seed)}
  end

  defp parse(_arguments) do
    raise ArgumentError,
          "expected COMMAND [--seed INTEGER]; commands: #{Enum.join(Map.keys(@commands), ", ")}"
  end

  defp fetch_command!(command) do
    Map.fetch!(@commands, command)
  end
end
