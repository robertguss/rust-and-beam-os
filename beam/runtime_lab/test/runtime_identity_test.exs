defmodule RuntimeLab.RuntimeIdentityTest do
  use ExUnit.Case, async: true

  test "reports the exact frozen runtime and workload identity" do
    identity = RuntimeLab.identity()

    assert identity.application == "runtime_lab"
    assert identity.build_id == "runtime_lab-0.1.0"
    assert identity.elixir == "1.20.4"
    assert identity.otp == "29.0.5"
    assert identity.erts == "17.0.5"
    assert identity.emulator_flavor in [:jit, :emulator]
    assert identity.schedulers >= identity.schedulers_online
    assert identity.schedulers_online > 0
    assert identity.workload_version == "1.0.0"
  end

  test "emits a canonical structured identity event" do
    line = RuntimeLab.Event.format(:runtime_identity, otp: "29.0.5", seed: 20_260_901)

    assert line ==
             ~s(runtime_lab_event schema="runtime_lab/event-v1" type=runtime_identity workload_version="1.0.0" otp="29.0.5" seed=20260901)
  end
end
