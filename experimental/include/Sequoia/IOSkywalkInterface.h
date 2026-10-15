// Sequoia 15.8.1: IOSkywalkInterface (класс 0xb0 байт). Слоты из vtable ядра.
#ifndef IOSkywalkInterface_h
#define IOSkywalkInterface_h
#include <IOKit/IOService.h>
class IOSkywalkInterface : public IOService {
    OSDeclareAbstractStructors(IOSkywalkInterface)
public:
#include "gen/IOSkywalkInterface.inc"
protected:
    uint8_t _abi_pad_IOSkywalkInterface[0xb0 - sizeof(IOService)];
};
static_assert(sizeof(IOSkywalkInterface) == 0xb0, "IOSkywalkInterface size");
#endif
