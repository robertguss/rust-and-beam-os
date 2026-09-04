# ADR 0003: Select VirtIO-MMIO for the HVF/TCG transport and reject PCI as the common choice

- Status: proposed
- Date: 2026-09-04
- Owners: devin
- Plan task: RB-T-P012
- Evidence:
  - `docs/evidence/phase-0/RB-T-P012/README.md`
  - `docs/evidence/phase-0/RB-T-P012/boots/tcg-boot-01-serial.jsonl`
  - `docs/evidence/phase-0/RB-T-P012/boots/hvf-boot-01-serial.jsonl`

## Context

RB-T-P012 must demonstrate the same AArch64 device strategy on an Apple
Silicon host under QEMU/HVF that was already proven under Linux/TCG in
RB-T-P011, then freeze the decision between the VirtIO-PCI and VirtIO-MMIO
transports. The frozen transport must support the same display and
pointer-input devices on both accelerators without leaking
accelerator-specific assumptions above the platform/device layer.

The probe uses `virtio-gpu-pci` and `virtio-tablet-pci` via ECAM BAR
allocation, GIC `interrupt-map` routing and the `virtio-drivers` 0.13.0
`PciTransport`.

## Decision

1. **Reject VirtIO-PCI as the common transport.** The PCI path is
   functionally complete under TCG but fails before device feature
   negotiation under Apple Silicon HVF whenever both the display and the
   pointer-input `virtio-pci` devices are present. It therefore cannot satisfy
   the acceptance criterion of working on both accelerators with the same
   platform abstraction.
2. **Select VirtIO-MMIO as the only remaining candidate for a unified
   transport.** The next phase must validate that `virtio-gpu-device` and
   `virtio-tablet-device` (MMIO) complete the same reset, feature
   negotiation, display-frame and input-readiness sequence on both HVF and
   TCG.
3. **Block RB-G-GATE0 until that MMIO validation exists or an HVF PCI
   workaround is found and independently reproduced.** No kernel code may
   assume a transport that is not proven on both runners.

## Governing invariant

The transport used by the kernel must be proven on every declared
accelerator (Apple Silicon HVF and Linux/TCG) before it is frozen. A
successful run under TCG alone is not sufficient evidence.

## Alternatives considered

| Alternative | Outcome |
|-------------|---------|
| Keep PCI and qualify it as "TCG only" | Rejected. The task explicitly requires the same strategy on the Mac host; two transports would leak accelerator assumptions into the platform layer. |
| Keep PCI and add an HVF-specific quirk | Deferred. No bounded workaround was found; HVF fails consistently with one or more `virtio-pci` devices after BAR allocation. |
| Switch to VirtIO-MMIO | Accepted as the path forward. MMIO is the other first-class transport for `virtio-gpu` and `virtio-tablet` in QEMU, and it was the original priority per the task wording ("test the MMIO candidate first"). |

## Consequences and residual risks

- **Positive:** The PCI/TCG evidence provides a reference of correct device
  behavior (feature bits, queue sizes, pixel format, input event codes) that
  the MMIO run must reproduce.
- **Negative:** MMIO has not yet been exercised by the current probe. The
  probe will need to be extended with a DTB-driven MMIO enumeration path and
  a `MmioTransport` variant.
- **Risk:** If MMIO also fails on HVF, the discrepancy may be in the `virtio`
  device models or in GIC/timer setup rather than the transport, and a deeper
  HVF investigation will be required.
- **Reconsideration trigger:** Either (a) an HVF run with two `virtio-pci`
  devices completes the full `frame_presented` + `ready_for_input` sequence,
  or (b) an MMIO run on HVF and TCG reproduces the same `frame_presented`
  and `ready_for_input` events.

## Verification

- Reference command (TCG, passing):
  ```
  /tmp/qemu-hvf-test/build/qemu-system-aarch64 \
    -machine virt-11.1,gic-version=3,dtb-randomness=off \
    -cpu cortex-a72 -accel tcg -smp 1 -m 512M \
    -nodefaults -no-reboot -no-shutdown -display none \
    -serial file:/tmp/tcg-test1/serial \
    -kernel tests/virtio-probe/target/aarch64-unknown-none/release/virtio-probe.img \
    -device virtio-gpu-pci,id=gpu0,bus=pcie.0,addr=1,xres=640,yres=480 \
    -device virtio-tablet-pci,id=pointer0,bus=pcie.0,addr=2
  ```
- Failing command (HVF):
  Replace `-cpu cortex-a72 -accel tcg` with `-cpu host -accel hvf`; the
  probe reaches `pci_bar` for the second device and then loses sync.

## Durable evidence

- `docs/evidence/phase-0/RB-T-P012/README.md`
- `docs/evidence/phase-0/RB-T-P012/boots/tcg-boot-01-serial.jsonl`
- `docs/evidence/phase-0/RB-T-P012/boots/hvf-boot-01-serial.jsonl`
