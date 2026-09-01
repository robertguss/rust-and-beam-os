defmodule RuntimeLab.RuntimeIdentity do
  @moduledoc "Exact runtime, scheduler, and workload identity."

  alias RuntimeLab.Event

  @spec snapshot() :: map()
  def snapshot do
    %{
      application: "runtime_lab",
      build_id: RuntimeLab.build_id(),
      dirty_cpu_schedulers: :erlang.system_info(:dirty_cpu_schedulers),
      dirty_cpu_schedulers_online: :erlang.system_info(:dirty_cpu_schedulers_online),
      dirty_io_schedulers: :erlang.system_info(:dirty_io_schedulers),
      elixir: System.version(),
      emulator_flavor: :erlang.system_info(:emu_flavor),
      erts: :erlang.system_info(:version) |> List.to_string(),
      otp: otp_version(),
      schedulers: :erlang.system_info(:schedulers),
      schedulers_online: :erlang.system_info(:schedulers_online),
      thread_pool_size: :erlang.system_info(:thread_pool_size),
      workload_version: RuntimeLab.workload_version()
    }
  end

  @spec emit() :: :ok
  def emit do
    identity = snapshot()

    Event.emit(:runtime_identity,
      application: identity.application,
      build_id: identity.build_id,
      dirty_cpu_schedulers: identity.dirty_cpu_schedulers,
      dirty_cpu_schedulers_online: identity.dirty_cpu_schedulers_online,
      dirty_io_schedulers: identity.dirty_io_schedulers,
      elixir: identity.elixir,
      emulator_flavor: identity.emulator_flavor,
      erts: identity.erts,
      otp: identity.otp,
      schedulers: identity.schedulers,
      schedulers_online: identity.schedulers_online,
      thread_pool_size: identity.thread_pool_size
    )
  end

  defp otp_version do
    path =
      :code.root_dir()
      |> List.to_string()
      |> Path.join("releases/#{:erlang.system_info(:otp_release)}/OTP_VERSION")

    path
    |> File.read!()
    |> String.trim()
  end
end
