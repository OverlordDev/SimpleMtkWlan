// slots 266..281 из vtable Sequoia
    virtual void free() APPLE_KEXT_OVERRIDE;   // override slot 18
    virtual bool init(OSDictionary*) APPLE_KEXT_OVERRIDE;   // override slot 73
    virtual bool willTerminate(IOService*, UInt) APPLE_KEXT_OVERRIDE;   // override slot 128
    virtual bool didTerminate(IOService*, UInt, bool*) APPLE_KEXT_OVERRIDE;   // override slot 129
    virtual bool handleOpen(IOService*, UInt, void*) APPLE_KEXT_OVERRIDE;   // override slot 189
    virtual void handleClose(IOService*, UInt) APPLE_KEXT_OVERRIDE;   // override slot 190
    virtual bool handleIsOpen(IOService const*) const APPLE_KEXT_OVERRIDE;   // override slot 191
    virtual IOReturn enable(UInt) = 0;   // slot 266
    virtual IOReturn disable(UInt) = 0;   // slot 267
    virtual IOReturn clientConnectWithTask(task*, IOService*, UInt);   // slot 268
    virtual void clientDisconnect(IOService*, UInt);   // slot 269
    virtual bool isTerminating();   // slot 270
    virtual void _RESERVEDIOSkywalkInterface0();
    virtual void _RESERVEDIOSkywalkInterface1();
    virtual void _RESERVEDIOSkywalkInterface2();
    virtual void _RESERVEDIOSkywalkInterface3();
    virtual void _RESERVEDIOSkywalkInterface4();
    virtual void _RESERVEDIOSkywalkInterface5();
    virtual void _RESERVEDIOSkywalkInterface6();
    virtual void _RESERVEDIOSkywalkInterface7();
    virtual void _RESERVEDIOSkywalkInterface8();
    virtual void _RESERVEDIOSkywalkInterface9();
    virtual void _RESERVEDIOSkywalkInterface10();
