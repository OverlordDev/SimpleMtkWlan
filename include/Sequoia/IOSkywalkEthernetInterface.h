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
protected:
    uint8_t _abi_pad_IOSkywalkEthernetInterface[0x110 - sizeof(IOSkywalkNetworkInterface)];
};
static_assert(sizeof(IOSkywalkEthernetInterface) == 0x110, "IOSkywalkEthernetInterface size");
#endif
