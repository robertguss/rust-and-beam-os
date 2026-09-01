#define _GNU_SOURCE

#include <errno.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <unistd.h>

#define ALTERNATE_STACK_SIZE (64 * 1024)

static unsigned char alternate_stack[ALTERNATE_STACK_SIZE];
static volatile sig_atomic_t signal_seen;
static volatile sig_atomic_t signal_on_alternate_stack;

static int fail(const char *scenario) {
    fprintf(stderr, "beam-host-fault-probe: scenario=%s status=fail errno=%d\n", scenario, errno);
    return 1;
}

static void signal_handler(int number) {
    unsigned char marker;
    uintptr_t pointer = (uintptr_t)&marker;
    uintptr_t start = (uintptr_t)alternate_stack;
    uintptr_t end = start + sizeof(alternate_stack);
    signal_seen = number == SIGUSR1;
    signal_on_alternate_stack = pointer >= start && pointer < end;
}

static void *cancellable_reader(void *argument) {
    int *descriptors = argument;
    char ready = 'r';
    char byte;
    if (write(descriptors[1], &ready, 1) != 1) {
        return (void *)1;
    }
    if (read(descriptors[2], &byte, 1) < 0) {
        return (void *)1;
    }
    return NULL;
}

static void *exiting_thread(void *argument) {
    return argument;
}

static int allocation_failure(void) {
    errno = 0;
    void *mapping = mmap(NULL, SIZE_MAX / 2, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping != MAP_FAILED || (errno != ENOMEM && errno != EINVAL)) {
        if (mapping != MAP_FAILED) {
            munmap(mapping, SIZE_MAX / 2);
        }
        return fail("allocation");
    }
    return 0;
}

static int copy_failure(void) {
    int descriptors[2];
    if (pipe(descriptors) != 0) {
        return fail("copy-pipe");
    }
    void *guard = mmap(NULL, (size_t)sysconf(_SC_PAGESIZE), PROT_NONE,
                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    char byte = 'c';
    if (guard == MAP_FAILED || write(descriptors[1], &byte, 1) != 1) {
        return fail("copy-setup");
    }
    errno = 0;
    ssize_t copied = read(descriptors[0], guard, 1);
    int saved_errno = errno;
    if (munmap(guard, (size_t)sysconf(_SC_PAGESIZE)) != 0 ||
        close(descriptors[0]) != 0 || close(descriptors[1]) != 0) {
        return fail("copy-cleanup");
    }
    errno = saved_errno;
    if (copied != -1 || errno != EFAULT) {
        return fail("copy");
    }
    return 0;
}

static int timeout_path(void) {
    struct timespec timeout = {.tv_sec = 0, .tv_nsec = 1000000};
    if (ppoll(NULL, 0, &timeout, NULL) != 0) {
        return fail("timeout");
    }
    return 0;
}

static int cancellation_path(void) {
    int ready[2];
    int blocked[2];
    pthread_t thread;
    char marker;
    if (pipe(ready) != 0 || pipe(blocked) != 0) {
        return fail("cancellation-pipe");
    }
    int descriptors[] = {ready[0], ready[1], blocked[0], blocked[1]};
    if (pthread_create(&thread, NULL, cancellable_reader, descriptors) != 0 ||
        read(ready[0], &marker, 1) != 1 || marker != 'r' ||
        pthread_cancel(thread) != 0) {
        return fail("cancellation-start");
    }
    void *result = NULL;
    if (pthread_join(thread, &result) != 0 || result != PTHREAD_CANCELED) {
        return fail("cancellation-join");
    }
    for (size_t index = 0; index < sizeof(descriptors) / sizeof(descriptors[0]); index++) {
        if (close(descriptors[index]) != 0) {
            return fail("cancellation-close");
        }
    }
    return 0;
}

static int signal_path(void) {
    stack_t stack = {
        .ss_sp = alternate_stack,
        .ss_flags = 0,
        .ss_size = sizeof(alternate_stack),
    };
    struct sigaction action = {0};
    action.sa_handler = signal_handler;
    action.sa_flags = SA_ONSTACK;
    sigemptyset(&action.sa_mask);
    if (sigaltstack(&stack, NULL) != 0 ||
        sigaction(SIGUSR1, &action, NULL) != 0 ||
        pthread_kill(pthread_self(), SIGUSR1) != 0 ||
        !signal_seen || !signal_on_alternate_stack) {
        return fail("signal");
    }
    return 0;
}

static int close_failure(void) {
    int descriptors[2];
    if (pipe(descriptors) != 0 || close(descriptors[0]) != 0) {
        return fail("close-setup");
    }
    errno = 0;
    int result = close(descriptors[0]);
    int saved_errno = errno;
    if (close(descriptors[1]) != 0) {
        return fail("close-cleanup");
    }
    errno = saved_errno;
    if (result != -1 || errno != EBADF) {
        return fail("close");
    }
    return 0;
}

static int thread_exit_path(void) {
    pthread_t thread;
    void *expected = (void *)(uintptr_t)0x5242;
    void *result = NULL;
    if (pthread_create(&thread, NULL, exiting_thread, expected) != 0 ||
        pthread_join(thread, &result) != 0 || result != expected) {
        return fail("thread-exit");
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        return fail("arguments");
    }
    if (allocation_failure() != 0 || copy_failure() != 0 || timeout_path() != 0 ||
        cancellation_path() != 0 || signal_path() != 0 || close_failure() != 0 ||
        thread_exit_path() != 0) {
        return 1;
    }

    FILE *output = fopen(argv[1], "w");
    if (output == NULL) {
        return fail("result-open");
    }
    fputs("{\"schema\":\"rust-beam/beam-host-fault-probe/v1\","
          "\"status\":\"pass\",\"allocation\":\"ENOMEM-or-EINVAL\","
          "\"copy\":\"EFAULT\",\"timeout\":\"expired\","
          "\"cancellation\":\"joined\",\"signal\":\"alternate-stack\","
          "\"close\":\"EBADF\",\"thread_start\":\"created\","
          "\"thread_exit\":\"joined\",\"shutdown\":\"normal\"}\n",
          output);
    if (fclose(output) != 0) {
        return fail("result-close");
    }
    return 0;
}
