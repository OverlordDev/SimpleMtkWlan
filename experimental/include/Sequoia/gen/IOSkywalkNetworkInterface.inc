// slots 282..331 из vtable Sequoia
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual bool init(OSDictionary*) APPLE_KEXT_OVERRIDE;   // override slot 73
    virtual void stop(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 185
    virtual void joinPMtree(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 244
    virtual IOReturn setAggressiveness(unsigned long, unsigned long) APPLE_KEXT_OVERRIDE;   // override slot 248
    virtual IOReturn enable(UInt) APPLE_KEXT_OVERRIDE;   // override slot 266
    virtual IOReturn disable(UInt) APPLE_KEXT_OVERRIDE;   // override slot 267
    virtual IOReturn registerNetworkInterfaceWithLogicalLink(IOSkywalkNetworkInterface::RegistrationInfo const*, IOSkywalkLogicalLink*, IOSkywalkPacketBufferPool*, IOSkywalkPacketBufferPool*, UInt);   // slot 282
    virtual IOReturn deregisterLogicalLink();   // slot 283
    virtual SInt32 initBSDInterfaceParameters(ifnet_init_eparams*, sockaddr_dl**) = 0;   // slot 284
    virtual bool prepareBSDInterface(__ifnet*, UInt);   // slot 285
    virtual void finalizeBSDInterface(__ifnet*, UInt);   // slot 286
    virtual ifnet_t getBSDInterface() const;   // slot 287
    virtual void setBSDName(char const*);   // slot 288
    virtual const char * getBSDName() const;   // slot 289
    virtual IOReturn processBSDCommand(__ifnet*, UInt, void*);   // slot 290
    virtual IOReturn processInterfaceCommand(ifdrv*);   // slot 291
    virtual IOReturn interfaceAdvisoryEnable(bool);   // slot 292
    virtual SInt32 setInterfaceEnable(bool);   // slot 293
    virtual SInt32 setRunningState(bool);   // slot 294
    virtual IOReturn handleChosenMedia(UInt);   // slot 295
    virtual void * getSupportedMediaArray(UInt*, UInt*);   // slot 296
    virtual void * getPacketTapInfo(UInt*, UInt*);   // slot 297
    virtual UInt getUnsentDataByteCount(UInt*, UInt*, UInt) const;   // slot 298
    virtual UInt32 getSupportedWakeFlags(UInt*);   // slot 299
    virtual void enableNetworkWake(UInt);   // slot 300
    virtual void calculateRingSizeForQueue(IOSkywalkPacketQueue const*, UInt*) const;   // slot 301
    virtual UInt getMaxTransferUnit();   // slot 302
    virtual void setMaxTransferUnit(UInt);   // slot 303
    virtual UInt getMinPacketSize();   // slot 304
    virtual UInt getHardwareAssists();   // slot 305
    virtual void setHardwareAssists(UInt, UInt);   // slot 306
    virtual void * getInterfaceFamily();   // slot 307
    virtual void * getInterfaceSubFamily();   // slot 308
    virtual UInt getInitialMedia();   // slot 309
    virtual UInt32 getFeatureFlags();   // slot 310
    virtual UInt getTxDataOffset();   // slot 311
    virtual UInt captureInterfaceState(UInt);   // slot 312
    virtual void restoreInterfaceState(UInt);   // slot 313
    virtual void setMTU(UInt);   // slot 314
    virtual bool bpfTap(UInt, UInt);   // slot 315
    virtual const char * getBSDNamePrefix();   // slot 316
    virtual UInt getBSDUnitNumber();   // slot 317
    virtual const char * classNameOverride();   // slot 318
    virtual void deferBSDAttach(bool);   // slot 319
    virtual void reportDetailedLinkStatus(if_link_status const*);   // slot 320
    virtual UInt getTSOOptions(IOSkywalkNetworkInterface::IOSkywalkTSOOptions*);   // slot 321
    virtual void _RESERVEDIOSkywalkNetworkInterface0();
    virtual void _RESERVEDIOSkywalkNetworkInterface1();
    virtual void _RESERVEDIOSkywalkNetworkInterface2();
    virtual void _RESERVEDIOSkywalkNetworkInterface3();
    virtual void _RESERVEDIOSkywalkNetworkInterface4();
    virtual void _RESERVEDIOSkywalkNetworkInterface5();
    virtual void _RESERVEDIOSkywalkNetworkInterface6();
    virtual void _RESERVEDIOSkywalkNetworkInterface7();
    virtual void _RESERVEDIOSkywalkNetworkInterface8();
    virtual void _RESERVEDIOSkywalkNetworkInterface9();
