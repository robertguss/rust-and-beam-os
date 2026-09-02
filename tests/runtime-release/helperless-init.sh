#!/bin/busybox sh
set -u

/bin/busybox --install -s /bin
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
export HOME=/tmp/runtime-lab-home
export TMPDIR=/tmp
export LC_ALL=C.UTF-8
export TZ=UTC
export ERL_CRASH_DUMP=/dev/null
export ERL_CRASH_DUMP_SECONDS=0
export RELEASE_ROOT=/system/beam/runtime_lab
export ROOTDIR="$RELEASE_ROOT"
export BINDIR="$RELEASE_ROOT/erts-17.0.5/bin"
export PROGNAME=runtime_lab
export EMU=beam
export RELEASE_NAME=runtime_lab
export RELEASE_VSN=0.1.0
export RELEASE_MODE=embedded
export RELEASE_DISTRIBUTION=none
export RB_ERTS_ARTIFACT_BUILD_ID=otp-29.0.5-erts-17.0.5-helperless-beam-sha256-2236a94efdea84687c7139f4fa021c4381aa5d00969976bfc330049554711c22

fail() {
    code="$1"
    stage="$2"
    printf 'RB_RELEASE_GUEST event=fail stage=%s status=%s\n' "$stage" "$code"
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

mkdir -p /dev /proc /sys /tmp/runtime-lab-home /tmp/traces "$RELEASE_ROOT" /work
mount -t devtmpfs devtmpfs /dev || true
stty -F /dev/console -onlcr || true
must mount-proc mount -t proc proc /proc
must mount-sysfs mount -t sysfs sysfs /sys
must hostname hostname rb-release-helperless
must module-virtio-mmio modprobe virtio_mmio
must module-virtio-blk modprobe virtio_blk
must module-ext4 modprobe ext4
must module-squashfs modprobe squashfs
for _attempt in $(seq 1 200); do
    [ -b /dev/vda ] && [ -b /dev/vdb ] && break
    sleep 0.05
done
[ -b /dev/vda ] && [ -b /dev/vdb ] || fail 1 block-devices
release_device=
results_device=
for device in /dev/vda /dev/vdb; do
    identity="$(blkid "$device" 2>/dev/null || true)"
    case "$identity" in
        *'TYPE="squashfs"'*) release_device="$device" ;;
        *'LABEL="RBRELEASE"'*'TYPE="ext4"'*) results_device="$device" ;;
    esac
done
[ -n "$release_device" ] && [ -n "$results_device" ] || fail 1 block-identities
must mount-release mount -t squashfs -o ro "$release_device" "$RELEASE_ROOT"
must mount-results mount -t ext4 -o rw,noatime "$results_device" /work
mkdir -p /work/results /work/results/traces

grep " $RELEASE_ROOT squashfs ro," /proc/mounts > /work/results/release-mount.txt || fail 1 release-not-read-only
if printf 'forbidden\n' > "$RELEASE_ROOT/.rb-harness-write" 2>/dev/null; then
    fail 1 release-write-succeeded
fi
for helper in erl_child_setup inet_gethost; do
    [ ! -e "$BINDIR/$helper" ] || fail 1 "helper-present-$helper"
done
printf 'RB_RELEASE_GUEST event=boot kernel=%s machine=aarch64 mount=squashfs-ro profile=helperless\n' "$(uname -r)"

strace -ff -qq -ttt -T -yy -s 512 -o /tmp/traces/release \
    "$BINDIR/beam.smp" -S 2:2 -SDcpu 1:1 -SDio 1 -A 1 -- \
    -root "$RELEASE_ROOT" -bindir "$BINDIR" -progname runtime_lab -- \
    -home "$HOME" -boot "$RELEASE_ROOT/releases/0.1.0/start" \
    -boot_var ERTS_LIB_DIR "$RELEASE_ROOT/lib" \
    -boot_var RELEASE_LIB "$RELEASE_ROOT/lib" \
    -config "$RELEASE_ROOT/releases/0.1.0/sys" \
    -args_file "$RELEASE_ROOT/releases/0.1.0/vm.args" \
    -kernel inetrc "\"$RELEASE_ROOT/lib/runtime_lab-0.1.0/priv/inetrc\"" \
    -mode embedded -noshell -noinput \
    -eval "'Elixir.RuntimeLab.HelperlessProbe':run()." -s init stop </dev/null
release_status=$?
printf 'RB_RELEASE_GUEST event=beam-exit status=%s\n' "$release_status"
[ "$release_status" -eq 0 ] || fail "$release_status" target-release

"$BINDIR/beam.smp" -S 1:1 -SDcpu 1:1 -SDio 1 -A 1 -- \
    -root "$RELEASE_ROOT" -bindir "$BINDIR" -progname runtime_lab -- \
    -home "$HOME" -boot "$RELEASE_ROOT/releases/29/start_clean" \
    -boot_var ERTS_LIB_DIR "$RELEASE_ROOT/lib" \
    -kernel inetrc "\"$RELEASE_ROOT/lib/runtime_lab-0.1.0/priv/inetrc\"" \
    -noshell -noinput -eval 'io:format("RB_RELEASE_GUEST event=sigterm-ready~n"), timer:sleep(infinity).' \
    </dev/null &
signal_pid=$!
sleep 1
beam_pid=
for process in /proc/[0-9]*; do
    [ -r "$process/comm" ] || continue
    [ "$(cat "$process/comm")" = "beam.smp" ] || continue
    beam_pid="$(basename "$process")"
done
[ -n "$beam_pid" ] || fail 1 sigterm-pid
printf 'RB_RELEASE_GUEST event=sigterm-target launcher_pid=%s beam_pid=%s\n' "$signal_pid" "$beam_pid"
kill -TERM "$beam_pid" || fail $? sigterm-send
for _attempt in $(seq 1 500); do
    kill -0 "$beam_pid" 2>/dev/null || break
    sleep 0.02
done
if kill -0 "$beam_pid" 2>/dev/null; then
    kill -KILL "$beam_pid" || true
    wait "$signal_pid" || true
    fail 1 sigterm-timeout
fi
wait "$signal_pid"
signal_status=$?
printf 'RB_RELEASE_GUEST event=sigterm-exit status=%s\n' "$signal_status"
[ "$signal_status" -eq 0 ] || fail "$signal_status" sigterm-exit

cp /tmp/traces/* /work/results/traces/
cp /proc/mounts /work/results/mounts.txt
printf 'status=pass\nrelease=0\nmount=squashfs-ro\n' > /work/results/guest-status.txt
sync
must unmount-release umount "$RELEASE_ROOT"
must unmount-results umount /work
printf 'RB_RELEASE_GUEST event=complete status=pass\n'
poweroff -f
while :; do sleep 1; done
