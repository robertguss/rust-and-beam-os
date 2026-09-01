use core::{
    fmt::{self, Write},
    ptr,
    sync::atomic::{AtomicUsize, Ordering},
};

const UART_FR: usize = 0x18;
const UART_DR: usize = 0x00;
const UART_FR_TXFF: u32 = 1 << 5;

static UART_BASE: AtomicUsize = AtomicUsize::new(0);

pub fn init(base: usize) {
    UART_BASE.store(base, Ordering::Release);
}

pub fn event(name: &str, fields: fmt::Arguments<'_>) {
    let mut serial = Serial;
    let _ = writeln!(
        serial,
        "{{\"component\":\"virtio-probe\",\"event\":\"{name}\"{fields}}}"
    );
}

pub fn panic_line(info: &core::panic::PanicInfo<'_>) {
    let mut serial = Serial;
    let _ = writeln!(
        serial,
        "{{\"component\":\"virtio-probe\",\"event\":\"panic\"}}"
    );
    let _ = writeln!(serial, "{info}");
}

struct Serial;

impl Write for Serial {
    fn write_str(&mut self, value: &str) -> fmt::Result {
        let base = UART_BASE.load(Ordering::Acquire);
        if base == 0 {
            return Err(fmt::Error);
        }
        for byte in value.bytes() {
            write_byte(base, byte);
        }
        Ok(())
    }
}

fn write_byte(base: usize, byte: u8) {
    // SAFETY: `init` stores the PL011 MMIO base discovered from the trusted QEMU DTB.
    unsafe {
        while ptr::read_volatile((base + UART_FR) as *const u32) & UART_FR_TXFF != 0 {
            core::hint::spin_loop();
        }
        ptr::write_volatile((base + UART_DR) as *mut u32, u32::from(byte));
    }
}
