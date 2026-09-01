use core::{
    alloc::{GlobalAlloc, Layout},
    ptr::{self, NonNull},
    sync::atomic::{AtomicUsize, Ordering},
};
use virtio_drivers::{BufferDirection, Hal, PAGE_SIZE, PhysAddr};

const HEAP_SIZE: usize = 16 * 1024 * 1024;

#[repr(C, align(4096))]
struct Heap([u8; HEAP_SIZE]);

static mut HEAP: Heap = Heap([0; HEAP_SIZE]);
static NEXT: AtomicUsize = AtomicUsize::new(0);
static RAM_START: AtomicUsize = AtomicUsize::new(0);
static RAM_END: AtomicUsize = AtomicUsize::new(0);
static MMIO_START: AtomicUsize = AtomicUsize::new(0);
static MMIO_END: AtomicUsize = AtomicUsize::new(0);
static ALLOCATION_COUNT: AtomicUsize = AtomicUsize::new(0);
static DMA_ALLOCATION_COUNT: AtomicUsize = AtomicUsize::new(0);
static DMA_DEALLOCATION_COUNT: AtomicUsize = AtomicUsize::new(0);
static SHARE_COUNT: AtomicUsize = AtomicUsize::new(0);
static UNSHARE_COUNT: AtomicUsize = AtomicUsize::new(0);
static MMIO_MAP_COUNT: AtomicUsize = AtomicUsize::new(0);
static BOUNDS_VIOLATIONS: AtomicUsize = AtomicUsize::new(0);

pub struct ProbeAllocator;
pub struct ProbeHal;

#[derive(Clone, Copy, Debug)]
pub struct Counters {
    pub allocations: usize,
    pub dma_allocations: usize,
    pub dma_deallocations: usize,
    pub shares: usize,
    pub unshares: usize,
    pub mmio_maps: usize,
    pub bounds_violations: usize,
}

pub fn configure(ram_start: usize, ram_size: usize, mmio_start: u64, mmio_size: u64) -> bool {
    let Some(ram_end) = ram_start.checked_add(ram_size) else {
        return false;
    };
    let Ok(mmio_start) = usize::try_from(mmio_start) else {
        return false;
    };
    let Ok(mmio_size) = usize::try_from(mmio_size) else {
        return false;
    };
    let Some(mmio_end) = mmio_start.checked_add(mmio_size) else {
        return false;
    };
    let heap_start = heap_start();
    let Some(heap_end) = heap_start.checked_add(HEAP_SIZE) else {
        return false;
    };
    if !range_inside(heap_start, HEAP_SIZE, ram_start, ram_end) {
        return false;
    }

    RAM_START.store(ram_start, Ordering::Release);
    RAM_END.store(ram_end, Ordering::Release);
    MMIO_START.store(mmio_start, Ordering::Release);
    MMIO_END.store(mmio_end, Ordering::Release);
    heap_end <= ram_end
}

pub fn heap_range() -> (usize, usize) {
    (heap_start(), HEAP_SIZE)
}

pub fn counters() -> Counters {
    Counters {
        allocations: ALLOCATION_COUNT.load(Ordering::Relaxed),
        dma_allocations: DMA_ALLOCATION_COUNT.load(Ordering::Relaxed),
        dma_deallocations: DMA_DEALLOCATION_COUNT.load(Ordering::Relaxed),
        shares: SHARE_COUNT.load(Ordering::Relaxed),
        unshares: UNSHARE_COUNT.load(Ordering::Relaxed),
        mmio_maps: MMIO_MAP_COUNT.load(Ordering::Relaxed),
        bounds_violations: BOUNDS_VIOLATIONS.load(Ordering::Relaxed),
    }
}

unsafe impl GlobalAlloc for ProbeAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        allocate(layout.size(), layout.align()).unwrap_or(ptr::null_mut())
    }

    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // The probe is a one-shot process. Keeping allocations until QEMU exits avoids a second
        // allocator and still satisfies the driver's non-aliasing lifetime contract.
    }
}

// SAFETY: The probe has an identity-mapped, single-core address space. Every returned DMA and
// shared range is checked against DTB-discovered RAM; every MMIO mapping is checked against the
// DTB-discovered PCI memory window. QEMU advertises `dma-coherent`, which the caller checks before
// constructing a driver.
unsafe impl Hal for ProbeHal {
    fn dma_alloc(pages: usize, _direction: BufferDirection) -> (PhysAddr, NonNull<u8>) {
        let Some(size) = pages.checked_mul(PAGE_SIZE) else {
            BOUNDS_VIOLATIONS.fetch_add(1, Ordering::Relaxed);
            return (0, NonNull::dangling());
        };
        let Some(address) = allocate(size, PAGE_SIZE) else {
            return (0, NonNull::dangling());
        };
        if !inside_ram(address as usize, size) {
            BOUNDS_VIOLATIONS.fetch_add(1, Ordering::Relaxed);
            return (0, NonNull::dangling());
        }
        DMA_ALLOCATION_COUNT.fetch_add(1, Ordering::Relaxed);
        (address as u64, NonNull::new(address).unwrap())
    }

    unsafe fn dma_dealloc(_paddr: PhysAddr, _vaddr: NonNull<u8>, _pages: usize) -> i32 {
        DMA_DEALLOCATION_COUNT.fetch_add(1, Ordering::Relaxed);
        0
    }

    unsafe fn mmio_phys_to_virt(paddr: PhysAddr, size: usize) -> NonNull<u8> {
        let address = usize::try_from(paddr).expect("PCI MMIO address exceeds usize");
        let start = MMIO_START.load(Ordering::Acquire);
        let end = MMIO_END.load(Ordering::Acquire);
        if !range_inside(address, size, start, end) {
            BOUNDS_VIOLATIONS.fetch_add(1, Ordering::Relaxed);
            panic!("PCI MMIO mapping outside DTB window");
        }
        MMIO_MAP_COUNT.fetch_add(1, Ordering::Relaxed);
        NonNull::new(address as *mut u8).unwrap()
    }

    unsafe fn share(buffer: NonNull<[u8]>, _direction: BufferDirection) -> PhysAddr {
        let address = buffer.as_ptr() as *mut u8 as usize;
        let size = buffer.len();
        if !inside_ram(address, size) {
            BOUNDS_VIOLATIONS.fetch_add(1, Ordering::Relaxed);
            return 0;
        }
        SHARE_COUNT.fetch_add(1, Ordering::Relaxed);
        address as u64
    }

    unsafe fn unshare(_paddr: PhysAddr, buffer: NonNull<[u8]>, _direction: BufferDirection) {
        let address = buffer.as_ptr() as *mut u8 as usize;
        if !inside_ram(address, buffer.len()) {
            BOUNDS_VIOLATIONS.fetch_add(1, Ordering::Relaxed);
        }
        UNSHARE_COUNT.fetch_add(1, Ordering::Relaxed);
    }
}

fn allocate(size: usize, align: usize) -> Option<*mut u8> {
    if size == 0 || !align.is_power_of_two() {
        return None;
    }
    let mut current = NEXT.load(Ordering::Relaxed);
    loop {
        let aligned = current.checked_add(align - 1)? & !(align - 1);
        let end = aligned.checked_add(size)?;
        if end > HEAP_SIZE {
            return None;
        }
        match NEXT.compare_exchange_weak(current, end, Ordering::AcqRel, Ordering::Relaxed) {
            Ok(_) => {
                ALLOCATION_COUNT.fetch_add(1, Ordering::Relaxed);
                let address = heap_start().checked_add(aligned)? as *mut u8;
                // SAFETY: This bump range is fresh, in-bounds, and remains allocated for the run.
                unsafe { ptr::write_bytes(address, 0, size) };
                return Some(address);
            }
            Err(observed) => current = observed,
        }
    }
}

fn heap_start() -> usize {
    // SAFETY: Taking a raw address does not create a reference to the mutable static.
    unsafe { ptr::addr_of_mut!(HEAP.0).cast::<u8>() as usize }
}

fn inside_ram(address: usize, size: usize) -> bool {
    range_inside(
        address,
        size,
        RAM_START.load(Ordering::Acquire),
        RAM_END.load(Ordering::Acquire),
    )
}

fn range_inside(address: usize, size: usize, start: usize, end: usize) -> bool {
    size > 0
        && address >= start
        && address
            .checked_add(size)
            .is_some_and(|range_end| range_end <= end)
}
