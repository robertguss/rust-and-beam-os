-module(rb_erts_workload).

-export([run/0]).

run() ->
    Profile = profile(),
    Parent = self(),
    Worker = spawn(fun() ->
        receive
            {ping, From} -> From ! {pong, self()}
        end
    end),
    Worker ! {ping, Parent},
    receive
        {pong, Worker} -> ok
    after 2000 ->
        error(message_timeout)
    end,

    _Timer = erlang:send_after(20, self(), timer_fired),
    receive
        timer_fired -> ok
    after 2000 ->
        error(timer_timeout)
    end,

    Binary = binary:copy(<<16#10, 16#20, 16#30, 16#40>>, 65536),
    262144 = byte_size(Binary),
    Table = ets:new(reference_table, [set, private]),
    true = ets:insert(Table, {payload, Binary}),
    [{payload, Binary}] = ets:lookup(Table, payload),
    true = ets:delete(Table),
    Garbage = lists:seq(1, 100000),
    100000 = length(Garbage),
    true = erlang:garbage_collect(),

    EmuFlavor = erlang:system_info(emu_flavor),
    emu = EmuFlavor,
    Schedulers = erlang:system_info(schedulers),
    SchedulersOnline = erlang:system_info(schedulers_online),
    ExpectedSchedulers = expected_schedulers(Profile),
    ExpectedSchedulers = Schedulers,
    ExpectedSchedulers = SchedulersOnline,
    DirtyCpu = erlang:system_info(dirty_cpu_schedulers),
    DirtyCpuOnline = erlang:system_info(dirty_cpu_schedulers_online),
    DirtyIo = erlang:system_info(dirty_io_schedulers),
    AsyncThreads = erlang:system_info(thread_pool_size),
    true = erlang:system_info(threads),

    Result = io_lib:format(
        "{\"schema\":\"rust-beam/erts-workload/v1\","
        "\"profile\":\"~s\",\"otp_release\":\"~s\",\"erts_version\":\"~s\","
        "\"emu_flavor\":\"~s\",\"build_type\":\"~s\","
        "\"schedulers\":~B,\"schedulers_online\":~B,"
        "\"dirty_cpu_schedulers\":~B,\"dirty_cpu_schedulers_online\":~B,"
        "\"dirty_io_schedulers\":~B,\"async_threads\":~B,"
        "\"process_message\":true,\"timer\":true,\"binary_bytes\":262144,"
        "\"ets\":true,\"forced_gc\":true}\n",
        [
            Profile,
            erlang:system_info(otp_release),
            erlang:system_info(version),
            atom_to_list(EmuFlavor),
            atom_to_list(erlang:system_info(build_type)),
            Schedulers,
            SchedulersOnline,
            DirtyCpu,
            DirtyCpuOnline,
            DirtyIo,
            AsyncThreads
        ]
    ),
    ResultPath = "/work/results/workload-" ++ Profile ++ ".json",
    ok = file:write_file(ResultPath, Result),
    io:format("RB_ERTS_RESULT profile=~s schedulers=~B dirty_cpu=~B dirty_io=~B async=~B~n", [
        Profile, Schedulers, DirtyCpu, DirtyIo, AsyncThreads
    ]),

    ReadyPath = "/work/results/ready-" ++ Profile,
    ContinuePath = "/work/results/continue-" ++ Profile,
    ok = file:write_file(ReadyPath, <<"ready\n">>),
    wait_for_continue(ContinuePath, 500),
    ok.

profile() ->
    case init:get_argument(profile) of
        {ok, [[Value]]} when Value =:= "single"; Value =:= "candidate" -> Value;
        Other -> error({invalid_profile, Other})
    end.

expected_schedulers("single") -> 1;
expected_schedulers("candidate") -> 2.

wait_for_continue(_Path, 0) ->
    error(snapshot_timeout);
wait_for_continue(Path, Remaining) ->
    case file:read_file_info(Path) of
        {ok, _} -> ok;
        {error, enoent} ->
            timer:sleep(10),
            wait_for_continue(Path, Remaining - 1);
        Error -> error({snapshot_marker, Error})
    end.
