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
    /* Данные регистрации, которые читает start() семейства. Рабочая Sequoia-сборка (laobamac/itlwm,
       include/Airport/macOS15/IOSkywalkNetworkInterface.h, 15.8 / 24H23) заполняет fRegistrationInfo вручную
       перед start(); без этого start() разыменует NULL. Смещение 0xb8 и размер 0x130 взяты оттуда.
       fBSDInterface - ifnet_t, объявлен как void* (тот же размер), чтобы не тянуть заголовки kpi. */
    struct ExpansionData {
        RegistrationInfo *fRegistrationInfo;
        void *fBSDInterface;
    };
    uint8_t _layout0[0x8];              /* 0xb0 .. 0xb8 */
    ExpansionData *mExpansionData;      /* 0xb8 */
    uint8_t _layout1[0x10];             /* 0xc0 .. 0xd0 */
};
static_assert(sizeof(IOSkywalkNetworkInterface::RegistrationInfo) == 0x130, "RegistrationInfo size");
static_assert(sizeof(IOSkywalkNetworkInterface) == 0xd0, "IOSkywalkNetworkInterface size");
static_assert(__offsetof(IOSkywalkNetworkInterface, mExpansionData) == 0xb8, "IOSkywalkNetworkInterface::mExpansionData offset");
#endif
