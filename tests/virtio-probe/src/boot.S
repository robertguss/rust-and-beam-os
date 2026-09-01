.section .text.boot, "ax"
.global _start
.type _start, %function
_start:
    b primary_entry
    .long 0
    .quad 0x80000
    .quad __image_end - _start
    .quad 0
    .quad 0
    .quad 0
    .quad 0
    .ascii "ARM\x64"
    .long 0

primary_entry:
    mov x20, x0

    mrs x1, cpacr_el1
    orr x1, x1, #(3 << 20)
    msr cpacr_el1, x1
    isb

    adrp x1, __stack_top
    add x1, x1, :lo12:__stack_top
    mov sp, x1

    adrp x1, __bss_start
    add x1, x1, :lo12:__bss_start
    adrp x2, __bss_end
    add x2, x2, :lo12:__bss_end
1:
    cmp x1, x2
    b.hs 2f
    stp xzr, xzr, [x1], #16
    b 1b
2:
    mov x0, x20
    bl rust_main
3:
    wfe
    b 3b
.size _start, . - _start

.section .bss.stack, "aw", %nobits
.align 12
__stack_bottom:
    .skip 0x40000
.global __stack_top
__stack_top:
