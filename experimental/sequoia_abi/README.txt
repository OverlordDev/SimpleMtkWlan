Реальный ABI IO80211Family на этой Sequoia (15.8.1, com.apple.iokit.IO80211Family 1200.13.1)
Получен 2026-10-10 прямо из /System/Library/KernelCollections/BootKernelExtensions.kc.

  vtable_dump.py <symbols.txt> <класс...>   читает vtable класса из KC (chained fixups: low 30 bit + база KC)
  symbols.txt = nm -gU по BootKernelExtensions.kc (строки "адрес тип имя")
  vtables_IO80211_IOSkywalk_*.txt           IO80211SkywalkInterface, IO80211InfraInterface, IO80211Controller,
                                            IOSkywalkNetworkInterface, IOSkywalkEthernetInterface
  vtables_AppleBCMWLANCore_*.txt            эталонный драйвер Apple: какие слоты и с какими сигнатурами он переопределяет

Главный вывод: заголовки референса (itlwm, цель __MAC_14_4) НЕ соответствуют Sequoia 15.8.1:
  - IO80211Controller: нет apple80211_ioctl*, apple80211VirtualRequest, apple80211SkywalkRequest,
    getHardwareAddressForInterface, useAppleRSNSupplicant, setVirtualHardwareAddress, postMessage(uint,...);
    добавлены debugStateInit, getPLATFORM_CONFIG, getLogger(const), allocIO80211RecursiveLock, getPostOffice и др.
    -> порядок слотов vtable другой, переопределения попали бы не в те слоты (паника).
  - IO80211SkywalkInterface: нет setEnabledBySystem/enabledBySystem/willRoam/setSelfMacAddr/getCurrentBssid,
    сигнатуры findOrCreateFlowQueue(IO80211FlowQueueHash), setLinkStateInternal без event_data, getBSDInterface const и т.д.
  - IO80211Interface (старый класс) в Sequoia отсутствует вообще.

(В репозитории нет сырых дампов vtable/дизассемблера из ядра Apple. Их можно воссоздать на своей системе:
 nm -gU /System/Library/KernelCollections/BootKernelExtensions.kc > bkc_exported_symbols.txt, затем vtable_dump.py / gen_headers.py.)
