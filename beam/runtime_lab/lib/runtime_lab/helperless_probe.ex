defmodule RuntimeLab.HelperlessProbe do
  @moduledoc false

  alias RuntimeLab.Event

  @artifact_build_id "otp-29.0.5-erts-17.0.5-helperless-beam-sha256-2236a94efdea84687c7139f4fa021c4381aa5d00969976bfc330049554711c22"
  @timeout_ms 1_000

  @spec run() :: :ok
  def run do
    :ok = RuntimeLab.ReleaseProbe.run_for(@artifact_build_id)
    {:ok, {127, 0, 0, 1}} = :inet.getaddr(~c"localhost", :inet)

    missing_host =
      negative(:public_missing_host, fn ->
        :inet.getaddr(~c"rb-helperless-missing.invalid", :inet)
      end)

    true = missing_host.outcome == inspect({:return, {:error, :nxdomain}})

    operations = [
      negative(:os_cmd, fn -> :os.cmd(~c"printf forbidden") end),
      negative(:system_cmd, fn -> System.cmd("/bin/true", []) end),
      negative(:port_spawn, fn -> Port.open({:spawn, "true"}, []) end),
      negative(:port_spawn_executable, fn -> Port.open({:spawn_executable, ~c"/bin/true"}, []) end),
      negative(:heart, fn -> :heart.start() end),
      missing_host
    ]

    true = Enum.all?(operations, &(&1.bounded and &1.rejected))

    Event.emit(:helperless_result,
      file_lookup: true,
      liveness_after_rejections: true,
      operations: inspect(operations, limit: :infinity, printable_limit: :infinity),
      status: :pass
    )
  end

  defp negative(name, operation) do
    token = make_ref()
    parent = self()
    started = System.monotonic_time(:millisecond)

    {pid, monitor} =
      spawn_monitor(fn ->
        send(parent, {token, capture(operation)})
      end)

    receive do
      {^token, outcome} ->
        Process.demonitor(monitor, [:flush])
        %{name: name, bounded: true, rejected: rejected?(outcome), outcome: inspect(outcome)}

      {:DOWN, ^monitor, :process, ^pid, reason} ->
        %{name: name, bounded: true, rejected: true, outcome: inspect({:exit, reason})}
    after
      @timeout_ms ->
        Process.exit(pid, :kill)
        receive do
          {:DOWN, ^monitor, :process, ^pid, _reason} -> :ok
        end

        %{
          name: name,
          bounded: false,
          rejected: false,
          outcome: "timeout after #{System.monotonic_time(:millisecond) - started}ms"
        }
    end
  end

  defp capture(operation) do
    {:return, operation.()}
  rescue
    error -> {:raise, error.__struct__, Exception.message(error)}
  catch
    kind, reason -> {kind, reason}
  end

  defp rejected?({:return, value}) when is_port(value) do
    Port.close(value)
    false
  end

  defp rejected?({:return, {:ok, _value}}), do: false
  defp rejected?({:return, value}) when is_list(value) or is_binary(value), do: false
  defp rejected?({:return, :ok}), do: false
  defp rejected?(_outcome), do: true
end
