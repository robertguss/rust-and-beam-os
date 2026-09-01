#!/bin/busybox sh
set -u

/bin/busybox --install -s /bin
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
export HOME=/tmp/home
export TMPDIR=/tmp
export LC_ALL=C
export TZ=UTC
export ERL_CRASH_DUMP=/dev/null
export ERL_CRASH_DUMP_SECONDS=0
export ROOTDIR=/otp
export BINDIR=/otp/erts-17.0.5/bin
export PROGNAME=erl
export EMU=beam

fail() {
    code="$1"
    stage="$2"
    printf 'RB_GUEST event=fail stage=%s status=%s\n' "$stage" "$code"
    if mountpoint -q /work; then
        mkdir -p /work/results
        printf 'status=fail\nstage=%s\nexit_code=%s\n' "$stage" "$code" > /work/results/guest-status.txt
        sync
        umount /work || true
    fi
    poweroff -f
    while :; do sleep 1; done
}

must() {
    stage="$1"
    shift
    "$@" || fail "$?" "$stage"
}

mkdir -p /dev /proc /sys /tmp/home /tmp/traces /work
mount -t devtmpfs devtmpfs /dev || true
stty -F /dev/console -onlcr || true
must mount-proc mount -t proc proc /proc
must mount-sysfs mount -t sysfs sysfs /sys
must hostname hostname rb-erts-reference
must module-virtio-mmio modprobe virtio_mmio
must module-virtio-blk modprobe virtio_blk
must module-ext4 modprobe ext4
for _attempt in $(seq 1 200); do
    [ -b /dev/vda ] && break
    sleep 0.05
done
[ -b /dev/vda ] || fail 1 block-device
must mount-results mount -t ext4 -o rw,noatime /dev/vda /work
mkdir -p /work/results/profiles /work/results/traces

printf 'RB_GUEST event=boot kernel=%s machine=aarch64 vcpus=%s\n' \
    "$(uname -r)" "$(find /sys/devices/system/cpu -maxdepth 1 -type d -name 'cpu[0-9]*' | wc -l)"
must platform-probe /probe/platform_probe /work/results/platform.json
cp /proc/cpuinfo /work/results/cpuinfo.txt
cp /proc/meminfo /work/results/meminfo.txt
cp /proc/cmdline /work/results/kernel-cmdline.txt
find /sys/devices/system/cpu -maxdepth 4 -type f \( -name 'coherency_line_size' -o -name 'size' -o -name 'type' \) \
    -print -exec cat {} \; > /work/results/cache-topology.txt 2>/dev/null || true

strace -ff -qq -ttt -T -yy -s 256 -o /tmp/traces/minimal \
    "$BINDIR/beam.smp" -S 1:1 -SDcpu 1:1 -SDio 1 -A 1 -- \
    -root /otp -bindir "$BINDIR" -progname erl -- \
    -home /tmp/home -boot /otp/releases/29/start -boot_var ERTS_LIB_DIR /otp/lib \
    -config /otp/releases/29/sys -noshell -noinput \
    -eval 'erlang:display(ok), halt().' </dev/null
minimal_status=$?
printf 'RB_GUEST event=minimal status=%s\n' "$minimal_status"
[ "$minimal_status" -eq 0 ] || fail "$minimal_status" minimal-eval

find_beam_pid() {
    for process in /proc/[0-9]*; do
        [ -r "$process/comm" ] || continue
        [ "$(cat "$process/comm")" = "beam.smp" ] || continue
        basename "$process"
        return 0
    done
    return 1
}

snapshot_process() {
    profile="$1"
    pid="$2"
    destination="/work/results/profiles/$profile"
    mkdir -p "$destination/tasks"
    for name in maps smaps_rollup status limits mountinfo auxv cmdline environ; do
        [ -r "/proc/$pid/$name" ] && cp "/proc/$pid/$name" "$destination/$name"
    done
    ls -la "/proc/$pid/fd" > "$destination/fds.txt"
    for task in "/proc/$pid/task/"*; do
        tid="$(basename "$task")"
        mkdir -p "$destination/tasks/$tid"
        for name in comm stat status syscall; do
            [ -r "$task/$name" ] && cp "$task/$name" "$destination/tasks/$tid/$name"
        done
    done
}

run_profile() {
    profile="$1"
    shift
    rm -f "/work/results/ready-$profile" "/work/results/continue-$profile"
    strace -ff -qq -ttt -T -yy -s 256 -o "/tmp/traces/$profile" \
        "$BINDIR/beam.smp" "$@" -- \
        -root /otp -bindir "$BINDIR" -progname erl -- \
        -home /tmp/home -boot /otp/releases/29/start -boot_var ERTS_LIB_DIR /otp/lib \
        -config /otp/releases/29/sys -pa /probe -noshell -noinput \
        -profile "$profile" -s rb_erts_workload run -s init stop </dev/null &
    tracer_pid=$!
    for _attempt in $(seq 1 500); do
        [ -f "/work/results/ready-$profile" ] && break
        kill -0 "$tracer_pid" 2>/dev/null || break
        sleep 0.02
    done
    [ -f "/work/results/ready-$profile" ] || fail 1 "$profile-ready"
    beam_pid="$(find_beam_pid)" || fail 1 "$profile-pid"
    snapshot_process "$profile" "$beam_pid"
    printf 'continue\n' > "/work/results/continue-$profile"
    wait "$tracer_pid"
    profile_status=$?
    printf 'RB_GUEST event=workload profile=%s status=%s pid=%s\n' "$profile" "$profile_status" "$beam_pid"
    [ "$profile_status" -eq 0 ] || fail "$profile_status" "$profile-workload"
}

run_profile single -S 1:1 -SDcpu 1:1 -SDio 1 -A 1
run_profile candidate -S 2:2 -SDcpu 1:1 -SDio 1 -A 1
cp /tmp/traces/* /work/results/traces/
printf 'status=pass\nminimal=0\nsingle=0\ncandidate=0\n' > /work/results/guest-status.txt
sync
must unmount-results umount /work
printf 'RB_GUEST event=complete status=pass\n'
poweroff -f
while :; do sleep 1; done
