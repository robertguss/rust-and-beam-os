defmodule RuntimeLab.Event do
  @moduledoc "Canonical line-oriented lifecycle events for tracing."

  @schema "runtime_lab/event-v1"

  @spec emit(atom(), keyword()) :: :ok
  def emit(type, fields \\ []) when is_atom(type) and is_list(fields) do
    type
    |> format(fields)
    |> IO.puts()
  end

  @spec format(atom(), keyword()) :: String.t()
  def format(type, fields \\ []) when is_atom(type) and is_list(fields) do
    encoded_fields =
      fields
      |> Enum.sort_by(fn {key, _value} -> Atom.to_string(key) end)
      |> Enum.map_join(" ", fn {key, value} ->
        "#{key}=#{encode(value)}"
      end)

    base =
      "runtime_lab_event schema=#{encode(@schema)} type=#{encode(type)} " <>
        "workload_version=#{encode(RuntimeLab.workload_version())}"

    if encoded_fields == "", do: base, else: base <> " " <> encoded_fields
  end

  defp encode(value) when is_atom(value), do: Atom.to_string(value)
  defp encode(value) when is_binary(value), do: inspect(value)
  defp encode(value) when is_integer(value), do: Integer.to_string(value)
  defp encode(value) when is_pid(value), do: inspect(value)

  defp encode(value) when is_map(value) do
    entries =
      value
      |> Enum.sort_by(fn {key, _value} -> encode(key) end)
      |> Enum.map_join(",", fn {key, nested} -> "#{encode(key)}:#{encode(nested)}" end)

    "%{" <> entries <> "}"
  end

  defp encode(value) when is_list(value) do
    "[" <> Enum.map_join(value, ",", &encode/1) <> "]"
  end

  defp encode(value) when is_tuple(value) do
    "{" <> (value |> Tuple.to_list() |> Enum.map_join(",", &encode/1)) <> "}"
  end

  defp encode(value), do: inspect(value, limit: :infinity, printable_limit: :infinity)
end
