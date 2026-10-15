// Sequoia 15.8.1: IOSkywalkEthernetInterface (0x110)
#ifndef IOSkywalkEthernetInterface_h
#define IOSkywalkEthernetInterface_h
#include "IOSkywalkNetworkInterface.h"
struct nicproxy_limits_info_s;
struct nicproxy_info_s;
class IOSkywalkEthernetInterface : public IOSkywalkNetworkInterface {
    OSDeclareAbstractStructors(IOSkywalkEthernetInterface)
public:
    struct RegistrationInfo {
        uint8_t pad[304];
    } __attribute__((packed));
public:
#include "gen/IOSkywalkEthernetInterface.inc"
public:
    bool initRegistrationInfo(IOSkywalkEthernetInterface::RegistrationInfo*, unsigned int, unsigned long);
    bool registerEthernetInterface(IOSkywalkEthernetInterface::RegistrationInfo const*, IOSkywalkPacketQueue**, unsigned int, IOSkywalkPacketBufferPool*, IOSkywalkPacketBufferPool*, unsigned int);
    /* Ethernet-часть данных регистрации (см. IOSkywalkNetworkInterface.h). Смещение 0x108 - из
       laobamac/itlwm include/Airport/macOS15/IOSkywalkEthernetInterface.h (static_assert там же). */
    struct ExpansionData {
        RegistrationInfo *fRegistrationInfo;
        void *fBSDInterface;
    };
    uint8_t _layout0[0x38];             /* 0xd0 .. 0x108 */
    ExpansionData *mExpansionData2;     /* 0x108 */
};
static_assert(sizeof(IOSkywalkEthernetInterface::RegistrationInfo) == 0x130, "RegistrationInfo size");
static_assert(sizeof(IOSkywalkEthernetInterface) == 0x110, "IOSkywalkEthernetInterface size");
static_assert(__offsetof(IOSkywalkEthernetInterface, mExpansionData2) == 0x108, "IOSkywalkEthernetInterface::mExpansionData2 offset");
#endif
