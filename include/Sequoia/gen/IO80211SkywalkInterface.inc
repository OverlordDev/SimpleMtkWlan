// slots 352..459 из vtable Sequoia
    virtual bool init() APPLE_KEXT_OVERRIDE;   // override slot 17
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual IOReturn configureReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 133
    virtual IOReturn updateReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 134
    virtual bool start(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 184
    virtual void stop(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 185
    virtual IOReturn newUserClient(task*, void*, UInt, OSDictionary*, IOUserClient**) APPLE_KEXT_OVERRIDE;   // override slot 238
    virtual const char * stringFromReturn(int) APPLE_KEXT_OVERRIDE;   // override slot 240
    virtual int errnoFromReturn(int) APPLE_KEXT_OVERRIDE;   // override slot 241
    virtual IOReturn setPowerState(unsigned long, IOService*) APPLE_KEXT_OVERRIDE;   // override slot 253
    virtual unsigned long maxCapabilityForDomainState(unsigned long) APPLE_KEXT_OVERRIDE;   // override slot 254
    virtual unsigned long initialPowerStateForDomainState(unsigned long) APPLE_KEXT_OVERRIDE;   // override slot 255
    virtual IOReturn enable(UInt) APPLE_KEXT_OVERRIDE;   // override slot 266
    virtual IOReturn disable(UInt) APPLE_KEXT_OVERRIDE;   // override slot 267
    virtual SInt32 initBSDInterfaceParameters(ifnet_init_eparams*, sockaddr_dl**) APPLE_KEXT_OVERRIDE;   // override slot 284
    virtual bool prepareBSDInterface(__ifnet*, UInt) APPLE_KEXT_OVERRIDE;   // override slot 285
    virtual IOReturn processBSDCommand(__ifnet*, UInt, void*) APPLE_KEXT_OVERRIDE;   // override slot 290
    virtual SInt32 setInterfaceEnable(bool) APPLE_KEXT_OVERRIDE;   // override slot 293
    virtual SInt32 setRunningState(bool) APPLE_KEXT_OVERRIDE;   // override slot 294
    virtual IOReturn handleChosenMedia(UInt) APPLE_KEXT_OVERRIDE;   // override slot 295
    virtual void * getSupportedMediaArray(UInt*, UInt*) APPLE_KEXT_OVERRIDE;   // override slot 296
    virtual UInt32 getFeatureFlags() APPLE_KEXT_OVERRIDE;   // override slot 310
    virtual const char * classNameOverride() APPLE_KEXT_OVERRIDE;   // override slot 318
    virtual void getHardwareAddress(ether_addr*) APPLE_KEXT_OVERRIDE;   // override slot 332
    virtual void setHardwareAddress(ether_addr*) APPLE_KEXT_OVERRIDE;   // override slot 333
    virtual IOReturn setPromiscuousModeEnable(bool, UInt) APPLE_KEXT_OVERRIDE;   // override slot 338
    virtual void * createPeerManager();   // slot 352
    virtual IOReturn createPeer(unsigned char const*, IO80211PeerManager*);   // slot 353
    virtual void postMessage(UInt, void*, unsigned long, bool);   // slot 354
    virtual IOReturn reportDataPathEvents(UInt, void*, unsigned long, bool);   // slot 355
    virtual IOReturn recordOutputPackets(TxSubmissionDequeueStats*, TxSubmissionDequeueStats*);   // slot 356
    virtual IOReturn recordOutputPacket(apple80211_wme_ac, int, int);   // slot 357
    virtual void logTxPacket(IO80211NetworkPacket*, PacketSkywalkScratch*, apple80211_wme_ac, bool);   // slot 358
    virtual void logTxCompletionPacket(IO80211NetworkPacket*, PacketSkywalkScratch*, unsigned char*, apple80211_wme_ac, int, UInt, bool, bool);   // slot 359
    virtual IOReturn recordCompletionPackets(TxCompletionEnqueueStats*, TxCompletionEnqueueStats*);   // slot 360
    virtual IOReturn inputPacket(IO80211NetworkPacket*, packet_info_tag*, ether_header*, bool*, bool);   // slot 361
    virtual IOReturn forwardInfraRelayPackets(IO80211NetworkPacket*, ether_header*);   // slot 362
    virtual void logSkywalkTxReqPacket(IO80211NetworkPacket*, PacketSkywalkScratch*, unsigned char*, apple80211_wme_ac, bool);   // slot 363
    virtual SInt64 pendingPackets(unsigned char);   // slot 364
    virtual SInt64 packetSpace(unsigned char);   // slot 365
    virtual bool isChipInterfaceReady();   // slot 366
    virtual bool isDebounceOnGoing();   // slot 367
    virtual bool setLinkState(IO80211LinkState, UInt, bool, UInt);   // slot 368
    virtual IO80211LinkState linkState();   // slot 369
    virtual void setScanningState(UInt, bool, apple80211_scan_data*, int);   // slot 370
    virtual void setDataPathState(bool);   // slot 371
    virtual void * getScanManager();   // slot 372
    virtual IOReturn getController();   // slot 373
    virtual void updateLinkParameters(apple80211_interface_availability*);   // slot 374
    virtual void updateInterfaceCoexRiskPct(UInt64);   // slot 375
    virtual void setLQM(UInt64);   // slot 376
    virtual void updateLinkStatus();   // slot 377
    virtual void updateLinkStatusGated();   // slot 378
    virtual void setInterfaceExtendedCCA(apple80211_channel, apple80211_cca_report*);   // slot 379
    virtual void setInterfaceCCA(apple80211_channel, int);   // slot 380
    virtual void setInterfaceNF(apple80211_channel, long long);   // slot 381
    virtual void setInterfaceOFDMDesense(apple80211_channel, long long);   // slot 382
    virtual void removePacketQueue(IO80211FlowQueueHash*);   // slot 383
    virtual void setDebugFlags(UInt64, UInt);   // slot 384
    virtual SInt64 debugFlags();   // slot 385
    virtual void setInterfaceChipCounters(apple80211_stat_report*, apple80211_chip_counters_tx*, apple80211_chip_error_counters_tx*, apple80211_chip_counters_rx*);   // slot 386
    virtual void setInterfaceMIBdot11(apple80211_stat_report*, apple80211_ManagementInformationBasedot11_counters*);   // slot 387
    virtual void setFrameStats(apple80211_stat_report*, apple80211_frame_counters*);   // slot 388
    virtual void setInfraSpecificFrameStats(apple80211_stat_report*, apple80211_infra_specific_stats*);   // slot 389
    virtual SInt64 getWmeTxCounters(UInt64*);   // slot 390
    virtual void setPeerManagerLogFlag(UInt, UInt, UInt);   // slot 391
    virtual void setWoWEnabled(bool);   // slot 392
    virtual bool wowEnabled();   // slot 393
    virtual void printDataPath(userPrintCtx*);   // slot 394
    virtual UInt32 getDataQueueDepth();   // slot 395
    virtual bool findOrCreateFlowQueue(IO80211FlowQueueHash);   // slot 396
    virtual UInt64 findOrCreateFlowQueueWithCache(IO80211FlowQueueHash, bool*);   // slot 397
    virtual UInt64 findExistingFlowQueue(IO80211FlowQueueHash);   // slot 398
    virtual void removePacketQueue(IO80211FlowQueueHash const*);   // slot 399
    virtual void flushPacketQueues();   // slot 400
    virtual void cachePeer(ether_addr*, UInt*);   // slot 401
    virtual bool shouldLog(UInt64);   // slot 402
    virtual void vlogDebug(UInt64, char const*, va_list);   // slot 403
    virtual void vlogDebugBPF(UInt64, char const*, va_list);   // slot 404
    virtual UInt64 createLinkQualityMonitor(IO80211Peer*, IOService*);   // slot 405
    virtual void releaseLinkQualityMonitor(IO80211Peer*);   // slot 406
    virtual void * getP2PSkywalkPeerMgr();   // slot 407
    virtual bool isCommandProhibited(int);   // slot 408
    virtual IOReturn findPeer(ether_addr&);   // slot 409
    virtual void setNotificationProperty(OSSymbol const*, OSObject const*);   // slot 410
    virtual void * getWorkerMatchingDict(OSString*);   // slot 411
    virtual bool init(IOService*, ether_addr*);   // slot 412
    virtual bool isInterfaceEnabled();   // slot 413
    virtual ether_addr * getSelfMacAddr();   // slot 414
    virtual IOReturn setMacAddress(ether_addr&) = 0;   // slot 415
    virtual void * getPacketPool(OSString*);   // slot 416
    virtual void * getLogger() const;   // slot 417
    virtual IOReturn handleSIOCSIFADDR();   // slot 418
    virtual IOReturn debugHandler(apple80211_debug_command*);   // slot 419
    virtual void statsDump();   // slot 420
    virtual void powerOnNotification();   // slot 421
    virtual void powerOffNotification();   // slot 422
    virtual UInt64 getTxQueueDepth();   // slot 423
    virtual UInt64 getRxQueueCapacity();   // slot 424
    virtual void updateRxCounter(UInt64);   // slot 425
    virtual void * getMultiCastQueue();   // slot 426
    virtual int getAssocState();   // slot 427
    virtual void notifyQueueState(apple80211_wme_ac, unsigned short);   // slot 428
    virtual int getTxHeadroom();   // slot 429
    virtual void * getRxCompQueue();   // slot 430
    virtual void * getTxCompQueue();   // slot 431
    virtual void * getTxSubQueue(apple80211_wme_ac);   // slot 432
    virtual void * getTxPacketPool();   // slot 433
    virtual void * getRxPacketPool();   // slot 434
    virtual void enableDatapath();   // slot 435
    virtual void disableDatapath();   // slot 436
    virtual int getNumTxQueues();   // slot 437
    virtual void * getLQMSummary(apple80211_lqm_summary*);   // slot 438
    virtual int getEventPipeSize();   // slot 439
    virtual UInt64 createEventPipe(IO80211APIUserClient*);   // slot 440
    virtual void destroyEventPipe(IO80211APIUserClient*);   // slot 441
    virtual IOReturn setUserBufferInfo(IOMemoryDescriptor*, UInt64);   // slot 442
    virtual void postMessageIOUC(char const*, UInt, void*, unsigned long);   // slot 443
    virtual bool isIOUCPipeOpened();   // slot 444
    virtual void * getRingMD(IO80211APIUserClient*, UInt64);   // slot 445
    virtual IOReturn attachPeer(ether_addr*);   // slot 446
    virtual IOReturn detachPeer(ether_addr*);   // slot 447
    virtual IOReturn setDebugTrafficReport(bool);   // slot 448
    virtual IOReturn getDataPathInterfaceStats(apple80211_data_path_interface_stats*);   // slot 449
    virtual IOReturn getDataPathPeerStats(apple80211_data_path_peer_stats*);   // slot 450
    virtual IOReturn getLastQueuePacketTime(ether_addr*);   // slot 451
    virtual IOReturn getLastRxUnicastLinkActivityTime(ether_addr*);   // slot 452
    virtual IOReturn updateInterfaceDataStats(apple80211_data_path_interface_stats*);   // slot 453
    virtual IOReturn updatePeerDataStats(apple80211_data_path_peer_stats*);   // slot 454
    virtual IOReturn logTxLatency(unsigned char*, UInt, UInt64);   // slot 455
    virtual IOReturn logRxLatency(UInt, UInt64);   // slot 456
    virtual IOReturn getNClearTxRxLatency(apple80211_latency_all_ac*, apple80211_latency_all_ac*);   // slot 457
    virtual IOReturn getLastTxTimeStamp(UInt64&);   // slot 458
    virtual IOReturn getLastRxTimeStamp(UInt64&);   // slot 459
