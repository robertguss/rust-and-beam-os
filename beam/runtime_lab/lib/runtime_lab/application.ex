defmodule RuntimeLab.Application do
  @moduledoc false

  use Application

  alias RuntimeLab.{Event, RuntimeIdentity}

  @impl true
  def start(_type, _arguments) do
    case RuntimeLab.Supervisor.start_link() do
      {:ok, _supervisor} = started ->
        Event.emit(:application_started, build_id: RuntimeLab.build_id())
        RuntimeIdentity.emit()
        started

      other ->
        other
    end
  end

  @impl true
  def stop(_application_state) do
    Event.emit(:application_stopped, status: :normal)
    :ok
  end
end
