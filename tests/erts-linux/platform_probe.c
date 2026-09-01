#define _GNU_SOURCE

#include <bits/hwcap.h>
#include <elf.h>
#include <pthread.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/auxv.h>
#include <sys/utsname.h>
#include <unistd.h>

static _Thread_local unsigned long tls_marker = 0x52554245414dUL;
static unsigned char alternate_stack[SIGSTKSZ];
static volatile sig_atomic_t signal_seen;
static uintptr_t signal_stack_pointer;
static uintptr_t signal_pc;
static uintptr_t signal_sp;
static unsigned long signal_pstate;
static unsigned int signal_context_magic;
static unsigned int signal_context_size;
static uintptr_t child_thread_pointer;
static intptr_t child_tls_offset;

static uintptr_t thread_pointer(void) {
    uintptr_t value;
    __asm__ volatile("mrs %0, tpidr_el0" : "=r"(value));
    return value;
}

static void handle_signal(int number, siginfo_t *info, void *context) {
    (void)number;
    (void)info;
    ucontext_t *ucontext = context;
    unsigned char stack_byte;
    const struct _aarch64_ctx *record = (const void *)ucontext->uc_mcontext.__reserved;
    signal_stack_pointer = (uintptr_t)&stack_byte;
    signal_pc = ucontext->uc_mcontext.pc;
    signal_sp = ucontext->uc_mcontext.sp;
    signal_pstate = ucontext->uc_mcontext.pstate;
    signal_context_magic = record->magic;
    signal_context_size = record->size;
    signal_seen = 1;
}

static void *thread_main(void *unused) {
    (void)unused;
    child_thread_pointer = thread_pointer();
    child_tls_offset = (intptr_t)(uintptr_t)&tls_marker - (intptr_t)child_thread_pointer;
    return NULL;
}

static int fail(const char *message) {
    fprintf(stderr, "platform-probe: %s\n", message);
    return 1;
}

static long l1_dcache_line_size(void) {
    FILE *input = fopen("/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size", "r");
    long value = -1;
    if (input != NULL) {
        if (fscanf(input, "%ld", &value) != 1) {
            value = -1;
        }
        fclose(input);
    }
    return value;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        return fail("expected one output path");
    }

    stack_t stack = {
        .ss_sp = alternate_stack,
        .ss_flags = 0,
        .ss_size = sizeof(alternate_stack),
    };
    if (sigaltstack(&stack, NULL) != 0) {
        return fail("sigaltstack failed");
    }
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_sigaction = handle_signal;
    action.sa_flags = SA_SIGINFO | SA_ONSTACK;
    sigemptyset(&action.sa_mask);
    if (sigaction(SIGUSR1, &action, NULL) != 0 || raise(SIGUSR1) != 0 || !signal_seen) {
        return fail("signal frame probe failed");
    }

    pthread_t thread;
    if (pthread_create(&thread, NULL, thread_main, NULL) != 0 || pthread_join(thread, NULL) != 0) {
        return fail("pthread TLS probe failed");
    }

    struct utsname identity;
    if (uname(&identity) != 0) {
        return fail("uname failed");
    }
    const uintptr_t main_thread_pointer = thread_pointer();
    const intptr_t main_tls_offset =
        (intptr_t)(uintptr_t)&tls_marker - (intptr_t)main_thread_pointer;
    const uintptr_t alternate_start = (uintptr_t)alternate_stack;
    const uintptr_t alternate_end = alternate_start + sizeof(alternate_stack);
    const int signal_on_alternate_stack =
        signal_stack_pointer >= alternate_start && signal_stack_pointer < alternate_end;
    const unsigned long hwcap = getauxval(AT_HWCAP);
    const unsigned long hwcap2 = getauxval(AT_HWCAP2);

    FILE *output = fopen(argv[1], "w");
    if (output == NULL) {
        return fail("cannot create output");
    }
    fprintf(
        output,
        "{\"schema\":\"rust-beam/erts-linux-platform/v1\","
        "\"sysname\":\"%s\",\"release\":\"%s\",\"machine\":\"%s\","
        "\"page_size\":%lu,\"clock_ticks\":%lu,\"configured_cpus\":%lu,"
        "\"online_cpus\":%lu,\"l1_dcache_line_size\":%ld,"
        "\"at_hwcap\":%lu,\"at_hwcap2\":%lu,\"hwcap_fp\":%s,"
        "\"hwcap_asimd\":%s,\"hwcap_atomics\":%s,"
        "\"main_thread_pointer\":%lu,\"main_tls_offset\":%ld,"
        "\"child_thread_pointer\":%lu,\"child_tls_offset\":%ld,"
        "\"siginfo_size\":%zu,\"ucontext_size\":%zu,\"mcontext_size\":%zu,"
        "\"signal_on_altstack\":%s,\"signal_pc\":%lu,\"signal_sp\":%lu,"
        "\"signal_pstate\":%lu,\"signal_context_magic\":%u,"
        "\"signal_context_size\":%u}\n",
        identity.sysname,
        identity.release,
        identity.machine,
        getauxval(AT_PAGESZ),
        getauxval(AT_CLKTCK),
        getauxval(AT_PHNUM) == 0 ? 0UL : (unsigned long)sysconf(_SC_NPROCESSORS_CONF),
        (unsigned long)sysconf(_SC_NPROCESSORS_ONLN),
        l1_dcache_line_size(),
        hwcap,
        hwcap2,
        (hwcap & HWCAP_FP) != 0 ? "true" : "false",
        (hwcap & HWCAP_ASIMD) != 0 ? "true" : "false",
        (hwcap & HWCAP_ATOMICS) != 0 ? "true" : "false",
        (unsigned long)main_thread_pointer,
        (long)main_tls_offset,
        (unsigned long)child_thread_pointer,
        (long)child_tls_offset,
        sizeof(siginfo_t),
        sizeof(ucontext_t),
        sizeof(mcontext_t),
        signal_on_alternate_stack ? "true" : "false",
        (unsigned long)signal_pc,
        (unsigned long)signal_sp,
        signal_pstate,
        signal_context_magic,
        signal_context_size);
    if (fclose(output) != 0) {
        return fail("cannot close output");
    }
    return 0;
}
