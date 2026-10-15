//
//  CCStream.h
//  itlwm
//
//  Created by qcwap on 2023/6/14.
//  Copyright © 2023 钟先耀. All rights reserved.
//

#ifndef CCStream_h
#define CCStream_h

#include <IOKit/IOService.h>
#include "CCPipe.h"

struct CCStreamOptions {
    uint64_t stream_type;
    uint64_t console_level;
    char pad[0x348];
};

class CCStream : public IOService {
    OSDeclareAbstractStructors(CCStream)
    
public:
    virtual void free() APPLE_KEXT_OVERRIDE;
    virtual IOReturn configureReport(IOReportChannelList *,UInt,void *,void *) APPLE_KEXT_OVERRIDE;
    virtual IOReturn updateReport(IOReportChannelList *,UInt,void *,void *) APPLE_KEXT_OVERRIDE;
    virtual bool attach( IOService * provider ) APPLE_KEXT_OVERRIDE;
    virtual void detach( IOService * provider ) APPLE_KEXT_OVERRIDE;
    virtual bool profileLoaded(void);
    virtual bool profileRemoved(void);
    virtual CCStream const *initWithPipeAndName(CCPipe *,char const*,CCStreamOptions const*);
    
public:
    static CCStream *withPipeAndName(CCPipe *,char const*,CCStreamOptions const*);
    CCPipe *getPipe() const;
    
public:
    uint8_t filter[0x90];
};


/* Sequoia 15.x: поток данных (stream_type 1) и репортёр сбоев поверх него; в ядре экспортируются */
class CCDataStream : public CCStream {
    OSDeclareAbstractStructors(CCDataStream)
public:
    uint8_t _pad_unused;
};

class CCFaultReporter : public OSObject {
    OSDeclareAbstractStructors(CCFaultReporter)
public:
    static CCFaultReporter *withStreamWorkloop(CCDataStream *, IOWorkLoop *);
};

/* Sequoia 15.x: Family через getFaultReporterFromDriver() ждёт НЕ CCFaultReporter, а обёртку IO80211FaultReporter
   (CommonFaultReporter). Рабочая сборка laobamac/itlwm (include/Airport/macOS15/FaultReporter.h):
       core = CCFaultReporter::withStreamWorkloop(dataStream, workloop);
       rep  = IO80211FaultReporter::allocWithParams(core);   // проверить OSDynamicCast(CommonFaultReporter, rep)
   Классы живут в ядре (IO80211Family); здесь только объявления. */
class CommonFaultReporter : public OSObject {
    OSDeclareAbstractStructors(CommonFaultReporter)
};

class IO80211FaultReporter : public CommonFaultReporter {
    OSDeclareDefaultStructors(IO80211FaultReporter)
public:
    static IO80211FaultReporter *allocWithParams(CCFaultReporter *);
};

#endif /* CCStream_h */