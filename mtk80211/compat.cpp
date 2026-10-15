//
//  compat.cpp
//  SimpleMtkWlan
//
//  Created by laobamac (王孝慈) on 2026/4/15.
//  Copyright © 2026 laobamac (王孝慈). All rights reserved.
//

/*
* Copyright (C) 2020  钟先耀
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*/
//
//  compat.cpp
//  net80211
//
//  Copyright (c) 2012 Prashant Vaibhav. All rights reserved.
//

#include "compat.h"
#include <IOKit/IOLib.h>
#include <sys/random.h>
#include <sys/param.h>
#include <sys/proc.h>

OSDefineMetaClassAndStructors(pci_intr_handle, OSObject)

int pci_get_capability(pci_chipset_tag_t chipsettag, pcitag_t pcitag, int capid, int *offsetp, pcireg_t *valuep) {
	uint8_t offset;
	UInt32 value = pcitag->findPCICapability(capid, &offset);
	if (valuep)
		*valuep = (pcireg_t)value;
	if (offsetp)
		*offsetp = offset;
	if (value == 0)
		return 0;
	else
		return 1;
}

pcireg_t pci_conf_read(pci_chipset_tag_t pc, pcitag_t tag, int reg) {
	return tag->configRead32(reg);
}

void pci_conf_write(pci_chipset_tag_t pc, pcitag_t tag, int reg, pcireg_t val) {
	tag->configWrite32(reg, val);
}

pcireg_t pci_mapreg_type(pci_chipset_tag_t pc, pcitag_t tag, int reg) {
	return 0; // XXX this is not needed on OS X, will always be memorymap
}

int pci_mapreg_map(const struct pci_attach_args *pa, int reg, pcireg_t type, int busflags, bus_space_tag_t *tagp,
		   bus_space_handle_t *handlep, bus_addr_t *basep, bus_size_t *sizep, bus_size_t maxsize)
{	
	IOMemoryMap* map = pa->pa_tag->mapDeviceMemoryWithRegister(reg);
	if (map == 0)
		return kIOReturnError;
	
	*handlep = reinterpret_cast<caddr_t>(map->getVirtualAddress());
	
	if (tagp)
		*tagp = map;
	if (basep)
		*basep = map->getVirtualAddress();
	if (sizep)
		*sizep = map->getSize();
	
	return 0;
}

int
pci_intr_map_msix(struct pci_attach_args *pa, int vec, pci_intr_handle_t *ihp)
{
    pci_chipset_tag_t pc = pa->pa_pc;
    pcitag_t tag = pa->pa_tag;
    pcireg_t reg;

    KASSERT(PCI_MSIX_VEC(vec) == vec, "PCI_MSIX_VEC(vec) == vec");

    if (pci_get_capability(pc, tag, PCI_CAP_MSIX, NULL, &reg) == 0)
        return 1;

    if (vec > PCI_MSIX_MC_TBLSZ(reg))
        return 1;
    
    return pci_intr_map_msi(pa, ihp);
}

int pci_intr_map_msi(struct pci_attach_args *paa, pci_intr_handle_t *ih) {
	if (paa == 0 || ih == 0)
		return 1;
	
	*ih = new pci_intr_handle();
	
	if (*ih == 0)
		return 1;
	
	(*ih)->dev = paa->pa_tag;  // pci device reference
	
	(*ih)->workloop = paa->workloop;
	
	return 0; // XXX not required on OS X
}

int pci_intr_map(struct pci_attach_args *paa, pci_intr_handle_t *ih) {
	return pci_intr_map_msi(paa, ih);
}

void interruptTrampoline(OSObject *ih, IOInterruptEventSource *, int count);
void interruptTrampoline(OSObject *ih, IOInterruptEventSource *, int count) {
	pci_intr_handle* _ih = OSDynamicCast(pci_intr_handle, ih);
	if (_ih == 0)
		return;
	(void)_ih->func(_ih->arg); // jump to actual interrupt handler
}

void* pci_intr_establish(pci_chipset_tag_t pc, pci_intr_handle_t ih, int level, int (*handler)(void *), void *arg) {
	ih->arg = arg;
	ih->func = handler;
	ih->intr = IOInterruptEventSource::interruptEventSource(ih, &interruptTrampoline, ih->dev);
	
	if (ih->intr == 0)
		return 0;
	if (ih->workloop->addEventSource(ih->intr) != kIOReturnSuccess)
		return 0;
	
	ih->intr->enable();
	return ih;
}

void* pci_intr_establish(pci_chipset_tag_t pc, pci_intr_handle_t ih, int level, int (*handler)(void *), void *arg, const char *name) {
	return pci_intr_establish(pc, ih, level, handler, arg);
}

void pci_intr_disestablish(pci_chipset_tag_t pc, void *ih) {
	pci_intr_handle_t intr = (pci_intr_handle_t) ih;
	
	if (intr->workloop && intr->intr)
		intr->workloop->removeEventSource(intr->intr);
	if (intr->intr)
		intr->intr->release();
	intr->intr = 0;
	
	intr->dev = 0;
	
	intr->workloop = 0;
	
	intr->arg = 0;
	intr->func = 0;
	intr->release();
	intr = 0;
	ih = 0;
}

const char *pci_intr_string(pci_chipset_tag_t pc, pci_intr_handle_t ih) {
	return "msi";
}

uint64_t bus_space_read_8(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset) {
    return *((uint64_t*)(handle + offset));
}

void bus_space_write_8(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset, uint64_t value) {
    *((uint64_t*)(handle + offset)) = value;
}

uint32_t bus_space_read_4(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset) {
	return *((uint32_t*)(handle + offset));
}

void bus_space_write_1(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset, uint8_t value) {
    *((uint8_t*)(handle + offset)) = value;
}

void bus_space_write_4(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset, uint32_t value) {
	*((uint32_t*)(handle + offset)) = value;
}

void bus_space_barrier(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t offset, bus_size_t length, int flags) {
	return; // In OSX device memory access is always uncached and serialized (afaik!)
}

void bus_space_unmap(bus_space_tag_t space, bus_space_handle_t handle, bus_size_t size) {
	if (space)
		space->release();
}

int bus_dmamap_create(bus_dma_tag_t tag, bus_size_t size, int nsegments, bus_size_t maxsegsz, bus_size_t boundary, int flags, bus_dmamap_t *dmamp) {
	if (dmamp == 0)
		return 1;
	*dmamp = new bus_dmamap;
	memset(*dmamp, 0, sizeof(**dmamp));
	(*dmamp)->dm_maxsize = size;
	(*dmamp)->dm_maxsegs = nsegments;
	(*dmamp)->cursor = IOMbufNaturalMemoryCursor::withSpecification(maxsegsz, nsegments);
	if ((*dmamp)->cursor == 0)
		return 1;
	else
		return 0;
}

IOBufferMemoryDescriptor* alloc_dma_memory(size_t size, mach_vm_address_t alignment,/* void** vaddr, mach_vm_address_t* paddr, */IOOptionBits opts);
IOBufferMemoryDescriptor* alloc_dma_memory(size_t size, mach_vm_address_t alignment,/* void** vaddr, mach_vm_address_t* paddr, */IOOptionBits opts = kIOMemoryPhysicallyContiguous | kIOMapInhibitCache)
{
	size_t		reqsize;
	uint64_t	phymask;
	int		i;
	/*
	if (alignment <= PAGE_SIZE) {
		reqsize = size;
		phymask = 0x00000000ffffffffull & (~(alignment - 1));
	} else {
		reqsize = size + alignment;
		phymask = 0x00000000fffff000ull; /* page-aligned 
	}*/
	
	phymask = 0x00000000ffffffffull & (~(alignment - 1));
	reqsize = size;
	
	IOBufferMemoryDescriptor* mem = 0;
	mem = IOBufferMemoryDescriptor::inTaskWithPhysicalMask(kernel_task, opts, reqsize, phymask);
	if (!mem)
		return 0;

	mem->prepare();
	/*
	if (paddr)
		*paddr = mem->getPhysicalAddress();
	if (vaddr)
		*vaddr = mem->getBytesNoCopy();
	
	/*
	 * Check the alignment and increment by 4096 until we get the
	 * requested alignment. Fail if can't obtain the alignment
	 * we requested.
	 
	if ((*paddr & (alignment - 1)) != 0) {
		for (i = 0; i < alignment / 4096; i++) {
			if ((*paddr & (alignment - 1 )) == 0)
				break;
			*paddr += 4096;
			*vaddr = ((uint8_t*) *vaddr) + 4096;
		}
		if (i == alignment / 4096) {
			mem->complete();
			mem->release();
			return 0;
		}
	}*/
	return mem;
}


int bus_dmamem_alloc(bus_dma_tag_t tag, bus_size_t size, bus_size_t alignment, bus_size_t boundary, bus_dma_segment_t *segs, int nsegs, int *rsegs, int flags) {
	// Ignore flags and don't pass in the number of segments, it's not used in the driver (always 1 anyway)
	if (segs == 0)
		return 1;
	memset(segs, 0, sizeof(*segs));
	segs->buf = alloc_dma_memory(size, alignment);
	if (segs->buf == 0)
		return 1;
	segs->ds_addr = segs->buf->getPhysicalAddress();
	segs->ds_len = size;
	if (rsegs)
		*rsegs = 1;
	return 0;
}

int bus_dmamem_map(bus_dma_tag_t tag, bus_dma_segment_t *segs, int nsegs, size_t size, void **kvap, int flags) {
	// ignore flags, the memory is already mapped as one segment by the call to bus_dmamem_alloc so just return the virtual address
	if (segs == 0 || segs->buf == 0 || kvap == 0)
		return 1;
	*kvap = segs->buf->getBytesNoCopy();
	return 0;
}

bus_addr_t bus_dmamap_get_paddr(bus_dma_segment_t seg) {
	if (seg.buf == 0)
		return 0;
	else
		return seg.ds_addr;
}

void bus_dmamap_sync(bus_dma_tag_t tag, bus_dmamap_t dmam, bus_addr_t offset, bus_size_t len, int ops) {
	if ((ops & (BUS_DMASYNC_PREWRITE | BUS_DMASYNC_POSTREAD)) == 0)
		return;
	if (dmam == 0 || !dmam->dm_bounce || dmam->dm_bounce_mem == 0 ||
	    dmam->dm_mbuf == 0)
		return;

	void *bounce = dmam->dm_bounce_mem->getBytesNoCopy();
	if (bounce == 0)
		return;

	size_t copy_len = len;
	if (offset > dmam->dm_mapsize)
		return;
	if (copy_len > dmam->dm_mapsize - offset)
		copy_len = dmam->dm_mapsize - offset;
	if (copy_len == 0)
		return;

	if (ops & BUS_DMASYNC_PREWRITE) {
		mbuf_copydata(dmam->dm_mbuf, offset, copy_len,
		    (uint8_t *)bounce + offset);
	}
	if (ops & BUS_DMASYNC_POSTREAD) {
		mbuf_copyback(dmam->dm_mbuf, offset, copy_len,
		    (uint8_t *)bounce + offset, MBUF_DONTWAIT);
		mbuf_inbound_modified(dmam->dm_mbuf);
	}
}

void bus_dmamem_unmap(bus_dma_segment_t seg) {
	if (seg.buf == 0)
		return;
	seg.buf->complete();
}

void bus_dmamem_unmap(bus_dma_tag_t tag, void *kva, size_t size) {
	return;
}

void bus_dmamem_free(bus_dma_tag_t tag, bus_dma_segment_t *segs, int nsegs) {
	if (segs == 0)
		return;
	if (segs->buf == 0)
		return;
	segs->buf->release();
	memset(segs, 0, sizeof(*segs));
}

void bus_dmamap_destroy(bus_dma_tag_t tag, bus_dmamap_t dmam) {
	if (dmam == 0)
		return;
	if (dmam->mem) {
		dmam->mem->complete();
		dmam->mem->release();
	}
	dmam->mem = 0;
	if (dmam->dm_bounce_mem) {
		dmam->dm_bounce_mem->complete();
		dmam->dm_bounce_mem->release();
	}
	dmam->dm_bounce_mem = 0;
	if (dmam->cursor)
		dmam->cursor->release();
	dmam->cursor = 0;
	delete dmam;
}

int bus_dmamap_load(bus_dmamap_t map, mbuf_t mb) {
	if (map == 0 || mb == 0)
		return 1;
	IOPhysicalSegment segs[23];
	if (map->mem) {
		map->mem->complete();
		map->mem->release();
		map->mem = 0;
	}
	map->dm_mbuf = mb;
	map->dm_bounce = false;
	map->dm_nsegs = map->cursor->getPhysicalSegmentsWithCoalesce(mb, segs, 23);
	if (map->dm_nsegs == 0)
		return 1;
	size_t pktlen = mbuf_pkthdr_len(mb);
	if (pktlen > UINT32_MAX)
		return 1;
	map->dm_mapsize = (bus_size_t)pktlen;
	bool needs_bounce = false;
	/*
	 * The device descriptors only have room for dm_maxsegs buffers
	 * (4 in the TX descriptor). Chains with more physical segments
	 * overflowed the descriptor and corrupted the neighbouring TX
	 * descriptors, hanging the DMA engine under load. Linearise those
	 * through the bounce buffer instead.
	 */
	if (map->dm_maxsegs > 0 && map->dm_nsegs > map->dm_maxsegs) {
		static uint32_t seg_log_count;
		if (seg_log_count < 16 || (seg_log_count % 1024) == 0)
			mtk_ringlog("dmaseg overflow nsegs=%d max=%d len=%zu -> bounce\n",
			    map->dm_nsegs, map->dm_maxsegs, pktlen);
		seg_log_count++;
		needs_bounce = true;
	}
	for (int i = 0; i < map->dm_nsegs && !needs_bounce; i++) {
		if (segs[i].location > UINT32_MAX || segs[i].length > UINT32_MAX) {
			needs_bounce = true;
			break;
		}
	}
	if (needs_bounce) {
		static uint32_t bounce_log_count;
		bus_size_t bounce_size = map->dm_maxsize;
		if (bounce_size == 0 || bounce_size < pktlen)
			bounce_size = (bus_size_t)pktlen;
		if (map->dm_bounce_mem == 0 ||
		    map->dm_bounce_size < bounce_size) {
			if (map->dm_bounce_mem != 0) {
				map->dm_bounce_mem->complete();
				map->dm_bounce_mem->release();
				map->dm_bounce_mem = 0;
				map->dm_bounce_size = 0;
			}
			IOBufferMemoryDescriptor *mem =
			    alloc_dma_memory(bounce_size, PAGE_SIZE);
			if (mem == 0)
				return 1;
			map->dm_bounce_mem = mem;
			map->dm_bounce_size = bounce_size;
		}
		bus_addr_t addr = map->dm_bounce_mem->getPhysicalAddress();
		if (addr > UINT32_MAX) {
			return 1;
		}
		map->dm_bounce = true;
		map->dm_nsegs = 1;
		map->dm_segs[0].buf = NULL;
		map->dm_segs[0].ds_addr = addr;
		map->dm_segs[0].ds_len = (bus_size_t)pktlen;
		if (bounce_log_count < 16) {
			IOLog("SimpleMtkWlan-dma: bounce mbuf map len=%zu bounce_size=%u dma=0x%llx\n",
			    pktlen, map->dm_bounce_size, (unsigned long long)addr);
			bounce_log_count++;
		}
		return 0;
	}
	for (int i = 0; i < map->dm_nsegs; i++) {
		map->dm_segs[i].buf = NULL;
		map->dm_segs[i].ds_addr = segs[i].location;
		map->dm_segs[i].ds_len = (bus_size_t)segs[i].length;
	}
	return 0;
}

int bus_dmamap_load(bus_dma_tag_t tag, bus_dmamap_t map, void *buf, bus_size_t buflen, void *p, int flags) {
	if (map == 0 || buf == 0)
		return 1;
	if (map->mem) {
		map->mem->complete();
		map->mem->release();
		map->mem = 0;
	}
	IOMemoryDescriptor *mem = IOMemoryDescriptor::withAddress(buf, buflen,
	    kIODirectionOutIn);
	if (mem == 0)
		return 1;
	if (mem->prepare(kIODirectionOutIn) != kIOReturnSuccess) {
		mem->release();
		return 1;
	}

	IOByteCount offset = 0;
	bus_size_t remaining = buflen;
	int nsegs = 0;

	while (remaining > 0 && nsegs < 23) {
		IOByteCount seglen = 0;
		addr64_t addr = mem->getPhysicalSegment(offset, &seglen);

		if (addr == 0 || seglen == 0)
			break;
		if (seglen > remaining)
			seglen = remaining;
		map->dm_segs[nsegs].buf = NULL;
		map->dm_segs[nsegs].ds_addr = (bus_addr_t)addr;
		map->dm_segs[nsegs].ds_len = (bus_size_t)seglen;
		offset += seglen;
		remaining -= seglen;
		nsegs++;
	}
	if (remaining != 0) {
		mem->complete();
		mem->release();
		map->dm_nsegs = 0;
		map->dm_mapsize = 0;
		return 1;
	}
	map->mem = mem;
	map->dm_mbuf = 0;
	map->dm_bounce = false;
	map->dm_nsegs = nsegs;
	map->dm_mapsize = buflen;
	return 0;
}

int bus_dmamap_load_mbuf(bus_dma_tag_t tag, bus_dmamap_t map, mbuf_t m, int flags) {
	return bus_dmamap_load(map, m);
}

void bus_dmamap_unload(bus_dma_tag_t tag, bus_dmamap_t map) {
	if (map == 0)
		return;
	if (map->mem) {
		map->mem->complete();
		map->mem->release();
		map->mem = 0;
	}
	map->dm_mbuf = 0;
	map->dm_bounce = false;
	map->dm_nsegs = 0;
	map->dm_mapsize = 0;
}

/*
 * Debug ring buffer. Kernel printf from this kext does not reach the unified
 * log on recent macOS, so lines are also kept here and published to the
 * IORegistry property "MtkLog" (read with: ioreg -w0 -rn SimpleMtkWlan).
 */
#include <IOKit/IOService.h>
#include <libkern/libkern.h>
#include <kern/clock.h>
#include <kern/thread_call.h>

#define MTK_RING_SIZE 40000
static char mtk_ring[MTK_RING_SIZE];
static UInt32 mtk_ring_len;
static UInt32 mtk_ring_seq;
#define MTK_HB_SIZE 30000
static char mtk_hb[MTK_HB_SIZE];
static UInt32 mtk_hb_len;
static UInt32 mtk_hb_seq;
#define MTK_KEEP_SIZE 28000
static char mtk_keep[MTK_KEEP_SIZE];
static UInt32 mtk_keep_len;
static UInt32 mtk_keep_seq;
static IOSimpleLock *mtk_ring_lock;
static thread_call_t mtk_ring_call;
static IOService *mtk_ring_svc;
static bool mtk_ring_run;

static bool mtk_has(const char *h, const char *n)
{
    size_t nl = strlen(n);
    for (; *h; h++)
        if (strncmp(h, n, nl) == 0)
            return true;
    return false;
}

extern "C" void mtk_ringlog(const char *fmt, ...)
{
    char line[600];
    va_list ap;
    int n;
    clock_sec_t sec;
    clock_usec_t usec;

    if (!mtk_ring_lock)
        return;
    /* drop high-volume per-frame/scan chatter so the ring keeps the interesting part */
    if (fmt && (mtk_has(fmt, "txwi") || mtk_has(fmt, "tx desc") || mtk_has(fmt, "tx free event") ||
        mtk_has(fmt, "TXS wcid") || mtk_has(fmt, "tx frame wcid") || mtk_has(fmt, "scan request") ||
        mtk_has(fmt, "mcu tx cmd") || mtk_has(fmt, "newstate task 1 -> 1")))
        return;
    clock_get_calendar_microtime(&sec, &usec);
    n = snprintf(line, sizeof(line), "[%u.%03u] ", (unsigned)(sec % 100000), (unsigned)(usec / 1000));
    va_start(ap, fmt);
    n += vsnprintf(line + n, sizeof(line) - n, fmt, ap);
    va_end(ap);
    if (n >= (int)sizeof(line))
        n = sizeof(line) - 1;
    if (n > 0 && line[n - 1] != '\n') {
        if (n < (int)sizeof(line) - 1)
            line[n++] = '\n';
        else
            line[n - 1] = '\n';
    }

    /* separate rolling buffer for the 1 Hz heartbeat and hardware dumps */
    if (mtk_has(line, " HB ") || mtk_has(line, " HW ")) {
        IOInterruptState hs = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
        if (mtk_hb_len + n > MTK_HB_SIZE) {
            UInt32 drop = mtk_hb_len + n - MTK_HB_SIZE;
            if (drop > mtk_hb_len)
                drop = mtk_hb_len;
            memmove(mtk_hb, mtk_hb + drop, mtk_hb_len - drop);
            mtk_hb_len -= drop;
        }
        memcpy(mtk_hb + mtk_hb_len, line, n);
        mtk_hb_len += n;
        mtk_hb_seq++;
        IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, hs);
        return;
    }

    /* never-rolling buffer for one-off dumps (assoc req, beacons, mgmt frames) */
    if (mtk_has(line, " TXASSOCREQ ") || mtk_has(line, " RXMGT ") || mtk_has(line, " APRSNIE ") ||
        mtk_has(line, " BCNDUMP ") || mtk_has(line, " VARIANT ") || mtk_has(line, " CAND ") || mtk_has(line, " UTXD ") ||
        mtk_has(line, "key add done") || mtk_has(line, "key add complete")) {
        IOInterruptState ks = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
        if (mtk_keep_len + n <= MTK_KEEP_SIZE) {
            memcpy(mtk_keep + mtk_keep_len, line, n);
            mtk_keep_len += n;
            mtk_keep_seq++;
        }
        IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, ks);
        return;
    }

    IOInterruptState st = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
    if (mtk_ring_len + n > MTK_RING_SIZE) {
        UInt32 drop = mtk_ring_len + n - MTK_RING_SIZE;
        if (drop > mtk_ring_len)
            drop = mtk_ring_len;
        memmove(mtk_ring, mtk_ring + drop, mtk_ring_len - drop);
        mtk_ring_len -= drop;
    }
    memcpy(mtk_ring + mtk_ring_len, line, n);
    mtk_ring_len += n;
    mtk_ring_seq++;
    IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, st);
}

static void mtk_ring_publish(thread_call_param_t, thread_call_param_t)
{
    static UInt32 last_seq = (UInt32)-1, last_kseq = (UInt32)-1, last_hseq = (UInt32)-1;
    char *copy = (char *)IOMalloc(MTK_RING_SIZE + 1);
    if (copy && mtk_ring_svc) {
        UInt32 len = 0, seq;
        IOInterruptState st = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
        seq = mtk_ring_seq;
        if (seq != last_seq) {
            len = mtk_ring_len;
            memcpy(copy, mtk_ring, len);
        }
        IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, st);
        if (seq != last_seq) {
            copy[len] = 0;
            last_seq = seq;
            mtk_ring_svc->setProperty("MtkLog", copy);
        }
    }
    if (copy)
        IOFree(copy, MTK_RING_SIZE + 1);
    {
        char *kc = (char *)IOMalloc(MTK_KEEP_SIZE + 1);
        if (kc && mtk_ring_svc) {
            UInt32 kl = 0, ks;
            IOInterruptState st = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
            ks = mtk_keep_seq;
            if (ks != last_kseq) {
                kl = mtk_keep_len;
                memcpy(kc, mtk_keep, kl);
            }
            IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, st);
            if (ks != last_kseq) {
                kc[kl] = 0;
                last_kseq = ks;
                mtk_ring_svc->setProperty("MtkKeep", kc);
            }
        }
        if (kc)
            IOFree(kc, MTK_KEEP_SIZE + 1);
    }
    {
        char *hc = (char *)IOMalloc(MTK_HB_SIZE + 1);
        if (hc && mtk_ring_svc) {
            UInt32 hl = 0, hs;
            IOInterruptState st = IOSimpleLockLockDisableInterrupt(mtk_ring_lock);
            hs = mtk_hb_seq;
            if (hs != last_hseq) {
                hl = mtk_hb_len;
                memcpy(hc, mtk_hb, hl);
            }
            IOSimpleLockUnlockEnableInterrupt(mtk_ring_lock, st);
            if (hs != last_hseq) {
                hc[hl] = 0;
                last_hseq = hs;
                mtk_ring_svc->setProperty("MtkHB", hc);
            }
        }
        if (hc)
            IOFree(hc, MTK_HB_SIZE + 1);
    }
    if (mtk_ring_run) {
        uint64_t dl;
        clock_interval_to_deadline(500, kMillisecondScale, &dl);
        thread_call_enter_delayed(mtk_ring_call, dl);
    }
}

extern "C" void mtk_ringlog_start(IOService *svc)
{
    if (mtk_ring_call)
        return;
    mtk_ring_lock = IOSimpleLockAlloc();
    mtk_ring_svc = svc;
    mtk_ring_run = true;
    mtk_ring_call = thread_call_allocate(mtk_ring_publish, NULL);
    mtk_ringlog("ringlog started\n");
    if (mtk_ring_call)
        thread_call_enter(mtk_ring_call);
}

extern "C" void mtk_ringlog_stop(void)
{
    mtk_ring_run = false;
    if (mtk_ring_call) {
        thread_call_cancel_wait(mtk_ring_call);
        thread_call_free(mtk_ring_call);
        mtk_ring_call = NULL;
    }
    mtk_ring_svc = NULL;
}
