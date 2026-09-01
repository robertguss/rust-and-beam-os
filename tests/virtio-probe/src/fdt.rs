use core::{ptr, slice, str};

const FDT_MAGIC: u32 = 0xd00d_feed;
const FDT_BEGIN_NODE: u32 = 1;
const FDT_END_NODE: u32 = 2;
const FDT_PROP: u32 = 3;
const FDT_NOP: u32 = 4;
const FDT_END: u32 = 9;
const MAX_DTB_SIZE: usize = 2 * 1024 * 1024;
const MAX_DEPTH: usize = 16;
const MAX_PCI_INTERRUPT_ROUTES: usize = 16;

#[derive(Clone, Copy, Debug, Default)]
pub struct PciInterruptRoute {
    pub child_address: u32,
    pub pin: u8,
    pub gic_irq: u32,
    pub flags: u32,
}

#[derive(Clone, Copy, Debug)]
pub struct Platform {
    pub dtb_size: usize,
    pub uart_base: usize,
    pub uart_size: usize,
    pub ram_start: usize,
    pub ram_size: usize,
    pub pci_ecam_base: usize,
    pub pci_ecam_size: usize,
    pub pci_mmio_base: u64,
    pub pci_mmio_size: u64,
    pub pci_bus_start: u8,
    pub pci_bus_end: u8,
    pub pci_dma_coherent: bool,
    pub pci_interrupt_parent: u32,
    pub pci_interrupt_address_mask: u32,
    pub pci_interrupt_routes: [PciInterruptRoute; MAX_PCI_INTERRUPT_ROUTES],
    pub pci_interrupt_route_count: usize,
}

impl Platform {
    pub fn pci_interrupt_route(
        &self,
        bus: u8,
        device: u8,
        function: u8,
        pin: u8,
    ) -> Option<PciInterruptRoute> {
        let child_address =
            ((u32::from(bus) << 16) | (u32::from(device) << 11) | (u32::from(function) << 8))
                & self.pci_interrupt_address_mask;
        self.pci_interrupt_routes[..self.pci_interrupt_route_count]
            .iter()
            .copied()
            .find(|route| route.child_address == child_address && route.pin == pin)
    }
}

#[derive(Clone, Copy, Debug)]
pub struct FdtError(pub &'static str);

#[derive(Clone, Copy, Default)]
struct Node<'a> {
    uart: bool,
    pci: bool,
    memory: bool,
    dma_coherent: bool,
    address_cells: Option<usize>,
    size_cells: Option<usize>,
    reg: Option<&'a [u8]>,
    ranges: Option<&'a [u8]>,
    bus_range: Option<&'a [u8]>,
    interrupt_map: Option<&'a [u8]>,
    interrupt_map_mask: Option<&'a [u8]>,
}

pub unsafe fn discover(dtb_address: usize) -> Result<Platform, FdtError> {
    if dtb_address == 0 {
        return Err(FdtError("null DTB address"));
    }

    // SAFETY: QEMU's direct Linux boot contract passes a readable FDT pointer in x0.
    let magic = unsafe { read_be_u32_ptr(dtb_address as *const u8, 0) };
    if magic != FDT_MAGIC {
        return Err(FdtError("invalid DTB magic"));
    }
    // SAFETY: The validated FDT header contains at least the standard ten words.
    let total_size = unsafe { read_be_u32_ptr(dtb_address as *const u8, 4) } as usize;
    if !(40..=MAX_DTB_SIZE).contains(&total_size) {
        return Err(FdtError("invalid DTB size"));
    }
    // SAFETY: `total_size` is bounded and the firmware-owned blob remains live for the probe.
    let bytes = unsafe { slice::from_raw_parts(dtb_address as *const u8, total_size) };

    let structure_offset = be_u32(bytes, 8)? as usize;
    let strings_offset = be_u32(bytes, 12)? as usize;
    let strings_size = be_u32(bytes, 32)? as usize;
    let structure_size = be_u32(bytes, 36)? as usize;
    let structure = checked_block(bytes, structure_offset, structure_size)?;
    let strings = checked_block(bytes, strings_offset, strings_size)?;

    let mut nodes = [Node::default(); MAX_DEPTH];
    let mut depth = 0usize;
    let mut offset = 0usize;
    let mut root_address_cells = None;
    let mut root_size_cells = None;
    let mut uart = None;
    let mut memory = None;
    let mut pci = None;

    loop {
        let token = take_u32(structure, &mut offset)?;
        match token {
            FDT_BEGIN_NODE => {
                if depth >= MAX_DEPTH {
                    return Err(FdtError("DTB nesting exceeds probe bound"));
                }
                let name = take_cstr(structure, &mut offset)?;
                nodes[depth] = Node {
                    memory: name == "memory" || name.starts_with("memory@"),
                    ..Node::default()
                };
                depth += 1;
            }
            FDT_END_NODE => {
                if depth == 0 {
                    return Err(FdtError("unbalanced DTB node"));
                }
                depth -= 1;
                let node = nodes[depth];
                if depth == 0 {
                    root_address_cells = node.address_cells;
                    root_size_cells = node.size_cells;
                }
                if node.uart {
                    uart = Some(node);
                }
                if node.memory {
                    memory = Some(node);
                }
                if node.pci {
                    pci = Some(node);
                }
            }
            FDT_PROP => {
                if depth == 0 {
                    return Err(FdtError("DTB property outside node"));
                }
                let length = take_u32(structure, &mut offset)? as usize;
                let name_offset = take_u32(structure, &mut offset)? as usize;
                let end = offset
                    .checked_add(length)
                    .ok_or(FdtError("DTB property overflow"))?;
                let value = structure
                    .get(offset..end)
                    .ok_or(FdtError("truncated DTB property"))?;
                offset = align4(end)?;
                let name = string_at(strings, name_offset)?;
                let node = &mut nodes[depth - 1];
                match name {
                    "compatible" => {
                        node.uart |= string_list_contains(value, "arm,pl011")?;
                        node.pci |= string_list_contains(value, "pci-host-ecam-generic")?;
                    }
                    "device_type" => node.memory |= cstr(value)? == "memory",
                    "reg" => node.reg = Some(value),
                    "ranges" => node.ranges = Some(value),
                    "bus-range" => node.bus_range = Some(value),
                    "interrupt-map" => node.interrupt_map = Some(value),
                    "interrupt-map-mask" => node.interrupt_map_mask = Some(value),
                    "dma-coherent" => node.dma_coherent = true,
                    "#address-cells" => node.address_cells = Some(single_cell(value)? as usize),
                    "#size-cells" => node.size_cells = Some(single_cell(value)? as usize),
                    _ => {}
                }
            }
            FDT_NOP => {}
            FDT_END => break,
            _ => return Err(FdtError("unknown DTB structure token")),
        }
    }

    let address_cells = root_address_cells.ok_or(FdtError("missing root address cells"))?;
    let size_cells = root_size_cells.ok_or(FdtError("missing root size cells"))?;
    if address_cells != 2 || size_cells != 2 {
        return Err(FdtError("unsupported root cell geometry"));
    }

    let uart = uart.ok_or(FdtError("PL011 not found in DTB"))?;
    let (uart_base, uart_size) = parse_reg(
        uart.reg.ok_or(FdtError("PL011 has no reg property"))?,
        address_cells,
        size_cells,
    )?;
    let memory = memory.ok_or(FdtError("memory node not found in DTB"))?;
    let (ram_start, ram_size) = parse_reg(
        memory
            .reg
            .ok_or(FdtError("memory node has no reg property"))?,
        address_cells,
        size_cells,
    )?;
    let pci = pci.ok_or(FdtError("PCI ECAM node not found in DTB"))?;
    let (pci_ecam_base, pci_ecam_size) = parse_reg(
        pci.reg
            .ok_or(FdtError("PCI ECAM node has no reg property"))?,
        address_cells,
        size_cells,
    )?;
    if pci_ecam_size < 0x1000_0000 {
        return Err(FdtError("PCI ECAM window is smaller than 256 MiB"));
    }
    if pci.address_cells != Some(3) || pci.size_cells != Some(2) {
        return Err(FdtError("unsupported PCI cell geometry"));
    }
    let (pci_mmio_base, pci_mmio_size) = parse_pci_mmio_range(
        pci.ranges
            .ok_or(FdtError("PCI node has no ranges property"))?,
        address_cells,
    )?;
    let (pci_bus_start, pci_bus_end) = parse_bus_range(pci.bus_range)?;
    let (
        pci_interrupt_parent,
        pci_interrupt_address_mask,
        pci_interrupt_routes,
        pci_interrupt_route_count,
    ) = parse_pci_interrupt_map(
        pci.interrupt_map
            .ok_or(FdtError("PCI node has no interrupt-map property"))?,
        pci.interrupt_map_mask
            .ok_or(FdtError("PCI node has no interrupt-map-mask property"))?,
    )?;

    Ok(Platform {
        dtb_size: total_size,
        uart_base: to_usize(uart_base)?,
        uart_size: to_usize(uart_size)?,
        ram_start: to_usize(ram_start)?,
        ram_size: to_usize(ram_size)?,
        pci_ecam_base: to_usize(pci_ecam_base)?,
        pci_ecam_size: to_usize(pci_ecam_size)?,
        pci_mmio_base,
        pci_mmio_size,
        pci_bus_start,
        pci_bus_end,
        pci_dma_coherent: pci.dma_coherent,
        pci_interrupt_parent,
        pci_interrupt_address_mask,
        pci_interrupt_routes,
        pci_interrupt_route_count,
    })
}

fn checked_block(bytes: &[u8], offset: usize, size: usize) -> Result<&[u8], FdtError> {
    let end = offset
        .checked_add(size)
        .ok_or(FdtError("DTB block overflow"))?;
    bytes
        .get(offset..end)
        .ok_or(FdtError("DTB block is out of bounds"))
}

fn be_u32(bytes: &[u8], offset: usize) -> Result<u32, FdtError> {
    let raw: [u8; 4] = bytes
        .get(offset..offset + 4)
        .ok_or(FdtError("truncated DTB word"))?
        .try_into()
        .map_err(|_| FdtError("truncated DTB word"))?;
    Ok(u32::from_be_bytes(raw))
}

unsafe fn read_be_u32_ptr(base: *const u8, offset: usize) -> u32 {
    // SAFETY: The caller provides a readable firmware FDT header pointer.
    u32::from_be(unsafe { ptr::read_unaligned(base.add(offset).cast::<u32>()) })
}

fn take_u32(bytes: &[u8], offset: &mut usize) -> Result<u32, FdtError> {
    let value = be_u32(bytes, *offset)?;
    *offset += 4;
    Ok(value)
}

fn align4(value: usize) -> Result<usize, FdtError> {
    value
        .checked_add(3)
        .map(|value| value & !3)
        .ok_or(FdtError("DTB alignment overflow"))
}

fn take_cstr<'a>(bytes: &'a [u8], offset: &mut usize) -> Result<&'a str, FdtError> {
    let tail = bytes
        .get(*offset..)
        .ok_or(FdtError("truncated DTB string"))?;
    let end = tail
        .iter()
        .position(|byte| *byte == 0)
        .ok_or(FdtError("unterminated DTB string"))?;
    let value = str::from_utf8(&tail[..end]).map_err(|_| FdtError("non-UTF-8 DTB string"))?;
    *offset = align4(*offset + end + 1)?;
    Ok(value)
}

fn cstr(bytes: &[u8]) -> Result<&str, FdtError> {
    let end = bytes
        .iter()
        .position(|byte| *byte == 0)
        .unwrap_or(bytes.len());
    str::from_utf8(&bytes[..end]).map_err(|_| FdtError("non-UTF-8 DTB property"))
}

fn string_at(strings: &[u8], offset: usize) -> Result<&str, FdtError> {
    cstr(
        strings
            .get(offset..)
            .ok_or(FdtError("DTB string offset out of bounds"))?,
    )
}

fn string_list_contains(mut bytes: &[u8], needle: &str) -> Result<bool, FdtError> {
    while !bytes.is_empty() {
        let end = bytes
            .iter()
            .position(|byte| *byte == 0)
            .ok_or(FdtError("unterminated DTB string list"))?;
        let value =
            str::from_utf8(&bytes[..end]).map_err(|_| FdtError("non-UTF-8 DTB string list"))?;
        if value == needle {
            return Ok(true);
        }
        bytes = &bytes[end + 1..];
    }
    Ok(false)
}

fn single_cell(bytes: &[u8]) -> Result<u32, FdtError> {
    if bytes.len() != 4 {
        return Err(FdtError("DTB cell property has wrong size"));
    }
    be_u32(bytes, 0)
}

fn read_cells(bytes: &[u8], start_cell: usize, cells: usize) -> Result<u64, FdtError> {
    if cells > 2 {
        return Err(FdtError("DTB value exceeds 64 bits"));
    }
    let mut value = 0u64;
    for index in 0..cells {
        value = (value << 32) | u64::from(be_u32(bytes, (start_cell + index) * 4)?);
    }
    Ok(value)
}

fn parse_reg(
    bytes: &[u8],
    address_cells: usize,
    size_cells: usize,
) -> Result<(u64, u64), FdtError> {
    let entry_cells = address_cells + size_cells;
    if entry_cells == 0 || bytes.len() < entry_cells * 4 {
        return Err(FdtError("truncated DTB reg property"));
    }
    Ok((
        read_cells(bytes, 0, address_cells)?,
        read_cells(bytes, address_cells, size_cells)?,
    ))
}

fn parse_pci_mmio_range(bytes: &[u8], parent_address_cells: usize) -> Result<(u64, u64), FdtError> {
    const CHILD_ADDRESS_CELLS: usize = 3;
    const CHILD_SIZE_CELLS: usize = 2;
    const PCI_MEMORY_32: u32 = 0x0200_0000;
    let entry_cells = CHILD_ADDRESS_CELLS + parent_address_cells + CHILD_SIZE_CELLS;
    let entry_size = entry_cells * 4;
    if entry_size == 0 || bytes.len() % entry_size != 0 {
        return Err(FdtError("malformed PCI ranges property"));
    }
    for entry in bytes.chunks_exact(entry_size) {
        let flags = be_u32(entry, 0)? & 0x0300_0000;
        if flags == PCI_MEMORY_32 {
            let parent = read_cells(entry, CHILD_ADDRESS_CELLS, parent_address_cells)?;
            let size = read_cells(
                entry,
                CHILD_ADDRESS_CELLS + parent_address_cells,
                CHILD_SIZE_CELLS,
            )?;
            if size == 0 || parent.checked_add(size).is_none() {
                return Err(FdtError("invalid PCI MMIO range"));
            }
            return Ok((parent, size));
        }
    }
    Err(FdtError("32-bit PCI memory range not found"))
}

fn parse_bus_range(bytes: Option<&[u8]>) -> Result<(u8, u8), FdtError> {
    let Some(bytes) = bytes else {
        return Ok((0, 255));
    };
    if bytes.len() != 8 {
        return Err(FdtError("malformed PCI bus-range property"));
    }
    let start = be_u32(bytes, 0)?;
    let end = be_u32(bytes, 4)?;
    if start > end || end > u32::from(u8::MAX) {
        return Err(FdtError("invalid PCI bus range"));
    }
    Ok((start as u8, end as u8))
}

fn parse_pci_interrupt_map(
    bytes: &[u8],
    mask: &[u8],
) -> Result<
    (
        u32,
        u32,
        [PciInterruptRoute; MAX_PCI_INTERRUPT_ROUTES],
        usize,
    ),
    FdtError,
> {
    const CHILD_CELLS: usize = 4;
    const PARENT_HANDLE_CELLS: usize = 1;
    const GIC_ADDRESS_CELLS: usize = 2;
    const GIC_INTERRUPT_CELLS: usize = 3;
    const ENTRY_CELLS: usize =
        CHILD_CELLS + PARENT_HANDLE_CELLS + GIC_ADDRESS_CELLS + GIC_INTERRUPT_CELLS;
    const GIC_SPI: u32 = 0;
    const GIC_SPI_BASE: u32 = 32;

    if mask.len() != CHILD_CELLS * 4
        || be_u32(mask, 4)? != 0
        || be_u32(mask, 8)? != 0
        || be_u32(mask, 12)? != 7
    {
        return Err(FdtError("unsupported PCI interrupt-map-mask"));
    }
    let address_mask = be_u32(mask, 0)?;
    let entry_size = ENTRY_CELLS * 4;
    if bytes.is_empty()
        || bytes.len() % entry_size != 0
        || bytes.len() / entry_size > MAX_PCI_INTERRUPT_ROUTES
    {
        return Err(FdtError("malformed PCI interrupt-map"));
    }

    let mut routes = [PciInterruptRoute::default(); MAX_PCI_INTERRUPT_ROUTES];
    let mut count = 0usize;
    let mut interrupt_parent = None;
    for entry in bytes.chunks_exact(entry_size) {
        let parent = be_u32(entry, 16)?;
        if interrupt_parent
            .replace(parent)
            .is_some_and(|value| value != parent)
        {
            return Err(FdtError("PCI interrupt-map has multiple parents"));
        }
        if be_u32(entry, 20)? != 0 || be_u32(entry, 24)? != 0 || be_u32(entry, 28)? != GIC_SPI {
            return Err(FdtError("unsupported PCI interrupt parent geometry"));
        }
        let spi = be_u32(entry, 32)?;
        let flags = be_u32(entry, 36)?;
        let pin = be_u32(entry, 12)?;
        if !(1..=4).contains(&pin) || spi.checked_add(GIC_SPI_BASE).is_none() {
            return Err(FdtError("invalid PCI interrupt route"));
        }
        routes[count] = PciInterruptRoute {
            child_address: be_u32(entry, 0)? & address_mask,
            pin: pin as u8,
            gic_irq: spi + GIC_SPI_BASE,
            flags,
        };
        count += 1;
    }
    Ok((
        interrupt_parent.ok_or(FdtError("empty PCI interrupt-map"))?,
        address_mask,
        routes,
        count,
    ))
}

fn to_usize(value: u64) -> Result<usize, FdtError> {
    usize::try_from(value).map_err(|_| FdtError("DTB address does not fit usize"))
}
