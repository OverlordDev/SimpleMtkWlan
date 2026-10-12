// slots 332..351 из vtable Sequoia
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual bool init(OSDictionary*) APPLE_KEXT_OVERRIDE;   // override slot 73
    virtual IOReturn newUserClient(task*, void*, UInt, OSDictionary*, IOUserClient**) APPLE_KEXT_OVERRIDE;   // override slot 238
    virtual IOReturn setPowerState(unsigned long, IOService*) APPLE_KEXT_OVERRIDE;   // override slot 253
    virtual IOReturn enable(UInt) APPLE_KEXT_OVERRIDE;   // override slot 266
    virtual SInt32 initBSDInterfaceParameters(ifnet_init_eparams*, sockaddr_dl**) APPLE_KEXT_OVERRIDE;   // override slot 284
    virtual bool prepareBSDInterface(__ifnet*, UInt) APPLE_KEXT_OVERRIDE;   // override slot 285
    virtual IOReturn processBSDCommand(__ifnet*, UInt, void*) APPLE_KEXT_OVERRIDE;   // override slot 290
    virtual void * getPacketTapInfo(UInt*, UInt*) APPLE_KEXT_OVERRIDE;   // override slot 297
    virtual void enableNetworkWake(UInt) APPLE_KEXT_OVERRIDE;   // override slot 300
    virtual UInt getMaxTransferUnit() APPLE_KEXT_OVERRIDE;   // override slot 302
    virtual UInt getMinPacketSize() APPLE_KEXT_OVERRIDE;   // override slot 304
    virtual void * getInterfaceFamily() APPLE_KEXT_OVERRIDE;   // override slot 307
    virtual void * getInterfaceSubFamily() APPLE_KEXT_OVERRIDE;   // override slot 308
    virtual UInt getInitialMedia() APPLE_KEXT_OVERRIDE;   // override slot 309
    virtual const char * getBSDNamePrefix() APPLE_KEXT_OVERRIDE;   // override slot 316
    virtual void getHardwareAddress(ether_addr*);   // slot 332
    virtual void setHardwareAddress(ether_addr*);   // slot 333
    virtual void setLinkLayerAddress(ether_addr*);   // slot 334
    virtual bool configureMulticastFilter(UInt, ether_addr const*, UInt);   // slot 335
    virtual bool setMulticastAddresses(ether_addr const*, UInt);   // slot 336
    virtual void setAllMulticastModeEnable(bool);   // slot 337
    virtual IOReturn setPromiscuousModeEnable(bool, UInt);   // slot 338
    virtual void reportNicProxyLimits(nicproxy_limits_info_s);   // slot 339
    virtual void hwConfigNicProxyData(nicproxy_info_s*);   // slot 340
    virtual void _RESERVEDIOSkywalkEthernetInterface0();
    virtual void _RESERVEDIOSkywalkEthernetInterface1();
    virtual void _RESERVEDIOSkywalkEthernetInterface2();
    virtual void _RESERVEDIOSkywalkEthernetInterface3();
    virtual void _RESERVEDIOSkywalkEthernetInterface4();
    virtual void _RESERVEDIOSkywalkEthernetInterface5();
    virtual void _RESERVEDIOSkywalkEthernetInterface6();
    virtual void _RESERVEDIOSkywalkEthernetInterface7();
    virtual void _RESERVEDIOSkywalkEthernetInterface8();
    virtual void _RESERVEDIOSkywalkEthernetInterface9();
    virtual void _RESERVEDIOSkywalkEthernetInterface10();
