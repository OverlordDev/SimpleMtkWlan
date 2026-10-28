// Sequoia 15.8.1: IOSkywalkNetworkInterface (0xd0)
#ifndef IOSkywalkNetworkInterface_h
#define IOSkywalkNetworkInterface_h
#include <net/if.h>
#include "IOSkywalkInterface.h"
struct if_link_status;   /* mangled: PK14if_link_status */
class IOSkywalkPacketQueue;
class IOSkywalkLogicalLink;
class IOSkywalkPacketBufferPool;
struct ifdrv;
class IOSkywalkNetworkInterface : public IOSkywalkInterface {
    OSDeclareAbstractStructors(IOSkywalkNetworkInterface)
public:
    struct RegistrationInfo {
        uint8_t pad[304];
    } __attribute__((packed));
    struct IOSkywalkTSOOptions;
public:
#include "gen/IOSkywalkNetworkInterface.inc"
public:
    // не виртуальные, экспортируются ядром
    void reportLinkStatus(unsigned int, unsigned int);
    void reportDetailedLinkStatus_nv();   // заглушка имени, реально виртуальный слот выше
protected:
    uint8_t _abi_pad_IOSkywalkNetworkInterface[0xd0 - sizeof(IOSkywalkInterface)];
};
static_assert(sizeof(IOSkywalkNetworkInterface) == 0xd0, "IOSkywalkNetworkInterface size");
#endif
