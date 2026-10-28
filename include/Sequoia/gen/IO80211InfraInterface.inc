// slots 460..464 из vtable Sequoia
    virtual bool init() APPLE_KEXT_OVERRIDE;   // override slot 17
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual IOReturn configureReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 133
    virtual IOReturn updateReport(IOReportChannelList*, UInt, void*, void*) APPLE_KEXT_OVERRIDE;   // override slot 134
    virtual bool start(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 184
    virtual void stop(IOService*) APPLE_KEXT_OVERRIDE;   // override slot 185
    virtual IOReturn setPowerState(unsigned long, IOService*) APPLE_KEXT_OVERRIDE;   // override slot 253
    virtual SInt32 initBSDInterfaceParameters(ifnet_init_eparams*, sockaddr_dl**) APPLE_KEXT_OVERRIDE;   // override slot 284
    virtual bool prepareBSDInterface(__ifnet*, UInt) APPLE_KEXT_OVERRIDE;   // override slot 285
    virtual IOReturn processBSDCommand(__ifnet*, UInt, void*) APPLE_KEXT_OVERRIDE;   // override slot 290
    virtual SInt32 setInterfaceEnable(bool) APPLE_KEXT_OVERRIDE;   // override slot 293
    virtual UInt getHardwareAssists() APPLE_KEXT_OVERRIDE;   // override slot 305
    virtual bool bpfTap(UInt, UInt) APPLE_KEXT_OVERRIDE;   // override slot 315
    virtual void hwConfigNicProxyData(nicproxy_info_s*) APPLE_KEXT_OVERRIDE;   // override slot 340
    virtual void postMessage(UInt, void*, unsigned long, bool) APPLE_KEXT_OVERRIDE;   // override slot 354
    virtual IOReturn recordOutputPackets(TxSubmissionDequeueStats*, TxSubmissionDequeueStats*) APPLE_KEXT_OVERRIDE;   // override slot 356
    virtual void logTxPacket(IO80211NetworkPacket*, PacketSkywalkScratch*, apple80211_wme_ac, bool) APPLE_KEXT_OVERRIDE;   // override slot 358
    virtual void logTxCompletionPacket(IO80211NetworkPacket*, PacketSkywalkScratch*, unsigned char*, apple80211_wme_ac, int, UInt, bool, bool) APPLE_KEXT_OVERRIDE;   // override slot 359
    virtual IOReturn recordCompletionPackets(TxCompletionEnqueueStats*, TxCompletionEnqueueStats*) APPLE_KEXT_OVERRIDE;   // override slot 360
    virtual IOReturn inputPacket(IO80211NetworkPacket*, packet_info_tag*, ether_header*, bool*, bool) APPLE_KEXT_OVERRIDE;   // override slot 361
    virtual SInt64 pendingPackets(unsigned char) APPLE_KEXT_OVERRIDE;   // override slot 364
    virtual SInt64 packetSpace(unsigned char) APPLE_KEXT_OVERRIDE;   // override slot 365
    virtual bool isDebounceOnGoing() APPLE_KEXT_OVERRIDE;   // override slot 367
    virtual bool setLinkState(IO80211LinkState, UInt, bool, UInt) APPLE_KEXT_OVERRIDE;   // override slot 368
    virtual IO80211LinkState linkState() APPLE_KEXT_OVERRIDE;   // override slot 369
    virtual void setScanningState(UInt, bool, apple80211_scan_data*, int) APPLE_KEXT_OVERRIDE;   // override slot 370
    virtual void setDataPathState(bool) APPLE_KEXT_OVERRIDE;   // override slot 371
    virtual void * getScanManager() APPLE_KEXT_OVERRIDE;   // override slot 372
    virtual void updateLinkParameters(apple80211_interface_availability*) APPLE_KEXT_OVERRIDE;   // override slot 374
    virtual void updateInterfaceCoexRiskPct(UInt64) APPLE_KEXT_OVERRIDE;   // override slot 375
    virtual void setLQM(UInt64) APPLE_KEXT_OVERRIDE;   // override slot 376
    virtual void updateLinkStatus() APPLE_KEXT_OVERRIDE;   // override slot 377
    virtual void updateLinkStatusGated() APPLE_KEXT_OVERRIDE;   // override slot 378
    virtual void setInterfaceExtendedCCA(apple80211_channel, apple80211_cca_report*) APPLE_KEXT_OVERRIDE;   // override slot 379
    virtual void setInterfaceCCA(apple80211_channel, int) APPLE_KEXT_OVERRIDE;   // override slot 380
    virtual void setInterfaceNF(apple80211_channel, long long) APPLE_KEXT_OVERRIDE;   // override slot 381
    virtual void setInterfaceOFDMDesense(apple80211_channel, long long) APPLE_KEXT_OVERRIDE;   // override slot 382
    virtual void setDebugFlags(UInt64, UInt) APPLE_KEXT_OVERRIDE;   // override slot 384
    virtual SInt64 debugFlags() APPLE_KEXT_OVERRIDE;   // override slot 385
    virtual void setInterfaceChipCounters(apple80211_stat_report*, apple80211_chip_counters_tx*, apple80211_chip_error_counters_tx*, apple80211_chip_counters_rx*) APPLE_KEXT_OVERRIDE;   // override slot 386
    virtual void setInterfaceMIBdot11(apple80211_stat_report*, apple80211_ManagementInformationBasedot11_counters*) APPLE_KEXT_OVERRIDE;   // override slot 387
    virtual void setFrameStats(apple80211_stat_report*, apple80211_frame_counters*) APPLE_KEXT_OVERRIDE;   // override slot 388
    virtual void setInfraSpecificFrameStats(apple80211_stat_report*, apple80211_infra_specific_stats*) APPLE_KEXT_OVERRIDE;   // override slot 389
    virtual SInt64 getWmeTxCounters(UInt64*) APPLE_KEXT_OVERRIDE;   // override slot 390
    virtual void setPeerManagerLogFlag(UInt, UInt, UInt) APPLE_KEXT_OVERRIDE;   // override slot 391
    virtual void setWoWEnabled(bool) APPLE_KEXT_OVERRIDE;   // override slot 392
    virtual bool wowEnabled() APPLE_KEXT_OVERRIDE;   // override slot 393
    virtual UInt64 createLinkQualityMonitor(IO80211Peer*, IOService*) APPLE_KEXT_OVERRIDE;   // override slot 405
    virtual void releaseLinkQualityMonitor(IO80211Peer*) APPLE_KEXT_OVERRIDE;   // override slot 406
    virtual int getAssocState() APPLE_KEXT_OVERRIDE;   // override slot 427
    virtual void * getLQMSummary(apple80211_lqm_summary*) APPLE_KEXT_OVERRIDE;   // override slot 438
    virtual IOReturn setLinkStateInternal(IO80211LinkState, UInt, bool, UInt);   // slot 460
    virtual IOReturn setCurrentApAddress(ether_addr*);   // slot 461
    virtual void setWCL_ADVISORTY_INFO(apple80211_wcl_advisory_info*);   // slot 462
    virtual void * getWCL_TX_RX_LATENCY(apple80211_wcl_tx_rx_latency*);   // slot 463
    virtual IOReturn createLQMData();   // slot 464
