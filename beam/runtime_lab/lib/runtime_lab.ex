defmodule RuntimeLab do
  @moduledoc """
  Deterministic Linux reference workload for the Rust + BEAM OS POC.

  Demo state is in memory and survives only an intentional feature-worker
  restart. It resets with the application supervisor, BEAM VM, or system.
  """

  alias RuntimeLab.{DemoState, FeatureWorker, RuntimeIdentity, Workloads}

  @workload_version "1.0.0"
  @build_id "runtime_lab-0.1.0"
  @default_seed 20_260_901

  @spec workload_version() :: String.t()
  def workload_version, do: @workload_version

  @spec build_id() :: String.t()
  def build_id, do: @build_id

  @spec default_seed() :: pos_integer()
  def default_seed, do: @default_seed

  @spec identity() :: map()
  def identity, do: RuntimeIdentity.snapshot()

  @spec snapshot() :: map()
  def snapshot, do: DemoState.snapshot()

  @spec increment(integer()) :: non_neg_integer()
  def increment(amount \\ 1), do: FeatureWorker.increment(amount)

  @spec crash_once() :: map()
  def crash_once, do: Workloads.run(:crash_once)

  @spec run(Workloads.command(), keyword()) :: map()
  def run(command, options \\ []), do: Workloads.run(command, options)

  @spec state_boundaries() :: map()
  def state_boundaries do
    %{
      feature_worker_restart: :preserved,
      application_supervisor_restart: :reset,
      beam_vm_restart: :reset,
      system_reboot: :reset
    }
  end
end
