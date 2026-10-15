#include <IOKit/IOLib.h>
#include <IOKit/IOService.h>
#include <IOKit/network/IOEthernetController.h>
#include <Sequoia/Apple80211.h>

class ProbeInfra : public IO80211InfraProtocol {
    OSDeclareDefaultStructors(ProbeInfra)
public:
#include "gen/pure_decl_infra.inc"
};
class ProbeCtl : public IO80211Controller {
    OSDeclareDefaultStructors(ProbeCtl)
public:
#include "gen/pure_decl_controller.inc"
};
#include "pure_def_infra_p.inc"
#include "pure_def_ctl_p.inc"
OSDefineMetaClassAndStructors(ProbeInfra, IO80211InfraProtocol)
OSDefineMetaClassAndStructors(ProbeCtl, IO80211Controller)
