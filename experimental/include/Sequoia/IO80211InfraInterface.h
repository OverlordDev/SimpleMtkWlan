//
//  IO80211InfraInterface.h
//  itlwm
//
//  Created by qcwap on 2023/6/12.
//  Copyright © 2023 钟先耀. All rights reserved.
//

#ifndef IO80211InfraInterface_h
#define IO80211InfraInterface_h

struct apple80211_wcl_advisory_info;
struct apple80211_wcl_tx_rx_latency;

class IO80211InfraInterface : public IO80211SkywalkInterface {
    OSDeclareAbstractStructors(IO80211InfraInterface)
public:
#include "gen/IO80211InfraInterface.inc"
protected:
    uint8_t _abi_pad_IO80211InfraInterface[0x120 - sizeof(IO80211SkywalkInterface)];
};
static_assert(sizeof(IO80211InfraInterface) == 0x120, "IO80211InfraInterface size");
#endif
