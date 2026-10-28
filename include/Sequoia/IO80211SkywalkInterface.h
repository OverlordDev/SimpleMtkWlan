//
//  IO80211SkywalkInterface.h
//  IO80211Family
//
//  Created by 钟先耀 on 2019/10/18.
//  Copyright © 2019 钟先耀. All rights reserved.
//

#ifndef _IO80211SKYWALK_H
#define _IO80211SKYWALK_H

#include <Availability.h>
#include "IOSkywalkEthernetInterface.h"

// This is necessary, because even the latest Xcode does not support properly targeting 11.0.
#ifndef __IO80211_TARGET
#error "Please define __IO80211_TARGET to the requested version"
#endif

class TxSubmissionDequeueStats;
class TxCompletionEnqueueStats;
class IO80211NetworkPacket;
class PacketSkywalkScratch;
struct IO80211FlowQueueHash { uint64_t hash; };   /* в ядре Sequoia это структура (mangled 20IO80211FlowQueueHash) */
class IO80211Peer;
class CCPipe;
class IO80211APIUserClient;
struct apple80211_wme_ac;
struct apple80211_interface_availability;
struct apple80211_cca_report;
struct apple80211_stat_report;
struct apple80211_chip_counters_tx;
struct apple80211_chip_counters_rx;
struct apple80211_chip_error_counters_tx;
struct apple80211_ManagementInformationBasedot11_counters;
struct apple80211_lteCoex_report;
struct apple80211_frame_counters;
struct userPrintCtx;
struct apple80211_lqm_summary;
struct apple80211_infra_specific_stats;

struct TxPacketRequest {
    uint16_t    unk1;       // 0
    uint16_t    t;       // 2
    uint16_t    mU;       // 4
    uint16_t    mM;       // 6
    uint16_t    pkt_cnt;
    uint16_t    unk2;
    uint16_t    unk3;
    uint16_t    unk4;
    uint32_t    pad;
    mbuf_t      bufs[8];    // 18
    uint32_t    reqTx;
};

static_assert(sizeof(struct TxPacketRequest) == 0x60, "TxPacketRequest size error");

class IO80211SkywalkInterface : public IOSkywalkEthernetInterface {
    OSDeclareAbstractStructors(IO80211SkywalkInterface)
public:
#include "gen/IO80211SkywalkInterface.inc"
public:
    /* не виртуальные, экспортируются ядром (вызываются драйвером Apple напрямую) */
    void setInterfaceRole(UInt);
    UInt getInterfaceRole();
    void setInterfaceId(UInt);
    UInt getInterfaceId();
    void setInitMacAddress(ether_addr&);
protected:
    uint8_t _abi_pad_IO80211SkywalkInterface[0x118 - sizeof(IOSkywalkEthernetInterface)];
};
static_assert(sizeof(IO80211SkywalkInterface) == 0x118, "IO80211SkywalkInterface size");
#endif
