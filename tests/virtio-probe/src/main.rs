#![no_std]
#![no_main]

extern crate alloc;

use core::{arch::global_asm, hint::spin_loop};
use virtio_drivers::{
    Error,
    device::{gpu::VirtIOGpu, input::VirtIOInput},
    queue::VirtQueue,
    transport::{
        DeviceStatus, DeviceType, Transport,
        pci::bus::{BarInfo, Cam, Command, DeviceFunction, MemoryBarType, MmioCam, PciRoot},
        pci::{PciTransport, virtio_device_type},
    },
};

mod fdt;
mod hal;
mod serial;

use fdt::Platform;
use hal::ProbeHal;

global_asm!(include_str!("boot.S"));

const VERSION_1: u64 = 1 << 32;
const ACCESS_PLATFORM: u64 = 1 << 33;
const EV_SYN: u16 = 0;
const EV_KEY: u16 = 1;
const EV_ABS: u16 = 3;
const ABS_X: u16 = 0;
const ABS_Y: u16 = 1;
const BTN_LEFT: u16 = 0x110;
const BTN_RIGHT: u16 = 0x111;
const AUDIT_SPINS: usize = 10_000_000;
const INPUT_SPINS: usize = 2_000_000_000;

#[global_allocator]
static ALLOCATOR: hal::ProbeAllocator = hal::ProbeAllocator;

#[unsafe(no_mangle)]
extern "C" fn rust_main(dtb_address: usize) -> ! {
    match run(dtb_address) {
        Ok(()) => finish(),
        Err(stage) => {
            serial::event("fail", format_args!(",\"stage\":\"{stage}\""));
            finish()
        }
    }
}

fn run(dtb_address: usize) -> Result<(), &'static str> {
    // SAFETY: `boot.S` passes through QEMU's FDT pointer from x0 before changing it.
    let platform = unsafe { fdt::discover(dtb_address) }.map_err(|error| error.0)?;
    serial::init(platform.uart_base);
    serial::event(
        "boot",
        format_args!(
            ",\"dtb_address\":{},\"dtb_size\":{},\"irq_mode\":\"masked-polling\"",
            dtb_address, platform.dtb_size
        ),
    );
    validate_platform(&platform)?;

    serial::event(
        "platform",
        format_args!(
            ",\"uart_base\":{},\"uart_size\":{},\"ram_start\":{},\"ram_size\":{},\"ecam_base\":{},\"ecam_size\":{},\"pci_mmio_base\":{},\"pci_mmio_size\":{},\"bus_start\":{},\"bus_end\":{},\"dma_coherent\":true",
            platform.uart_base,
            platform.uart_size,
            platform.ram_start,
            platform.ram_size,
            platform.pci_ecam_base,
            platform.pci_ecam_size,
            platform.pci_mmio_base,
            platform.pci_mmio_size,
            platform.pci_bus_start,
            platform.pci_bus_end,
        ),
    );

    // SAFETY: The DTB describes an ECAM window of at least `Cam::Ecam.size()` bytes, and all PCI
    // config accesses in this single-core probe go through this root.
    let cam = unsafe { MmioCam::new(platform.pci_ecam_base as *mut u8, Cam::Ecam) };
    let mut root = PciRoot::new(cam);
    let (gpu_function, input_function) = find_devices(&root, platform.pci_bus_start)?;
    let gpu_pin = pci_interrupt_pin(platform.pci_ecam_base, gpu_function)?;
    let input_pin = pci_interrupt_pin(platform.pci_ecam_base, input_function)?;
    let gpu_route = platform
        .pci_interrupt_route(
            gpu_function.bus,
            gpu_function.device,
            gpu_function.function,
            gpu_pin,
        )
        .ok_or("GPU PCI interrupt route not found in DTB")?;
    let input_route = platform
        .pci_interrupt_route(
            input_function.bus,
            input_function.device,
            input_function.function,
            input_pin,
        )
        .ok_or("input PCI interrupt route not found in DTB")?;
    serial::event(
        "pci_interrupts",
        format_args!(
            ",\"source\":\"ECAM interrupt pin plus DTB interrupt-map\",\"parent_phandle\":{},\"route_count\":{},\"gpu_pin\":{},\"gpu_gic_irq\":{},\"gpu_flags\":{},\"input_pin\":{},\"input_gic_irq\":{},\"input_flags\":{}",
            platform.pci_interrupt_parent,
            platform.pci_interrupt_route_count,
            gpu_pin,
            gpu_route.gic_irq,
            gpu_route.flags,
            input_pin,
            input_route.gic_irq,
            input_route.flags,
        ),
    );
    let mut next_bar = platform.pci_mmio_base;
    let mmio_end = next_bar
        .checked_add(platform.pci_mmio_size)
        .ok_or("PCI MMIO window overflow")?;
    allocate_bars(&mut root, gpu_function, &mut next_bar, mmio_end)?;
    allocate_bars(&mut root, input_function, &mut next_bar, mmio_end)?;

    // SAFETY: The GPU BAR 4 is identity-mapped and sized at least 4 KiB by allocate_bars.
    audit_transport(&mut root, gpu_function, "gpu", true)?;
    audit_transport(&mut root, input_function, "input", false)?;

    let gpu_transport = PciTransport::new::<ProbeHal, _>(&mut root, gpu_function)
        .map_err(|_| "create GPU PCI transport")?;
    let mut gpu = VirtIOGpu::<ProbeHal, _>::new(gpu_transport).map_err(|_| "initialize GPU")?;
    let (width, height) = gpu.resolution().map_err(|_| "read GPU resolution")?;
    if width < 320 || height < 240 || width > 4096 || height > 2160 {
        return Err("unsupported GPU resolution");
    }
    let frame_bytes = usize::try_from(width)
        .ok()
        .and_then(|width| width.checked_mul(height as usize))
        .and_then(|pixels| pixels.checked_mul(4))
        .ok_or("framebuffer size overflow")?;
    let framebuffer = gpu
        .setup_framebuffer()
        .map_err(|_| "setup GPU framebuffer")?;
    if framebuffer.len() < frame_bytes {
        return Err("short GPU framebuffer");
    }
    draw_frame(framebuffer, width, height, 1, 0, 0, false);
    // SAFETY invariant: `gpu` owns this DMA allocation and remains alive and unmoved until all raw
    // framebuffer access below has ended. No driver method returns a second framebuffer reference.
    let framebuffer_address = framebuffer.as_mut_ptr() as usize;
    let framebuffer_length = framebuffer.len();
    let _ = framebuffer;
    gpu.flush().map_err(|_| "flush initial GPU frame")?;

    let mut cursor = [0u8; 64 * 64 * 4];
    draw_cursor(&mut cursor);
    gpu.setup_cursor(&cursor, width / 4, height / 4, 1, 1)
        .map_err(|_| "setup GPU cursor")?;
    serial::event(
        "frame_presented",
        format_args!(
            ",\"frame\":1,\"width\":{},\"height\":{},\"stride\":{},\"pixel_format\":\"B8G8R8A8_UNORM\",\"buffer_owner\":\"VirtIOGpu DMA\",\"present_completion\":\"synchronous used-ring response\",\"hardware_cursor\":true",
            width,
            height,
            width * 4
        ),
    );

    let input_transport = PciTransport::new::<ProbeHal, _>(&mut root, input_function)
        .map_err(|_| "create input PCI transport")?;
    let mut input =
        VirtIOInput::<ProbeHal, _>::new(input_transport).map_err(|_| "initialize input")?;
    let input_name_len = input.name().map_err(|_| "query input name")?.len();
    let abs_bits = input.ev_bits(EV_ABS as u8).map_err(|_| "query ABS bits")?;
    let key_bits = input.ev_bits(EV_KEY as u8).map_err(|_| "query KEY bits")?;
    if !bitmap_has(&abs_bits, ABS_X) || !bitmap_has(&abs_bits, ABS_Y) {
        return Err("input device lacks absolute X/Y");
    }
    if !bitmap_has(&key_bits, BTN_LEFT) || !bitmap_has(&key_bits, BTN_RIGHT) {
        return Err("input device lacks required buttons");
    }
    let x_info = input
        .abs_info(ABS_X as u8)
        .map_err(|_| "query ABS_X range")?;
    let y_info = input
        .abs_info(ABS_Y as u8)
        .map_err(|_| "query ABS_Y range")?;
    if x_info.max <= x_info.min || y_info.max <= y_info.min {
        return Err("invalid absolute input range");
    }
    serial::event(
        "ready_for_input",
        format_args!(
            ",\"input_name_length\":{},\"event_queue_size\":32,\"status_queue_size\":32,\"abs_x_code\":{},\"abs_y_code\":{},\"left_code\":{},\"right_code\":{},\"x_min\":{},\"x_max\":{},\"y_min\":{},\"y_max\":{}",
            input_name_len,
            ABS_X,
            ABS_Y,
            BTN_LEFT,
            BTN_RIGHT,
            x_info.min,
            x_info.max,
            y_info.min,
            y_info.max,
        ),
    );

    let mut x_raw = x_info.min;
    let mut y_raw = y_info.min;
    let mut x_seen = false;
    let mut y_seen = false;
    let mut left_down = false;
    let mut left_up = false;
    let mut capture_ready = false;
    let mut capture_ack = false;
    let mut frame_count = 1u32;
    let mut input_count = 0u32;
    let mut interrupt_count = 0u32;
    let mut duplicate_ack_empty = false;

    for _ in 0..INPUT_SPINS {
        let interrupt = input.ack_interrupt();
        if !interrupt.is_empty() {
            interrupt_count += 1;
            duplicate_ack_empty |= input.ack_interrupt().is_empty();
        }

        while let Some(event) = input.pop_pending_event() {
            input_count += 1;
            serial::event(
                "input_event",
                format_args!(
                    ",\"sequence\":{},\"type\":{},\"code\":{},\"value\":{}",
                    input_count, event.event_type, event.code, event.value
                ),
            );
            match (event.event_type, event.code) {
                (EV_ABS, ABS_X) => {
                    x_raw = event.value;
                    x_seen = true;
                }
                (EV_ABS, ABS_Y) => {
                    y_raw = event.value;
                    y_seen = true;
                }
                (EV_KEY, BTN_LEFT) if event.value == 1 => left_down = true,
                (EV_KEY, BTN_LEFT) if event.value == 0 && left_down => left_up = true,
                (EV_KEY, BTN_RIGHT) if event.value == 1 && capture_ready => capture_ack = true,
                (EV_SYN, _) if x_seen && y_seen && frame_count == 1 => {
                    let x = scale_axis(x_raw, x_info.min, x_info.max, width);
                    let y = scale_axis(y_raw, y_info.min, y_info.max, height);
                    // SAFETY: The ownership and lifetime invariant documented when this pointer was
                    // captured still holds; this temporary slice ends before the next GPU method.
                    let framebuffer = unsafe {
                        core::slice::from_raw_parts_mut(
                            framebuffer_address as *mut u8,
                            framebuffer_length,
                        )
                    };
                    draw_frame(framebuffer, width, height, 2, x, y, true);
                    gpu.move_cursor(x, y).map_err(|_| "move GPU cursor")?;
                    gpu.flush().map_err(|_| "flush changed GPU frame")?;
                    frame_count = 2;
                    serial::event(
                        "frame_presented",
                        format_args!(
                            ",\"frame\":2,\"cursor_x\":{},\"cursor_y\":{},\"x_raw\":{},\"y_raw\":{}",
                            x, y, x_raw, y_raw
                        ),
                    );
                }
                _ => {}
            }
        }

        if !capture_ready && frame_count == 2 && left_down && left_up {
            capture_ready = true;
            serial::event(
                "ready_for_capture",
                format_args!(
                    ",\"frames\":{},\"input_events\":{},\"left_down\":true,\"left_up\":true",
                    frame_count, input_count
                ),
            );
        }
        if capture_ack {
            break;
        }
        spin_loop();
    }
    if !capture_ack {
        return Err("input or capture acknowledgement timeout");
    }

    drop(input);
    drop(gpu);
    let counters = hal::counters();
    if counters.bounds_violations != 0
        || counters.dma_allocations == 0
        || counters.dma_allocations != counters.dma_deallocations
        || interrupt_count == 0
        || !duplicate_ack_empty
    {
        return Err("DMA teardown or interrupt acknowledgement invariant failed");
    }
    serial::event(
        "teardown",
        format_args!(
            ",\"transport_reset_on_drop\":true,\"queue_unset_pci_semantics\":\"spec-no-op-before-reset\",\"allocations\":{},\"dma_allocations\":{},\"dma_deallocations\":{},\"shares\":{},\"unshares\":{},\"mmio_maps\":{},\"bounds_violations\":{}",
            counters.allocations,
            counters.dma_allocations,
            counters.dma_deallocations,
            counters.shares,
            counters.unshares,
            counters.mmio_maps,
            counters.bounds_violations,
        ),
    );
    serial::event(
        "pass",
        format_args!(
            ",\"frames\":{},\"input_events\":{},\"interrupts_observed\":{},\"duplicate_isr_ack_empty\":{},\"polling_without_cpu_irqs\":true,\"capture_ack\":true",
            frame_count, input_count, interrupt_count, duplicate_ack_empty
        ),
    );
    Ok(())
}

fn validate_platform(platform: &Platform) -> Result<(), &'static str> {
    if !platform.pci_dma_coherent {
        return Err("PCI host is not dma-coherent");
    }
    if platform.pci_bus_start != 0 {
        return Err("probe requires root PCI bus zero");
    }
    if !hal::configure(
        platform.ram_start,
        platform.ram_size,
        platform.pci_mmio_base,
        platform.pci_mmio_size,
    ) {
        return Err("HAL ranges are invalid");
    }
    let (heap_start, heap_size) = hal::heap_range();
    serial::event(
        "dma_contract",
        format_args!(
            ",\"mapping\":\"identity\",\"cache_policy\":\"DTB dma-coherent required\",\"access_platform_negotiated\":false,\"barriers\":\"virtio-drivers SeqCst fence plus Acquire/Release rings\",\"heap_start\":{},\"heap_size\":{}",
            heap_start, heap_size
        ),
    );
    Ok(())
}

fn find_devices<C: virtio_drivers::transport::pci::bus::ConfigurationAccess>(
    root: &PciRoot<C>,
    bus: u8,
) -> Result<(DeviceFunction, DeviceFunction), &'static str> {
    let mut gpu = None;
    let mut input = None;
    let mut functions = 0u32;
    for (function, info) in root.enumerate_bus(bus) {
        functions += 1;
        match virtio_device_type(&info) {
            Some(DeviceType::GPU) => gpu = Some(function),
            Some(DeviceType::Input) => input = Some(function),
            _ => {}
        }
    }
    let gpu = gpu.ok_or("virtio-gpu-pci not found")?;
    let input = input.ok_or("virtio-input PCI pointer not found")?;
    serial::event(
        "pci_devices",
        format_args!(
            ",\"functions\":{},\"gpu_bdf\":\"{:02x}:{:02x}.{}\",\"input_bdf\":\"{:02x}:{:02x}.{}\"",
            functions, gpu.bus, gpu.device, gpu.function, input.bus, input.device, input.function,
        ),
    );
    Ok((gpu, input))
}

fn allocate_bars<C: virtio_drivers::transport::pci::bus::ConfigurationAccess>(
    root: &mut PciRoot<C>,
    function: DeviceFunction,
    next: &mut u64,
    end: u64,
) -> Result<(), &'static str> {
    let bars = root.bars(function).map_err(|_| "read PCI BAR geometry")?;
    for (index, bar) in bars.iter().enumerate() {
        let Some(BarInfo::Memory {
            address_type, size, ..
        }) = bar
        else {
            continue;
        };
        if *size == 0 || !size.is_power_of_two() {
            return Err("invalid PCI BAR size");
        }
        *next = align_up(*next, *size).ok_or("PCI BAR alignment overflow")?;
        let bar_end = next.checked_add(*size).ok_or("PCI BAR overflow")?;
        if bar_end > end || *next > u64::from(u32::MAX) {
            return Err("PCI BAR does not fit discovered 32-bit MMIO window");
        }
        match address_type {
            MemoryBarType::Width64 => root.set_bar_64(function, index as u8, *next),
            MemoryBarType::Width32 => root.set_bar_32(function, index as u8, *next as u32),
            MemoryBarType::Below1MiB => return Err("unsupported below-1MiB PCI BAR"),
        }
        serial::event(
            "pci_bar",
            format_args!(
                ",\"bus\":{},\"device\":{},\"function\":{},\"bar\":{},\"address\":{},\"size\":{},\"source\":\"DTB ranges plus ECAM BAR sizing\"",
                function.bus, function.device, function.function, index, *next, size
            ),
        );
        *next = bar_end;
    }
    root.set_command(function, Command::MEMORY_SPACE | Command::BUS_MASTER);
    Ok(())
}

fn pci_interrupt_pin(ecam_base: usize, function: DeviceFunction) -> Result<u8, &'static str> {
    let offset = usize::try_from(Cam::Ecam.cam_offset(function, 0x3c))
        .map_err(|_| "PCI ECAM offset exceeds usize")?;
    let address = ecam_base
        .checked_add(offset)
        .ok_or("PCI ECAM interrupt-pin address overflow")?;
    // SAFETY: The DTB-discovered ECAM window covers this checked BDF offset. The probe is
    // single-core and the read does not overlap a concurrent configuration transaction.
    let line_and_pin = unsafe { core::ptr::read_volatile(address as *const u32) };
    let pin = ((line_and_pin >> 8) & 0xff) as u8;
    if !(1..=4).contains(&pin) {
        return Err("PCI function has no valid INTx pin");
    }
    Ok(pin)
}

fn audit_transport<C: virtio_drivers::transport::pci::bus::ConfigurationAccess>(
    root: &mut PciRoot<C>,
    function: DeviceFunction,
    kind: &'static str,
    exercise_queue: bool,
) -> Result<(), &'static str> {
    let mut transport =
        PciTransport::new::<ProbeHal, _>(root, function).map_err(|_| "create audit transport")?;
    reset(&mut transport)?;
    serial::event(
        "debug",
        format_args!(",\"stage\":\"transport_reset\",\"device\":\"{}\"", kind),
    );
    transport.set_status(DeviceStatus::ACKNOWLEDGE | DeviceStatus::DRIVER);
    let offered = transport.read_device_features();
    if offered & VERSION_1 == 0 {
        return Err("virtio device does not offer VERSION_1");
    }
    let selected = VERSION_1;
    if selected & ACCESS_PLATFORM != 0 {
        return Err("ACCESS_PLATFORM must not be selected");
    }
    transport.write_driver_features(selected);
    let feature_status =
        DeviceStatus::ACKNOWLEDGE | DeviceStatus::DRIVER | DeviceStatus::FEATURES_OK;
    transport.set_status(feature_status);
    if !transport.get_status().contains(DeviceStatus::FEATURES_OK) {
        return Err("device rejected FEATURES_OK");
    }
    let queue0 = transport.max_queue_size(0);
    let queue1 = transport.max_queue_size(1);
    if queue0 < 2 || queue1 < 2 {
        return Err("virtio queue is smaller than probe contract");
    }
    serial::event(
        "transport_audit",
        format_args!(
            ",\"device\":\"{}\",\"offered_features\":{},\"selected_features\":{},\"version_1_offered\":true,\"features_ok_readback\":true,\"access_platform_selected\":false,\"queue0_max\":{},\"queue1_max\":{}",
            kind, offered, selected, queue0, queue1
        ),
    );

    transport.set_status(feature_status | DeviceStatus::FAILED);
    if !transport.get_status().contains(DeviceStatus::FAILED) {
        return Err("FAILED status did not read back");
    }
    reset(&mut transport)?;
    serial::event(
        "reset_recovery",
        format_args!(
            ",\"device\":\"{}\",\"failed_status_observed\":true,\"reset_to_zero\":true,\"generation\":1",
            kind
        ),
    );

    if exercise_queue {
        initialize_version_1(&mut transport)?;
        let mut queue = VirtQueue::<ProbeHal, 2>::new(&mut transport, 0, false, false)
            .map_err(|_| "create queue-exhaustion queue")?;
        let first = [0x11u8; 4];
        let second = [0x22u8; 4];
        let third = [0x33u8; 4];
        // SAFETY: The buffers remain live and untouched until the device reset immediately below.
        unsafe { queue.add(&[&first], &mut []) }.map_err(|_| "first queue add failed")?;
        // SAFETY: Same lifetime and reset reasoning as above.
        unsafe { queue.add(&[&second], &mut []) }.map_err(|_| "second queue add failed")?;
        // SAFETY: The call must fail before publishing `third`; all prior chains are invalidated by
        // the reset below without notifying the device.
        let exhausted = unsafe { queue.add(&[&third], &mut []) } == Err(Error::QueueFull);
        reset(&mut transport)?;
        drop(queue);
        if !exhausted {
            return Err("queue exhaustion did not return QueueFull");
        }
        serial::event(
            "queue_exhaustion",
            format_args!(
                ",\"device\":\"gpu\",\"queue_size\":2,\"accepted\":2,\"third_error\":\"QueueFull\",\"recovered_by_reset\":true"
            ),
        );

        initialize_version_1(&mut transport)?;
        let mut queue = VirtQueue::<ProbeHal, 2>::new(&mut transport, 0, false, false)
            .map_err(|_| "create malformed-command queue")?;
        let request = [0u8; 4];
        let mut guarded = [0xa5u8; 64];
        let output = &mut guarded[16..48];
        // SAFETY: The request and guarded output remain live and untouched until pop or reset.
        let token = unsafe { queue.add(&[&request], &mut [output]) }
            .map_err(|_| "submit malformed GPU command")?;
        transport.notify(0);
        let mut completed = false;
        for _ in 0..AUDIT_SPINS {
            if queue.can_pop() {
                completed = true;
                break;
            }
            spin_loop();
        }
        let mut response_length = 0u32;
        if completed {
            let output = &mut guarded[16..48];
            // SAFETY: This is the same request/output chain and token submitted above, and the used
            // ring indicates completion.
            response_length = unsafe { queue.pop_used(token, &[&request], &mut [output]) }
                .map_err(|_| "pop malformed GPU response")?;
        }
        reset(&mut transport)?;
        drop(queue);
        let canaries_ok = guarded[..16].iter().all(|byte| *byte == 0xa5)
            && guarded[48..].iter().all(|byte| *byte == 0xa5);
        if !completed || response_length > 32 || !canaries_ok {
            return Err("malformed GPU command bounds contract failed");
        }
        serial::event(
            "malformed_command",
            format_args!(
                ",\"request_length\":4,\"descriptor_output_length\":32,\"completed_before_timeout\":true,\"response_length\":{},\"canaries_ok\":true,\"timeout_spins\":{},\"recovered_by_reset\":true",
                response_length, AUDIT_SPINS
            ),
        );
    }
    reset(&mut transport)?;
    Ok(())
}

fn initialize_version_1(transport: &mut impl Transport) -> Result<(), &'static str> {
    reset(transport)?;
    transport.set_status(DeviceStatus::ACKNOWLEDGE | DeviceStatus::DRIVER);
    transport.write_driver_features(VERSION_1);
    let status = DeviceStatus::ACKNOWLEDGE | DeviceStatus::DRIVER | DeviceStatus::FEATURES_OK;
    transport.set_status(status);
    if !transport.get_status().contains(DeviceStatus::FEATURES_OK) {
        return Err("queue test FEATURES_OK rejected");
    }
    transport.set_status(status | DeviceStatus::DRIVER_OK);
    Ok(())
}

fn reset(transport: &mut impl Transport) -> Result<(), &'static str> {
    transport.set_status(DeviceStatus::empty());
    for i in 0..AUDIT_SPINS {
        let status = transport.get_status();
        if i == 0 {
            serial::event("debug_reset", format_args!(",\"status\":{}", status.bits()));
        }
        if status.is_empty() {
            return Ok(());
        }
        spin_loop();
    }
    Err("virtio reset timeout")
}

fn align_up(value: u64, alignment: u64) -> Option<u64> {
    value
        .checked_add(alignment - 1)
        .map(|value| value & !(alignment - 1))
}

fn bitmap_has(bitmap: &[u8], bit: u16) -> bool {
    bitmap
        .get(usize::from(bit / 8))
        .is_some_and(|byte| byte & (1 << (bit % 8)) != 0)
}

fn scale_axis(value: u32, min: u32, max: u32, dimension: u32) -> u32 {
    let value = value.clamp(min, max) - min;
    ((u64::from(value) * u64::from(dimension - 1)) / u64::from(max - min)) as u32
}

fn draw_frame(
    framebuffer: &mut [u8],
    width: u32,
    height: u32,
    frame: u32,
    cursor_x: u32,
    cursor_y: u32,
    pressed: bool,
) {
    for y in 0..height {
        for x in 0..width {
            let stripe = ((x / 32) + (y / 24) + frame) & 1;
            let mut color = if stripe == 0 {
                [0x30, 0x18, 0x10, 0xff]
            } else {
                [0x58, 0x28, 0x18, 0xff]
            };
            if x < 64 && y < 64 {
                color = [0xff, 0x00, 0xff, 0xff];
            } else if x >= width - 64 && y < 64 {
                color = [0xff, 0xff, 0x00, 0xff];
            } else if x < 64 && y >= height - 64 {
                color = [0x00, 0xff, 0xff, 0xff];
            } else if x >= width - 64 && y >= height - 64 {
                color = [0xff, 0xff, 0xff, 0xff];
            } else if x >= width / 2 - 80
                && x < width / 2 + 80
                && y >= height / 2 - 40
                && y < height / 2 + 40
            {
                color = if frame == 1 {
                    [0xff, 0x40, 0x20, 0xff]
                } else {
                    [0x20, 0xd0, 0x30, 0xff]
                };
            }
            put_pixel(framebuffer, width, x, y, color);
        }
    }
    if frame == 2 {
        for y in 0..24 {
            for x in 0..12 {
                if x <= y / 2 + 1 && cursor_x + x < width && cursor_y + y < height {
                    let border = x == 0 || x == y / 2 + 1 || y == 23;
                    let color = if border || !pressed {
                        [0xff, 0xff, 0xff, 0xff]
                    } else {
                        [0x20, 0x20, 0xff, 0xff]
                    };
                    put_pixel(framebuffer, width, cursor_x + x, cursor_y + y, color);
                }
            }
        }
    }
}

fn draw_cursor(cursor: &mut [u8; 64 * 64 * 4]) {
    for y in 0..64usize {
        for x in 0..64usize {
            let offset = (y * 64 + x) * 4;
            let visible = x <= y / 2 + 2 && y < 48;
            cursor[offset..offset + 4].copy_from_slice(if visible {
                &[0xff, 0xff, 0xff, 0xff]
            } else {
                &[0, 0, 0, 0]
            });
        }
    }
}

fn put_pixel(framebuffer: &mut [u8], width: u32, x: u32, y: u32, color: [u8; 4]) {
    let offset = ((y * width + x) * 4) as usize;
    framebuffer[offset..offset + 4].copy_from_slice(&color);
}

fn finish() -> ! {
    loop {
        // SAFETY: Event delivery is deliberately polling-only, so sleeping is not used. Keeping
        // CPU IRQs masked is part of the interrupt-loss acceptance check.
        spin_loop();
    }
}

#[panic_handler]
fn panic(info: &core::panic::PanicInfo<'_>) -> ! {
    serial::panic_line(info);
    finish()
}
