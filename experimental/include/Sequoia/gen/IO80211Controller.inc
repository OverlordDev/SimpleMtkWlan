// slots 394..462 из vtable Sequoia
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual bool init(OSDictionary*) APPLE_KEXT_OVERRIDE;   // override slot 73
    virtual IOReturn configureReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 133
    virtual IOReturn updateReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 134
    virtual bool start(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 184
    virtual void stop(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 185
    virtual IOWorkLoop * getWorkLoop() const APPLE_KEXT_OVERRIDE;   // override slot 209
    virtual const char * stringFromReturn(int) APPLE_KEXT_OVERRIDE;   // override slot 240
    virtual int errnoFromReturn(int) APPLE_KEXT_OVERRIDE;   // override slot 241
    virtual UInt32 getFeatures() const APPLE_KEXT_OVERRIDE;   // override slot 268
    virtual const OSString * newVendorString() const APPLE_KEXT_OVERRIDE;   // override slot 269
    virtual const OSString * newModelString() const APPLE_KEXT_OVERRIDE;   // override slot 270
    virtual bool createWorkLoop() APPLE_KEXT_OVERRIDE;   // override slot 306
    virtual IOReturn getHardwareAddress(IOEthernetAddress*) APPLE_KEXT_OVERRIDE;   // override slot 356
    virtual IOReturn setMulticastMode(bool) APPLE_KEXT_OVERRIDE;   // override slot 358
    virtual IOReturn setPromiscuousMode(bool) APPLE_KEXT_OVERRIDE;   // override slot 360
    virtual bool isCommandProhibited(int) = 0;   // slot 394
    virtual bool createWorkQueue();   // slot 395
    virtual IOReturn debugStateInit();   // slot 396
    virtual IO80211WorkQueue * getWorkQueue() const;   // slot 397
    virtual void requestPacketTx(void*, UInt);   // slot 398
    virtual IOCommandGate * getIO80211CommandGate() const;   // slot 399
    virtual IO80211SkywalkInterface * getPrimarySkywalkInterface();   // slot 400
    virtual int bpfOutputPacket(OSObject*, UInt, __mbuf*);   // slot 401
    virtual SInt32 monitorModeSetEnabled(bool, UInt);   // slot 402
    virtual SInt32 handleCardSpecific(IO80211SkywalkInterface*, unsigned long, void*, bool) = 0;   // slot 403
    virtual UInt32 hardwareOutputQueueDepth();   // slot 404
    virtual SInt32 performCountryCodeOperation(IO80211CountryCodeOp);   // slot 405
    virtual void dataLinkLayerAttachComplete();   // slot 406
    virtual SInt32 enableFeature(IO80211FeatureCode, void*);   // slot 407
    virtual IOReturn getDRIVER_VERSION(IO80211SkywalkInterface*, apple80211_version_data*) = 0;   // slot 408
    virtual IOReturn getHARDWARE_VERSION(IO80211SkywalkInterface*, apple80211_version_data*) = 0;   // slot 409
    virtual IOReturn getCARD_CAPABILITIES(IO80211SkywalkInterface*, apple80211_capability_data*) = 0;   // slot 410
    virtual IOReturn getPOWER(IO80211SkywalkInterface*, apple80211_power_data*) = 0;   // slot 411
    virtual IOReturn setPOWER(IO80211SkywalkInterface*, apple80211_power_data*) = 0;   // slot 412
    virtual IOReturn getCOUNTRY_CODE(IO80211SkywalkInterface*, apple80211_country_code_data*) = 0;   // slot 413
    virtual IOReturn setCOUNTRY_CODE(IO80211SkywalkInterface*, apple80211_country_code_data*) = 0;   // slot 414
    virtual IOReturn setGET_DEBUG_INFO(IO80211SkywalkInterface*, apple80211_debug_command*) = 0;   // slot 415
    virtual IOReturn getPLATFORM_CONFIG(IO80211SkywalkInterface*, apple80211_platform_config*);   // slot 416
    virtual SInt32 enableVirtualInterface(IO80211VirtualInterface*);   // slot 417
    virtual SInt32 disableVirtualInterface(IO80211VirtualInterface*);   // slot 418
    virtual bool requiresExplicitMBufRelease();   // slot 419
    virtual bool flowIdSupported();   // slot 420
    virtual IO80211FlowQueueLegacy * requestFlowQueue(FlowIdMetadata const*);   // slot 421
    virtual void releaseFlowQueue(IO80211FlowQueue*);   // slot 422
    virtual bool getLogPipes(CCPipe**, CCPipe**, CCPipe**);   // slot 423
    virtual void * getLogger() const = 0;   // slot 424
    virtual void enableFeatureForLoggingFlags(UInt64);   // slot 425
    virtual IOReturn requestQueueSizeAndTimeout(unsigned short*, unsigned short*);   // slot 426
    virtual IOReturn enablePacketTimestamping();   // slot 427
    virtual IOReturn disablePacketTimestamping();   // slot 428
    virtual UInt getPacketTSCounter();   // slot 429
    virtual void * getDriverTextLog();   // slot 430
    virtual UInt32 selfDiagnosticsReport(int, char const*, UInt);   // slot 431
    virtual void * getFaultReporterFromDriver() = 0;   // slot 432
    virtual IOReturn allocIO80211RecursiveLock();   // slot 433
    virtual UInt32 getDataQueueDepth(OSObject*);   // slot 434
    virtual bool wasDynSARInFailSafeMode();   // slot 435
    virtual void updateAdvisoryScoresIfNeed();   // slot 436
    virtual UInt64 getAVCAdvisoryInfo(IO80211InterfaceAVCAdvisory*);   // slot 437
    virtual IOReturn getActionFramePoolCapacity();   // slot 438
    virtual IOReturn getPostOffice();   // slot 439
    virtual IOReturn CreatePostOffice();   // slot 440
    virtual bool attachInterface(OSObject*, IOService*);   // slot 441
    virtual void detachInterface(OSObject*, bool);   // slot 442
    virtual IO80211VirtualInterface * createVirtualInterface(ether_addr*, UInt);   // slot 443
    virtual bool attachVirtualInterface(IO80211VirtualInterface**, ether_addr*, UInt, bool);   // slot 444
    virtual bool detachVirtualInterface(IO80211VirtualInterface*, bool);   // slot 445
    virtual void _RESERVEDIO80211Controller0();
    virtual void _RESERVEDIO80211Controller1();
    virtual void _RESERVEDIO80211Controller2();
    virtual void _RESERVEDIO80211Controller3();
    virtual void _RESERVEDIO80211Controller4();
    virtual void _RESERVEDIO80211Controller5();
    virtual void _RESERVEDIO80211Controller6();
    virtual void _RESERVEDIO80211Controller7();
    virtual void _RESERVEDIO80211Controller8();
    virtual void _RESERVEDIO80211Controller9();
    virtual void _RESERVEDIO80211Controller10();
    virtual void _RESERVEDIO80211Controller11();
    virtual void _RESERVEDIO80211Controller12();
    virtual void _RESERVEDIO80211Controller13();
    virtual void _RESERVEDIO80211Controller14();
    virtual void _RESERVEDIO80211Controller15();
    virtual IOReturn setMulticastList(ether_addr const*, UInt);   // slot 462
