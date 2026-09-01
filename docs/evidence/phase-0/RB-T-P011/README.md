# RB-T-P011 evidence

This is **target** evidence for an independent bare-metal `aarch64-unknown-none`
probe under QEMU TCG. It is not evidence that the future project kernel or BEAM
runtime can drive these devices, and it does not freeze the final RB-T-P014
platform profile.

## Mechanism and result

`just test-virtio-probe-tcg` built the `no_std` probe offline and ran ten fresh
QEMU processes. All ten passed. The sealed profile was QEMU 11.1.0,
`virt-11.1,gic-version=3,dtb-randomness=off`, Cortex-A53, `tcg,thread=single`,
one CPU, 512 MiB, no default devices, no semihosting, and `-display none`. Its
only explicit devices were a 640×480 `virtio-gpu-pci` at PCI address 1 and a
`virtio-tablet-pci` at address 2. The guest did not use those addresses
directly: it parsed QEMU's DTB for PL011, RAM, ECAM, PCI bus and 32-bit MMIO
windows and the PCI interrupt map, sized and allocated BARs through ECAM, and
identified GPU/input functions by VirtIO device type. It read each function's
INTx pin from ECAM and resolved the DTB routes to GIC IRQ 36 for the GPU and 37
for input, both level-high.

Every boot presented two synchronous B8G8R8A8 frames from a driver-owned DMA
buffer with 2,560-byte stride. QMP injected absolute coordinates 24,575 and
16,384, which the guest mapped to pixel 479,239, followed by left press/release
and a right-button capture acknowledgement. Each serial trace contains eight
input events and three observed interrupt-status transitions. The second frame
contains a changed green center, a software pointer marker, a hardware cursor,
and four stable corner colors. QMP's 640×480 PPM was checked by pixel value;
`screenshot.png` is the reviewable rendering.

`aggregate.json` records ten of ten passes, two frames and eight input events
per boot, and zero DMA bounds violations. Each `boots/boot-NN-receipt.json`
retains the exact QEMU argv, QMP machine/device metadata, hashes of its DTB,
screenshot, QMP trace, and serial trace, and the structured contract summary.
The corresponding QMP and serial traces are retained beside every receipt.
`machine.dtb` is the first boot's binary tree and `machine.dts` is its decoded
form. `qemu-provenance.json` binds the executable hash to the verified
141,831,772-byte QEMU source archive and Meson's no-download wrap policy.

## VirtIO contract

Both transports offered `VIRTIO_F_VERSION_1`, retained `FEATURES_OK`, and
reported their queue maxima (GPU 64/16, input 64/64). The probe selected only
VERSION_1: `VIRTIO_F_ACCESS_PLATFORM` remained clear because the DTB advertises
`dma-coherent` and the HAL uses identity DMA. Queue/ring ordering uses the
crate's sequentially consistent notification fence and acquire/release ring
operations. The probe also:

- observed `FAILED`, reset each device to status zero, and then reinitialized;
- filled a two-entry queue, observed `QueueFull`, and recovered by reset;
- sent a four-byte malformed GPU request into a guarded 32-byte output, received
  a bounded 24-byte response before timeout, and preserved both canaries;
- polled with CPU IRQs masked, observed interrupt status, and proved an
  immediate duplicate ISR acknowledgement was empty; and
- reset transports on drop, matched all 14 DMA allocations with 14
  deallocations, and reported no RAM/MMIO bounds violation in every boot.

## Dependency and unsafe boundary

The nested lockfile pins `virtio-drivers` 0.13.0. Default features are disabled
and the only directly enabled crate feature is `alloc`; `crate-features.txt`
records the complete resolved feature graph. The 96,008-byte MIT-licensed crate
archive has SHA-256
`cfdc1c628cdd8ce7c3b9e65a8ed550d0338e9ef9f911e729666f1cce097de2f7` and reports
upstream commit `c5d3ea74d5896036c4760d6199c1a1cc1257b659`. The source ledger
records the immutable locator, claim, consumer, and limitation.

The probe's unsafe integration points are deliberately narrow and documented at
their call sites:

- `boot.S` installs the stack, clears BSS, enables AArch64 FP/SIMD, and passes
  the bootloader DTB pointer to Rust;
- `fdt.rs` bounds the raw DTB slice with its validated header and parses all
  subsequent offsets from that slice;
- `hal.rs` implements the fixed bump allocator and `virtio_drivers::Hal`, with
  identity DMA restricted to discovered RAM and MMIO restricted to the
  discovered PCI window;
- `main.rs` constructs ECAM MMIO, upholds `VirtQueue::add`/`pop_used` buffer
  lifetimes, and temporarily reconstructs the uniquely owned framebuffer slice
  between driver calls; and
- `serial.rs` performs volatile PL011 status and data-register access at the
  DTB-discovered base.

## Learning checkpoint

The governing invariant is that the device, driver, and host observe one ordered
ownership transition for every queue buffer: transport status and features must
be accepted before DRIVER_OK, descriptor memory must remain live and in
discovered coherent RAM until used-ring completion or reset, and teardown must
reset the transport before releasing DMA. A plausible failure is a wrong
BAR/window or stale/non-coherent descriptor making a visually plausible first
frame while corrupting memory, losing input, or leaking a queue across reset. A
screenshot alone cannot distinguish that accident. The saved feature/status
readbacks, queue exhaustion, malformed-response canaries, polling/duplicate-ISR
checks, exact input events, bounds counters, matched DMA teardown, reset traces,
QMP metadata, and ten independent processes jointly exercise the mechanism and
its negative paths.

`verification.txt` records both required task commands and the complete crate
feature report. The retained evidence proves only this isolated TCG device path.
