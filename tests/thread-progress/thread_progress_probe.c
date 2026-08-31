#define _GNU_SOURCE

#include <errno.h>
#include <linux/futex.h>
#include <sched.h>
#include <signal.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#include <pthread.h>

enum {
    scheduler_count = 4,
    scheduler_rounds = 200,
    clone_stack_size = 1024 * 1024,
};

enum fault {
    fault_none,
    fault_lost_wakeup,
    fault_stalled_startup,
    fault_premature_block,
    fault_scheduler_stall,
    fault_exit_join,
};

struct scheduler_group {
    atomic_int ready;
    atomic_int first_waiters;
    atomic_int start;
    atomic_int stop;
    atomic_int failed;
    atomic_int tickets[scheduler_count];
    atomic_uint_fast64_t progress[scheduler_count];
    enum fault fault;
};

struct scheduler_arg {
    struct scheduler_group *group;
    int id;
};

struct signal_waiter {
    atomic_int armed;
    atomic_int futex_word;
    atomic_int result;
    atomic_int error;
};

struct clone_lifecycle {
    atomic_int started;
    atomic_int allow_exit;
    atomic_int hold_exit;
    atomic_int child_tid;
    atomic_int observed_tid;
    enum fault fault;
};

static atomic_int signals_seen;

static void fail_errno(const char *operation)
{
    perror(operation);
    exit(2);
}

static int futex_wait(atomic_int *word, int expected, const struct timespec *timeout)
{
    return (int)syscall(SYS_futex, word, FUTEX_WAIT_PRIVATE, expected, timeout, NULL, 0);
}

static int futex_wake(atomic_int *word, int count)
{
    return (int)syscall(SYS_futex, word, FUTEX_WAKE_PRIVATE, count, NULL, NULL, 0);
}

static uint64_t monotonic_milliseconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
        fail_errno("clock_gettime");
    }
    return (uint64_t)now.tv_sec * UINT64_C(1000) + (uint64_t)now.tv_nsec / UINT64_C(1000000);
}

static void sleep_milliseconds(long milliseconds)
{
    const struct timespec duration = {
        .tv_sec = milliseconds / 1000,
        .tv_nsec = (milliseconds % 1000) * 1000000,
    };
    struct timespec remaining = duration;
    while (nanosleep(&remaining, &remaining) != 0 && errno == EINTR) {
    }
}

static bool wait_at_least(atomic_int *value, int expected, uint64_t timeout_ms)
{
    const uint64_t deadline = monotonic_milliseconds() + timeout_ms;
    while (atomic_load_explicit(value, memory_order_acquire) < expected) {
        if (monotonic_milliseconds() >= deadline) {
            return false;
        }
        sleep_milliseconds(1);
    }
    return true;
}

static bool wait_progress(
    const atomic_uint_fast64_t *value,
    uint_fast64_t expected,
    uint64_t timeout_ms
)
{
    const uint64_t deadline = monotonic_milliseconds() + timeout_ms;
    while (atomic_load_explicit(value, memory_order_acquire) < expected) {
        if (monotonic_milliseconds() >= deadline) {
            return false;
        }
        sleep_milliseconds(1);
    }
    return true;
}

static void wake_all(atomic_int *word)
{
    if (futex_wake(word, INT32_MAX) < 0) {
        fail_errno("futex wake");
    }
}

static int wait_for_value_change(atomic_int *word, int expected, long timeout_ms)
{
    const struct timespec timeout = {
        .tv_sec = timeout_ms / 1000,
        .tv_nsec = (timeout_ms % 1000) * 1000000,
    };
    return futex_wait(word, expected, &timeout);
}

static void *scheduler_worker(void *raw)
{
    struct scheduler_arg *arg = raw;
    struct scheduler_group *group = arg->group;
    const int id = arg->id;

    if (group->fault == fault_stalled_startup && id == 0) {
        return NULL;
    }

    atomic_fetch_add_explicit(&group->ready, 1, memory_order_release);
    wake_all(&group->ready);
    while (atomic_load_explicit(&group->start, memory_order_acquire) == 0
           && atomic_load_explicit(&group->stop, memory_order_acquire) == 0) {
        const int result = wait_for_value_change(&group->start, 0, 100);
        if (result < 0 && errno != EAGAIN && errno != EINTR && errno != ETIMEDOUT) {
            atomic_store_explicit(&group->failed, 1, memory_order_release);
            return NULL;
        }
    }

    atomic_fetch_add_explicit(&group->first_waiters, 1, memory_order_release);
    wake_all(&group->first_waiters);

    for (int round = 1; round <= scheduler_rounds; ++round) {
        while (atomic_load_explicit(&group->tickets[id], memory_order_acquire) < round
               && atomic_load_explicit(&group->stop, memory_order_acquire) == 0) {
            const int current = atomic_load_explicit(&group->tickets[id], memory_order_relaxed);
            const int result = wait_for_value_change(&group->tickets[id], current, 100);
            if (result < 0 && errno == ETIMEDOUT) {
                atomic_store_explicit(&group->failed, 1, memory_order_release);
                return NULL;
            }
            if (result < 0 && errno != EAGAIN && errno != EINTR) {
                atomic_store_explicit(&group->failed, 1, memory_order_release);
                return NULL;
            }
        }
        if (atomic_load_explicit(&group->stop, memory_order_acquire) != 0) {
            return NULL;
        }
        if (group->fault == fault_scheduler_stall && id == 0 && round == 2) {
            while (atomic_load_explicit(&group->stop, memory_order_acquire) == 0) {
                (void)wait_for_value_change(&group->stop, 0, 100);
            }
            return NULL;
        }
        atomic_fetch_add_explicit(&group->progress[id], 1, memory_order_release);
    }
    return NULL;
}

static const char *exercise_scheduler_progress(enum fault fault)
{
    struct scheduler_group group = {
        .ready = ATOMIC_VAR_INIT(0),
        .first_waiters = ATOMIC_VAR_INIT(0),
        .start = ATOMIC_VAR_INIT(0),
        .stop = ATOMIC_VAR_INIT(0),
        .failed = ATOMIC_VAR_INIT(0),
        .fault = fault,
    };
    pthread_t threads[scheduler_count];
    struct scheduler_arg args[scheduler_count];
    int created = 0;
    const char *detected = NULL;

    for (int id = 0; id < scheduler_count; ++id) {
        atomic_init(&group.tickets[id], 0);
        atomic_init(&group.progress[id], 0);
        args[id] = (struct scheduler_arg){ .group = &group, .id = id };
        const int result = pthread_create(&threads[id], NULL, scheduler_worker, &args[id]);
        if (result != 0) {
            errno = result;
            fail_errno("pthread_create");
        }
        ++created;
    }

    if (!wait_at_least(&group.ready, scheduler_count, 1000)) {
        detected = "stalled-startup";
        goto cleanup;
    }
    atomic_store_explicit(&group.start, 1, memory_order_release);
    wake_all(&group.start);
    if (!wait_at_least(&group.first_waiters, scheduler_count, 1000)) {
        detected = "stalled-startup";
        goto cleanup;
    }
    // The userspace marker is published immediately before the kernel futex
    // call. Give every worker time to cross that boundary so the skipped-wake
    // injection cannot accidentally become a valid compare-before-block race.
    sleep_milliseconds(20);

    for (int round = 1; round <= scheduler_rounds; ++round) {
        for (int id = 0; id < scheduler_count; ++id) {
            atomic_store_explicit(&group.tickets[id], round, memory_order_release);
            if (!(fault == fault_lost_wakeup && id == 0 && round == 1)) {
                wake_all(&group.tickets[id]);
            }
        }
        for (int id = 0; id < scheduler_count; ++id) {
            if (!wait_progress(&group.progress[id], (uint_fast64_t)round, 500)) {
                detected = fault == fault_lost_wakeup ? "lost-wakeup" : "scheduler-stall";
                goto cleanup;
            }
        }
    }
    if (atomic_load_explicit(&group.failed, memory_order_acquire) != 0) {
        detected = fault == fault_lost_wakeup ? "lost-wakeup" : "scheduler-stall";
    }

cleanup:
    atomic_store_explicit(&group.stop, 1, memory_order_release);
    wake_all(&group.start);
    for (int id = 0; id < scheduler_count; ++id) {
        wake_all(&group.tickets[id]);
    }
    for (int id = 0; id < created; ++id) {
        const int result = pthread_join(threads[id], NULL);
        if (result != 0) {
            errno = result;
            fail_errno("pthread_join");
        }
    }
    return detected;
}

static const char *exercise_compare_before_block(enum fault fault)
{
    atomic_int word = ATOMIC_VAR_INIT(1);
    const int expected = fault == fault_premature_block ? 1 : 0;
    errno = 0;
    const int result = wait_for_value_change(&word, expected, 50);
    if (fault == fault_premature_block) {
        return result < 0 && errno == ETIMEDOUT ? "premature-futex-block" : "oracle-missed-fault";
    }
    if (result != -1 || errno != EAGAIN) {
        return "compare-before-block";
    }
    return NULL;
}

static void signal_handler(int signal_number)
{
    (void)signal_number;
    atomic_fetch_add_explicit(&signals_seen, 1, memory_order_relaxed);
}

static void *signal_waiter_main(void *raw)
{
    struct signal_waiter *waiter = raw;
    atomic_store_explicit(&waiter->armed, 1, memory_order_release);
    wake_all(&waiter->armed);
    errno = 0;
    const int result = futex_wait(&waiter->futex_word, 0, NULL);
    atomic_store_explicit(&waiter->error, errno, memory_order_relaxed);
    atomic_store_explicit(&waiter->result, result, memory_order_release);
    return NULL;
}

static const char *exercise_signal_interruption(void)
{
    struct sigaction action = {0};
    action.sa_handler = signal_handler;
    if (sigemptyset(&action.sa_mask) != 0 || sigaction(SIGUSR1, &action, NULL) != 0) {
        fail_errno("sigaction");
    }

    struct signal_waiter waiter = {
        .armed = ATOMIC_VAR_INIT(0),
        .futex_word = ATOMIC_VAR_INIT(0),
        .result = ATOMIC_VAR_INIT(999),
        .error = ATOMIC_VAR_INIT(0),
    };
    pthread_t thread;
    int result = pthread_create(&thread, NULL, signal_waiter_main, &waiter);
    if (result != 0) {
        errno = result;
        fail_errno("pthread_create signal waiter");
    }
    if (!wait_at_least(&waiter.armed, 1, 1000)) {
        return "signal-waiter-startup";
    }
    sleep_milliseconds(10);
    result = pthread_kill(thread, SIGUSR1);
    if (result != 0) {
        errno = result;
        fail_errno("pthread_kill");
    }
    result = pthread_join(thread, NULL);
    if (result != 0) {
        errno = result;
        fail_errno("pthread_join signal waiter");
    }
    if (atomic_load_explicit(&signals_seen, memory_order_relaxed) != 1
        || atomic_load_explicit(&waiter.result, memory_order_acquire) != -1
        || atomic_load_explicit(&waiter.error, memory_order_relaxed) != EINTR) {
        return "signal-interruption";
    }
    return NULL;
}

static int clone_child_main(void *raw)
{
    struct clone_lifecycle *lifecycle = raw;
    atomic_store_explicit(
        &lifecycle->observed_tid,
        (int)syscall(SYS_gettid),
        memory_order_release
    );
    atomic_store_explicit(&lifecycle->started, 1, memory_order_release);
    wake_all(&lifecycle->started);
    while (atomic_load_explicit(&lifecycle->allow_exit, memory_order_acquire) == 0) {
        (void)wait_for_value_change(&lifecycle->allow_exit, 0, 100);
    }
    if (lifecycle->fault == fault_exit_join) {
        while (atomic_load_explicit(&lifecycle->hold_exit, memory_order_acquire) == 0) {
            (void)wait_for_value_change(&lifecycle->hold_exit, 0, 100);
        }
    }
    return 0;
}

static bool wait_for_child_tid_clear(atomic_int *child_tid, uint64_t timeout_ms)
{
    const uint64_t deadline = monotonic_milliseconds() + timeout_ms;
    for (;;) {
        const int tid = atomic_load_explicit(child_tid, memory_order_acquire);
        if (tid == 0) {
            return true;
        }
        if (monotonic_milliseconds() >= deadline) {
            return false;
        }
        (void)wait_for_value_change(child_tid, tid, 50);
    }
}

static const char *exercise_clone_clear_child_tid(enum fault fault)
{
    void *stack = mmap(
        NULL,
        clone_stack_size,
        PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS | MAP_STACK,
        -1,
        0
    );
    if (stack == MAP_FAILED) {
        fail_errno("mmap clone stack");
    }
    struct clone_lifecycle lifecycle = {
        .started = ATOMIC_VAR_INIT(0),
        .allow_exit = ATOMIC_VAR_INIT(0),
        .hold_exit = ATOMIC_VAR_INIT(0),
        .child_tid = ATOMIC_VAR_INIT(0),
        .observed_tid = ATOMIC_VAR_INIT(0),
        .fault = fault,
    };
    atomic_int parent_tid = ATOMIC_VAR_INIT(0);
    const int flags = CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD
        | CLONE_SYSVSEM | CLONE_PARENT_SETTID | CLONE_CHILD_SETTID | CLONE_CHILD_CLEARTID;
    void *stack_top = (char *)stack + clone_stack_size;
    const int tid = clone(
        clone_child_main,
        stack_top,
        flags,
        &lifecycle,
        &parent_tid,
        NULL,
        &lifecycle.child_tid
    );
    if (tid < 0) {
        fail_errno("clone");
    }
    const char *detected = NULL;
    if (!wait_at_least(&lifecycle.started, 1, 1000)) {
        detected = "clone-startup";
        goto release;
    }
    const int recorded_parent_tid = atomic_load_explicit(&parent_tid, memory_order_acquire);
    const int recorded_child_tid = atomic_load_explicit(&lifecycle.child_tid, memory_order_acquire);
    const int observed_tid = atomic_load_explicit(&lifecycle.observed_tid, memory_order_acquire);
    if (recorded_parent_tid != tid || recorded_child_tid != tid || observed_tid != tid) {
        detected = "clone-tid-publication";
        goto release;
    }
    atomic_store_explicit(&lifecycle.allow_exit, 1, memory_order_release);
    wake_all(&lifecycle.allow_exit);
    if (!wait_for_child_tid_clear(&lifecycle.child_tid, 500)) {
        detected = fault == fault_exit_join ? "thread-exit-join" : "clear-child-tid";
    }

release:
    atomic_store_explicit(&lifecycle.allow_exit, 1, memory_order_release);
    atomic_store_explicit(&lifecycle.hold_exit, 1, memory_order_release);
    wake_all(&lifecycle.allow_exit);
    wake_all(&lifecycle.hold_exit);
    if (!wait_for_child_tid_clear(&lifecycle.child_tid, 1000)) {
        fprintf(stderr, "cleanup could not observe clear_child_tid\n");
        exit(2);
    }
    if (munmap(stack, clone_stack_size) != 0) {
        fail_errno("munmap clone stack");
    }
    return detected;
}

static enum fault parse_fault(const char *name)
{
    if (strcmp(name, "none") == 0) {
        return fault_none;
    }
    if (strcmp(name, "lost-wakeup") == 0) {
        return fault_lost_wakeup;
    }
    if (strcmp(name, "stalled-startup") == 0) {
        return fault_stalled_startup;
    }
    if (strcmp(name, "premature-futex-block") == 0) {
        return fault_premature_block;
    }
    if (strcmp(name, "scheduler-stall") == 0) {
        return fault_scheduler_stall;
    }
    if (strcmp(name, "thread-exit-join") == 0) {
        return fault_exit_join;
    }
    fprintf(stderr, "unknown fault: %s\n", name);
    exit(2);
}

static const char *fault_name(enum fault fault)
{
    switch (fault) {
    case fault_none:
        return "none";
    case fault_lost_wakeup:
        return "lost-wakeup";
    case fault_stalled_startup:
        return "stalled-startup";
    case fault_premature_block:
        return "premature-futex-block";
    case fault_scheduler_stall:
        return "scheduler-stall";
    case fault_exit_join:
        return "thread-exit-join";
    }
    return "invalid";
}

int main(int argc, char **argv)
{
    if (argc != 3 || strcmp(argv[1], "--inject") != 0) {
        fprintf(stderr, "usage: %s --inject <none|lost-wakeup|stalled-startup|premature-futex-block|scheduler-stall|thread-exit-join>\n", argv[0]);
        return 2;
    }
    const enum fault fault = parse_fault(argv[2]);
    const char *detected = exercise_compare_before_block(fault);
    if (detected == NULL && fault != fault_premature_block) {
        detected = exercise_signal_interruption();
    }
    if (detected == NULL && fault != fault_premature_block) {
        detected = exercise_clone_clear_child_tid(fault);
    }
    if (detected == NULL && fault != fault_premature_block && fault != fault_exit_join) {
        detected = exercise_scheduler_progress(fault);
    }

    if (fault == fault_none) {
        if (detected != NULL) {
            fprintf(stderr, "status=fail detected=%s injected=none\n", detected);
            return 1;
        }
        printf(
            "status=pass schedulers=%d rounds=%d futex=wait-wake compare_before_block=pass signal_eintr=pass clear_child_tid=pass scheduler_progress=pass\n",
            scheduler_count,
            scheduler_rounds
        );
        return 0;
    }
    if (detected == NULL || strcmp(detected, fault_name(fault)) != 0) {
        fprintf(
            stderr,
            "status=fail oracle=missed injected=%s detected=%s\n",
            fault_name(fault),
            detected == NULL ? "none" : detected
        );
        return 2;
    }
    fprintf(stderr, "status=fail detected=%s injected=%s\n", detected, fault_name(fault));
    return 1;
}
