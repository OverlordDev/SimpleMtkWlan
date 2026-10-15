//
//  AirportMtkWlanEthernetInterface.cpp
//  AirportMtkWlan-Sonoma
//
//  Created by qcwap on 2023/6/27.
//  Copyright © 2023 钟先耀. All rights reserved.
//

#include "AirportMtkWlanEthernetInterface.hpp"

#include <sys/_if_ether.h>
#include <net80211/ieee80211_var.h>

#include <IOKit/IOCommandGate.h>

/* Sequoia 15.2+: схема присоединения BSD-интерфейса из рабочей сборки laobamac/itlwm (ветка AIRPORT_WCL):
     - перед super::attachToDataLinkLayer() обязательно setInterfaceSubType(3);
     - prepareBSDInterface() выполняется ВНУТРИ gate очереди IO80211 (queue->inGate() && !queue->onThread()).
   Если setInterfaceSubType() не компилируется с вашим MacKernelSDK, сборка идёт так:
       -DMTK_SEQUOIA_BSD_ATTACH=0   (старое поведение, как до этой правки) */
#ifndef MTK_SEQUOIA_BSD_ATTACH
#define MTK_SEQUOIA_BSD_ATTACH 1
#endif

extern IOCommandGate *_fCommandGate;

#define super IOEthernetInterface
OSDefineMetaClassAndStructors(AirportMtkWlanEthernetInterface, IOEthernetInterface);

bool AirportMtkWlanEthernetInterface::
initWithSkywalkInterfaceAndProvider(IONetworkController *controller, IO80211SkywalkInterface *interface)
{
    bool ret = super::init(controller);
    if (ret)
        this->interface = interface;
    this->isAttach = false;
    return ret;
}

#if MTK_SEQUOIA_BSD_ATTACH
IOReturn AirportMtkWlanEthernetInterface::
prepareBSDGated(OSObject *, void *arg0, void *, void *, void *)
{
    AirportMtkWlanEthernetInterface *self = static_cast<AirportMtkWlanEthernetInterface *>(arg0);
    IO80211Controller *controller = OSDynamicCast(IO80211Controller, self->getController());
    IO80211WorkQueue *queue = controller ? controller->getWorkQueue() : NULL;
    if (!queue || !queue->inGate() || queue->onThread()) {
        XYLog("%s: not in the IO80211 work queue gate\n", __FUNCTION__);
        return kIOReturnNotPermitted;
    }
    return self->interface->prepareBSDInterface(self->getIfnet(), 0);
}
#endif

IOReturn AirportMtkWlanEthernetInterface::
attachToDataLinkLayer( IOOptionBits options, void *parameter )
{
    XYLog("%s\n", __FUNCTION__);
    char infName[IFNAMSIZ];
#if MTK_SEQUOIA_BSD_ATTACH
    if (!setInterfaceSubType(3)) {
        XYLog("%s: setInterfaceSubType(3) failed\n", __FUNCTION__);
        return kIOReturnNotReady;
    }
#endif
    IOReturn ret = super::attachToDataLinkLayer(options, parameter);
    if (ret == kIOReturnSuccess && interface) {
        UInt8 builtIn = 0;
        IOEthernetAddress addr;
        interface->setProperty("built-in", OSData::withBytes(&builtIn, sizeof(builtIn)));
        snprintf(infName, sizeof(infName), "%s%u", ifnet_name(getIfnet()), ifnet_unit(getIfnet()));
        interface->setProperty("IOInterfaceName", OSString::withCString(infName));
        interface->setProperty(kIOInterfaceUnit, OSNumber::withNumber(ifnet_unit(getIfnet()), 8));
        interface->setProperty(kIOInterfaceNamePrefix, OSString::withCString(ifnet_name(getIfnet())));
        if (OSDynamicCast(IOEthernetController, getController())->getHardwareAddress(&addr) == kIOReturnSuccess)
            setProperty(kIOMACAddress,  (void *) &addr,
                        kIOEthernetAddressSize);
#if MTK_SEQUOIA_BSD_ATTACH
        ret = _fCommandGate ? _fCommandGate->runAction(prepareBSDGated, this) : kIOReturnNotReady;
        if (ret != kIOReturnSuccess) {
            XYLog("%s: prepareBSDInterface under gate failed 0x%x\n", __FUNCTION__, ret);
            super::detachFromDataLinkLayer(options, parameter);
            isAttach = false;
            return ret;
        }
        isAttach = true;
        interface->registerService();
#else
        interface->registerService();
        interface->prepareBSDInterface(getIfnet(), 0);
#endif
//        ret = bpf_attach(getIfnet(), DLT_RAW, 0x48, &AirportMtkWlanEthernetInterface::bpfOutputPacket, &AirportMtkWlanEthernetInterface::bpfTap);
    }
#if MTK_SEQUOIA_BSD_ATTACH
    isAttach = (ret == kIOReturnSuccess);
#else
    isAttach = true;
#endif
    return ret;
}

void AirportMtkWlanEthernetInterface::
detachFromDataLinkLayer(IOOptionBits options, void *parameter)
{
    super::detachFromDataLinkLayer(options, parameter);
    isAttach = false;
}

/**
 Add another hack to fake that the provider is IOSkywalkNetworkInterface, to avoid skywalkfamily instance cast panic.
 */
IOService *AirportMtkWlanEthernetInterface::
getProvider() const
{
    return isAttach ? this->interface : super::getProvider();
}

errno_t AirportMtkWlanEthernetInterface::
bpfOutputPacket(ifnet_t interface, u_int32_t data_link_type, mbuf_t packet)
{
    XYLog("%s data_link_type: %d\n", __FUNCTION__, data_link_type);
    AirportMtkWlanEthernetInterface *networkInterface = (AirportMtkWlanEthernetInterface *)ifnet_softc(interface);
    return networkInterface->enqueueOutputPacket(packet);
}

errno_t AirportMtkWlanEthernetInterface::
bpfTap(ifnet_t interface, u_int32_t data_link_type, bpf_tap_mode direction)
{
    XYLog("%s data_link_type: %d direction: %d\n", __FUNCTION__, data_link_type, direction);
    return 0;
}

bool AirportMtkWlanEthernetInterface::
setLinkState(IO80211LinkState state)
{
    if (state == kIO80211NetworkLinkUp) {
        ifnet_set_flags(getIfnet(), ifnet_flags(getIfnet()) | (IFF_UP | IFF_RUNNING), (IFF_UP | IFF_RUNNING));
    } else {
        ifnet_set_flags(getIfnet(), ifnet_flags(getIfnet()) & ~(IFF_UP | IFF_RUNNING), 0);
    }
    return true;
}

extern const char* hexdump(uint8_t *buf, size_t len);

UInt32 AirportMtkWlanEthernetInterface::
inputPacket(mbuf_t packet, UInt32 length, IOOptionBits options, void *param)
{
    ether_header_t *eh;
    size_t len = mbuf_len(packet);
    
    eh = (ether_header_t *)mbuf_data(packet);
    if (len >= sizeof(ether_header_t) && eh->ether_type == htons(ETHERTYPE_PAE)) { // EAPOL packet
        const char* dump = hexdump((uint8_t*)mbuf_data(packet), len);
        XYLog("input EAPOL packet, len: %zu, data: %s\n", len, dump ? dump : "Failed to allocate memory");
        if (dump)
            IOFree((void*)dump, 3 * len + 1);
    }
    return IOEthernetInterface::inputPacket(packet, length, options, param);
}
