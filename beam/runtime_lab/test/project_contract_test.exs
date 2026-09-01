defmodule RuntimeLab.ProjectContractTest do
  use ExUnit.Case, async: true

  test "has no dependency or application-owned NIF" do
    assert Mix.Project.config()[:deps] == []

    for source <- Path.wildcard("lib/**/*.{ex,exs}") do
      contents = File.read!(source)
      refute contents =~ "load_nif"
      refute contents =~ "@on_load"
    end
  end

  test "freezes release inputs without a host ERTS or runtime config write" do
    release = Mix.Project.config()[:releases][:runtime_lab]

    assert release[:include_erts] == false
    assert release[:runtime_config_path] == false
    refute File.exists?("config/runtime.exs")
  end
end
