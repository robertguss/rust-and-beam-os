# RB-T-P012 Evidence: Apple Silicon HVF vs Linux/TCG VirtIO transport probe

## Summary

The bare-metal `virtio-probe` kernel was built and run under two QEMU
configurations:

- `tcg-boot-01-serial.jsonl` — QEMU TCG with `cortex-a72`, same `-machine
  virt-11.1` and same `virtio-gpu-pci` + `virtio-tablet-pci` layout.
- `hvf-boot-01-serial.jsonl` — QEMU HVF on Apple Silicon (`-accel hvf`,
  `-cpu host`), otherwise identical command.

## Observed results

### TCG (reference)

The probe completes the full device-status, feature-negotiation, reset, queue
exhaustion, display-frame, and pointer-input readiness sequence. Key events
include:

- `transport_audit` for both `gpu` and `input` with `version_1_offered` true
  and `features_ok_readback` true.
- `frame_presented` with `width=640,height=480` and
  `pixel_format="B8G8R8A8_UNORM"`.
- `ready_for_input` with absolute axis and button codes.

This establishes that the PCI transport, ECAM enumeration, GIC routing and
QEMU `virtio-pci` devices behave correctly under TCG.

### HVF (target accelerator)

The probe reaches PCI BAR allocation and then the vCPU loses sync before any
`transport_audit` event. The last serial record is `pci_bar` for the
`virtio-tablet-pci` BARs. The same kernel binary and DTB are used as in the
TCG run.

Variants tested on HVF with the same outcome:

- `virtio-gpu-pci` + `virtio-tablet-pci` on separate PCI slots (`addr=1` and
  `addr=2`, `addr=3`).
- Both devices on a multifunction slot (`addr=1.0` and `addr=1.1`).
- Single `virtio-gpu-pci` without input — the probe fails later because the
  pointer-input device is required, but it still does not complete the
  combined display+input scenario.

## Interpretation

The discrepancy is specific to the HVF accelerator and the presence of a second
`virtio-pci` device on the `gpex` root bus. TCG proves the PCI path is
otherwise valid; HVF fails before feature negotiation. This makes PCI an
unacceptable universal transport for the projected HVF and TCG runners until
either an HVF-specific workaround or an MMIO alternative is validated.
