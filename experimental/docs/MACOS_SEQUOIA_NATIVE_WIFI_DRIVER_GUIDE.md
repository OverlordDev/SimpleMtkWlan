# Нативный Wi-Fi драйвер под macOS Sequoia 15.x: что нужно знать и сделать

Руководство собрано по двум репозиториям:

- **Рабочий референс (Intel):** <https://github.com/laobamac/itlwm>, ветка `main`, цель `AirportItlwm-Sequoia`
  (коммит `897c7f4` «Add native AirportItlwm support for macOS Sequoia 15.2+», релиз `v2.4.0-alpha`).
- **Нерабочий порт (MediaTek):** <https://github.com/OverlordDev/SimpleMtkWlan>, каталог `experimental/AirportMtkWlan`.

Цель: чтобы карта появилась в штатном меню Wi-Fi macOS без HeliPort, то есть как «родная» Apple-карта.

---

## 0. Как читать этот документ

| Метка | Значение |
|---|---|
| **[КОД]** | прочитано в исходниках референса, подтверждено строкой кода или `static_assert` |
| **[README]** | со слов README/форума, мной не проверялось |
| **[ВЫВОД]** | моё заключение из сравнения, на железе не проверено |

**Что я не делал:** не собирал, не запускал, не дизассемблировал ядро Sequoia, не видел ни одного panic-лога. Всё про
«почему падает» в разделе 14 — [ВЫВОД]. Весь протокол (раздел 8–10) — [КОД], но это поведение одного драйвера (Intel),
не спецификация Apple: Apple ничего из этого не документирует.

Лицензия: оба проекта GPL-2.0, код OpenBSD/NetBSD/FreeBSD внутри сохраняет свои уведомления. Переносить код из референса —
значит оставаться под GPLv2.

---

## 1. Что такое «нативный» драйвер и чем он отличается от itlwm + HeliPort

| | itlwm (+ HeliPort) | AirportItlwm / AirportXxx (нативное меню) |
|---|---|---|
| Базовый класс | `IOEthernetController` | `IO80211Controller` (из `IO80211Family`) |
| Что видит macOS | обычный Ethernet-интерфейс `en*` | Wi-Fi интерфейс (`IO80211InfraInterface` + Skywalk) |
| Кто управляет сетью | своё приложение через user client | CoreWLAN / `airportd` / WiFi-агенты Apple, через Family |
| Что должен делать драйвер | net80211 + ioctl своего клиента | отвечать на запросы Family (`apple80211`/WCL) и слать ей события |
| Зависимости kext | IONetworking, IOPCI | + `IO80211Family`, `IOSkywalkFamily`, `corecapture` |

Следствие: нативный драйвер не «подключается к Wi-Fi сам». Он реализует **интерфейс, который ждёт Family**, а решение
«что сканировать, куда подключаться» принимает macOS.

На Sequoia это сделано новым слоем **WCL** (имена вида `setWCL_SCAN_REQ`, `setWCL_ASSOCIATE`, `getWCL_BSS_INFO`,
`WCLNetManager::handleLqmUpdate` в комментариях референса). Старая модель (`getSCAN_RESULT`, `setASSOCIATE`, события
`APPLE80211_M_*`) из Sonoma на Sequoia 15.2+ не ведёт к рабочему меню — см. раздел 14.

---

## 2. Предусловия: платформа, сборка, запуск

### 2.1 Версии ОС

- **[README]** Sequoia-цель: «Use this kext only on Darwin 24.2.0–24.99.99», то есть macOS 15.2 и новее, проверено на 15.8 (24H23), x86_64.
- **[КОД]** в `start()` стоит явная проверка:
  ```cpp
  #if __IO80211_TARGET == __MAC_15_2
      if (version_major != 24 || version_minor < 2) return false;
  #endif
  ```
- Sonoma-сборка на Sequoia не подходит, и наоборот (отдельные заголовки ABI в `include/Airport/macOS15/`, отзыв на форуме InsanelyMac).

### 2.2 Сборка (референс)

- Xcode, Python 3, `MacKernelSDK` (Acidanthera) строго на коммите `3f750085caa17ec3a7880f11c11bf4f48cd6a164` в `MacKernelSDK/`.
- Команда [README]:
  ```sh
  xcodebuild -project itlwm.xcodeproj -scheme AirportItlwm-Sequoia \
    -configuration Release ARCHS=x86_64 CODE_SIGNING_ALLOWED=NO build
  ```
- Макросы препроцессора для Sequoia-цели [КОД, `project.pbxproj` в коммите `9bc4b4d`]:
  `AIRPORT`, `AIRPORT_WCL`, `AIRPORT_VTD`, `__IO80211_TARGET=__MAC_15_2`, `__PRIVATE_SPI__`.
- `PrivateSPI.pch` определяет недостающие константы доступности: `__MAC_15_2 = 150200`, `__MAC_26_0 = 260000` и др.
  Без `__IO80211_TARGET` заголовок падает с `#error "Please define __IO80211_TARGET..."`.
- SimpleMtkWlan собирается clang-only скриптами без Xcode: `sequoia_build/build.sh` (Ethernet-вариант) и
  `experimental/build_airport.sh` (нативный). **[КОД]** `build_airport.sh` компилирует с `-D__IO80211_TARGET=__MAC_14_4`,
  `-DIO80211FAMILY_V2`, `-DAIRPORT`, `-D__PRIVATE_SPI__`; макросов `AIRPORT_WCL` и `AIRPORT_VTD` в нём нет, цель — 14.4, а не 15.2.
  Свои заголовки скрипт копирует поверх `include/Airport/` (`cp -R include/Sequoia/. include/Airport/`).

### 2.3 Загрузка

- Kext в `EFI/OC/Kexts`, запись в `Kernel → Add`, в `Info.plist` `OSBundleRequired = Network-Root` [КОД].
- Загружается в boot kernel collection. Поэтому при падении ядро умирает до того, как диск доступен: panic-лог не сохраняется
  (то самое «no panic report survives» из README SimpleMtkWlan).
- Если одна конфигурация OpenCore используется для Sequoia и Tahoe, kext каждой системы ограничивают по версии Darwin [README].
- Не загружать одновременно itlwm и AirportItlwm (общая рекомендация сообщества, [README] общей документации).

### 2.4 Boot-аргументы и настройки платформы

| Параметр | Откуда | Что делает |
|---|---|---|
| `itlwm_he=1` | [КОД] | включает HE (Wi-Fi 6), по умолчанию выключено |
| `-novht`, `-noht40` | [КОД] | отключают VHT / HT40 на стороне драйвера |
| `DisableIOMapper` (OpenCore quirk) | [README, форум] | нужен ряду пользователей, пока драйвер не использует DMA через IOMapper; см. раздел 11 |
| `keepsyms=1 debug=0x100 -v` | общие boot-args macOS | символы в бектрейсе и вывод; не из референса |

---

## 3. Архитектура: какие классы и зачем

```
IOPCIDevice  (Apple, провайдер)
  └─ IOPCIEDeviceWrapper : IOService          ← personality "itlwm" (матчинг по PCI ID)
       │   probe(): включает MSI, определяет модель, создаёт HAL (ItlIwx/ItlIwm/ItlIwn либо MtkMwx)
       │   start(): _fWorkloop = IO80211WorkQueue::workQueue(); PMinit; registerPowerDriver; registerService
       └─ AirportItlwm : IO80211Controller    ← personality "NetworkController" (IOProviderClass = IOPCIEDeviceWrapper)
            │   владеет: HAL, command gate, watchdog, CC-логгеры, BSD-интерфейсом
            ├─ AirportItlwmSkywalkInterface : IO80211InfraProtocol    ← интерфейс для Family (WCL команды, события)
            └─ AirportItlwmEthernetInterface : IOEthernetInterface    ← BSD-интерфейс en*, пакеты, ifnet
```

Принципиальные моменты:

- **Двухступенчатый матчинг.** Wrapper нужен, потому что `IO80211WorkQueue` и power management надо создать до контроллера,
  а контроллер матчится на wrapper (`IOMatchCategory = WiFiDriver`, `IONetworkRootType = airport`, `IOResourceMatch = IOBSD`).
- **Рабочая очередь одна.** Wrapper создаёт `IO80211WorkQueue`; контроллер возвращает её из `getWorkLoop()`, `getWorkQueue()`
  и создаёт `IOCommandGate` на ней. Любые обращения в Family должны идти внутри этого gate (раздел 7).
- **Два объекта-интерфейса.** Skywalk-интерфейс — то, что видит Family. Ethernet-интерфейс — то, что видит BSD/сетевой стек,
  и он «подменяет» своего провайдера на Skywalk-интерфейс (раздел 6).

---

## 4. `Info.plist` (рабочий образец)

**[КОД]** `AirportItlwm/WCL/Sequoia-Info.plist`. Два personality:

```xml
<key>IOKitPersonalities</key>
<dict>
  <key>NetworkController</key>
  <dict>
    <key>CFBundleIdentifier</key>  <string>com.zxystd.AirportItlwm</string>
    <key>IOClass</key>             <string>AirportItlwm</string>
    <key>IOMatchCategory</key>     <string>WiFiDriver</string>
    <key>IONetworkRootType</key>   <string>airport</string>
    <key>IOProbeScore</key>        <integer>70000</integer>
    <key>IOProviderClass</key>     <string>IOPCIEDeviceWrapper</string>
    <key>IOResourceMatch</key>     <string>IOBSD</string>
  </dict>
  <key>itlwm</key>
  <dict>
    <key>CFBundleIdentifier</key>  <string>com.zxystd.AirportItlwm</string>
    <key>IOClass</key>             <string>IOPCIEDeviceWrapper</string>
    <key>IOPCIMatch</key>          <string>0x27238086 0x43F08086 ...</string>
    <key>IOProbeScore</key>        <integer>70000</integer>
    <key>IOProviderClass</key>     <string>IOPCIDevice</string>
  </dict>
</dict>
<key>OSBundleLibraries</key>
<dict>
  <key>com.apple.driver.corecapture</key>        <string>1.0.0</string>
  <key>com.apple.iokit.IO80211Family</key>       <string>1.5.0</string>
  <key>com.apple.iokit.IONetworkingFamily</key>  <string>3.2</string>
  <key>com.apple.iokit.IOPCIFamily</key>         <string>2.9</string>
  <key>com.apple.iokit.IOSkywalkFamily</key>     <string>1.0</string>
  <key>com.apple.kpi.bsd</key>     <string>16.7</string>
  <key>com.apple.kpi.iokit</key>   <string>16.7</string>
  <key>com.apple.kpi.libkern</key> <string>16.7</string>
  <key>com.apple.kpi.mach</key>    <string>16.7</string>
</dict>
<key>OSBundleRequired</key> <string>Network-Root</string>
```

Для MediaTek: `IOPCIMatch = 0x796114c3 0x060814c3 0x792214c3` (так уже в `experimental/AirportMtkWlan/Info.plist`).
Этот файл у порта **совпадает** с референсом, причина падения не в матчинге.

---

## 5. ABI Sequoia: размеры и смещения (то, без чего код молча портит память)

Заголовки Apple для этих классов недоступны. Референс держит собственные копии в `include/Airport/macOS15/`,
порт — свои, сгенерированные из KC (`experimental/include/Sequoia/`). Сверка **[КОД]**:

| Класс | `sizeof` | Смещение / примечание |
|---|---|---|
| `IOSkywalkInterface` | `0xb0` | |
| `IOSkywalkNetworkInterface` | `0xd0` | `mExpansionData` по `0xb8` |
| `IOSkywalkEthernetInterface` | `0x110` | `mExpansionData2` по `0x108` |
| `IO80211SkywalkInterface` | `0x118` | |
| `IO80211InfraInterface` | `0x120` | |
| `IO80211InfraProtocol` | `0x120` | assert только в порте; в референсе отдельного assert не нашёл |
| `IO80211Controller` | `0x128` | |
| `IO80211WorkQueue` | `0x50` | |

Структуры регистрации:

```cpp
struct RegistrationInfo { uint8_t bytes[0x130]; };            // Network и Ethernet версии одинаковы
struct ExpansionData   { RegistrationInfo *fRegistrationInfo; ifnet_t fBSDInterface; };
```

Остальное:

- **Слоты vtable.** `IO80211Controller` (слоты 394–462), `IO80211InfraInterface` (460–464), `IO80211InfraProtocol` (465–654, **190 чисто
  виртуальных**). Порядок и сигнатуры обязаны совпадать с ядром. В порте они сгенерированы из `BootKernelExtensions.kc`:
  `nm -gU <kc>`, затем `sequoia_abi/vtable_dump.py`, `gen_headers.py`, проверка `check_vtable.py`.
- **Приватные слоты Controller** (`debugStateInit`, `getPLATFORM_CONFIG`, `allocIO80211RecursiveLock`, `getActionFramePoolCapacity`,
  `getPostOffice`, `CreatePostOffice`) в референсе объявлены `private` с `__asm__("<mangled>")`, чтобы занять слот без реализации.
- **Заголовки Sonoma (14.4) не совпадают с 15.x:** нет `apple80211_ioctl*`, `apple80211SkywalkRequest`, `useAppleRSNSupplicant`;
  сменились сигнатуры `findOrCreateFlowQueue`, `setLinkStateInternal`; старый `IO80211Interface` исчез [КОД, `sequoia_abi/README.txt`].

Любой `static_assert` по размеру/смещению должен быть в вашем коде: без него ошибка проявится как произвольный краш внутри Apple-кода.

---

## 6. Порядок `start()` — рабочий вариант

Скелет по `AirportItlwmV2.cpp::start()` (ветка `AIRPORT_WCL`) [КОД]. Номера шагов мои.

1. **Гейт ОС:** `version_major == 24 && version_minor >= 2`, иначе `return false`.
2. Свойства: `built-in = 0` (`OSData` из одного байта), `DriverKitDriver = false`.
3. **`initCCLogs()` до `super::start()`** (раздел 6.1).
4. `super::start(provider)` (`IO80211Controller::start`).
5. PCI: `setBusMasterEnable/IOEnable/MemoryEnable`, `configWrite8(0x41, 0)`, `requestPowerDomainState`, `initPCIPowerManagment`.
6. `_fCommandGate = IOCommandGate::commandGate(this, tsleepHandler)`; `_fWorkloop->addEventSource(_fCommandGate)`.
7. `createMediumTables`, `setCurrentMedium`, `setSelectedMedium` (`kIOMediumIEEE80211`, `kIOMediumIEEE80211None`).
8. `fHalService->initWithController(this, _fWorkloop, _fCommandGate)`; `ic_event_handler = eventHandler`; boot-args (`-novht`, `-noht40`, `itlwm_he`).
9. `fHalService->attach(pciNub)` — загрузка прошивки, MAC, каналы.
10. Watchdog (`IOWorkLoop` + `IOTimerEventSource`, период 1000 мс), `scanSource` на `_fWorkloop`.
11. `fNetIf = new AirportItlwmSkywalkInterface; fNetIf->init(this)` — внутри **обязательно две инициализации** (раздел 6.2).
12. `fNetIf->setInterfaceRole(1); setInterfaceId(1);`
13. `fNetIf->attach(this)`.
14. `attachInterface(fNetIf, this)` — метод Family.
15. `IONetworkController::attachInterface((IONetworkInterface **)&bsdInterface, false)` — **`false`**: регистрация откладывается.
16. `memset(&registInfo, 0, sizeof); fNetIf->initRegistrationInfo(&registInfo, 1, sizeof(registInfo))`.
17. **Заполнить `ExpansionData`** (раздел 6.3) и `fNetIf->deferBSDAttach(true)` при роли 1.
18. `fNetIf->start(this)`; при `false` — `super::stop`, `releaseAll`, `return false`.
19. `setLinkStatus(kIONetworkLinkValid)`; если нет сохранённых ESS — `ic_flags |= IEEE80211_F_AUTO_JOIN`.
20. `bsdInterface->registerService(); registerService();`

### 6.1 `initCCLogs()` — точная последовательность [КОД]

Эти три pipe-а + логгер + fault reporter Family требует **до** `IO80211Controller::start()`. Пропуск → паника ядра.

```cpp
driverLogPipe = CCPipe::withOwnerNameCapacity(this, "<bundle id>", "DriverLogs", &opts);   // pipe_type 0, log_data_type 1, pipe_size 0x200000
driverLogPipeStarted = driverLogPipe->CCPipe::startPipe();     // ВАЖНО: фабрика только инициализирует, startPipe создаёт event sources
CCStream *logger = CCStream::withPipeAndName(driverLogPipe, "<name>", &loggerOptions);
driverLogger = OSDynamicCast(CCLogStream, logger);             // отдаётся из getLogger()

driverDataPathPipe  = CCPipe::withOwnerNameCapacity(..., "DatapathEvents", ...);  driverDataPathPipe->CCPipe::startPipe();
driverSnapshotsPipe = CCPipe::withOwnerNameCapacity(..., "StateSnapshots", ...);  driverSnapshotsPipe->CCPipe::startPipe();

CCStreamOptions fault = {}; fault.stream_type = 1; fault.console_level = 0xFFFFFFFFFFFFFFFF;
driverFaultStream = CCStream::withPipeAndName(driverSnapshotsPipe, "FaultReporter", &fault);
CCDataStream *ds  = OSDynamicCast(CCDataStream, driverFaultStream);
driverCoreFaultReporter = CCFaultReporter::withStreamWorkloop(ds, _fWorkloop);
driverFaultReporter     = IO80211FaultReporter::allocWithParams(driverCoreFaultReporter);   // ОБЁРТКА
if (!OSDynamicCast(CommonFaultReporter, driverFaultReporter)) return false;
```

- `getFaultReporterFromDriver()` возвращает именно **`CommonFaultReporter*`** (результат `IO80211FaultReporter::allocWithParams`), а не «сырой»
  `CCFaultReporter`.
- `getLogger() const` возвращает `CCLogStream*`; `getLogPipes(CCPipe**, CCPipe**, CCPipe**)` отдаёт три pipe-а.
- `CCPipe::startPipe` вызывается с явной квалификацией класса: иначе диспетчеризация идёт через устаревший заголовок CCPipe.

### 6.2 `AirportItlwmSkywalkInterface::init(IOService *provider)` [КОД]

```cpp
bool ret = IO80211InfraInterface::init();          // 1) база
instance = OSDynamicCast(AirportItlwm, provider);
fHalService = instance->fHalService; scanSource = instance->scanSource;
IOEthernetAddress address;
if (instance->getHardwareAddress(&address) != kIOReturnSuccess) return false;   // MAC уже должен быть известен
if (!IO80211SkywalkInterface::init(provider, (ether_addr *)&address)) return false;  // 2) ВТОРАЯ инициализация, с MAC
if (!initWCL()) return false;                      // таймер join на instance->getWorkQueue()
```

Именно две инициализации. `IO80211SkywalkInterface::init(IOService*, ether_addr*)` — отдельный виртуальный слот (412).

### 6.3 Заполнение `ExpansionData` (причина «краш в `IOSkywalk*::start`»)

```cpp
fNetIf->mExpansionData ->fRegistrationInfo = (IOSkywalkNetworkInterface::RegistrationInfo  *)IOMalloc(sizeof(...));
fNetIf->mExpansionData2->fRegistrationInfo = (IOSkywalkEthernetInterface::RegistrationInfo *)IOMalloc(sizeof(...));
if (!fNetIf->mExpansionData->fRegistrationInfo || !fNetIf->mExpansionData2->fRegistrationInfo) → fail
memcpy(fNetIf->mExpansionData ->fRegistrationInfo, &registInfo, sizeof(registInfo));
memcpy(fNetIf->mExpansionData2->fRegistrationInfo, &registInfo, sizeof(registInfo));
```

Это ручная замена вызову `registerEthernetInterface(...)`. Без неё `start()` Skywalk-интерфейса читает NULL.
Для этого в заголовках должны быть настоящие поля `mExpansionData` (`+0xb8`) и `mExpansionData2` (`+0x108`), а не `_abi_pad`.

---

## 7. Рабочая очередь и gate: что и откуда можно вызывать

**[КОД]** Во всех местах WCL-кода есть проверки `queue->inGate()` и `!queue->onThread()`. Правила, которые из них следуют:

- Любой вызов в Family (`postMessage`, `setLinkState`, `prepareBSDInterface`, `setLQM`) выполняется **внутри gate** `IO80211WorkQueue`.
- Внешние вызовы (прошивка, `systq`, IRQ) в gate не находятся. Их переводят `_fCommandGate->runAction(wclCommand, this, code, arg)`.
- Из gate запрещено делать синхронные WCL-вызовы и выполнять работу на «своём» потоке очереди (`onThread()`), иначе
  `kIOReturnNotPermitted` или deadlock.
- События, идущие из прошивки в момент init (`DRIVER_RESET_BEGIN`, `DRIVER_READY`, `DRIVER_STOPPED`), могут прийти вне gate:
  их надо сериализовать через `runAction`, остальные события обрабатываются напрямую.
- Закрытие: `stopWCL()` ставит `wclStopping = true` под gate, отменяет таймеры, зануляет PSK (`explicit_bzero`).

Контроллер:

```cpp
bool            createWorkQueue()                { return _fWorkloop != 0; }
IOWorkLoop     *getWorkLoop() const              { return _fWorkloop; }       // в WCL-сборке переопределён
IO80211WorkQueue *getWorkQueue() const           { return _fWorkloop; }
```

`_fWorkloop` создаёт wrapper (`IO80211WorkQueue::workQueue()`), это глобальный указатель драйвера.

---

## 8. BSD-интерфейс (`IOEthernetInterface`-подкласс) [КОД]

```cpp
attachToDataLinkLayer(opts, param):
    if (!setInterfaceSubType(3)) return kIOReturnNotReady;     // Sequoia/Tahoe: обязательно до super
    ret = super::attachToDataLinkLayer(opts, param);
    interface->setProperty("built-in", 0), "IOInterfaceName" = "<name><unit>", kIOInterfaceUnit, kIOInterfaceNamePrefix
    setProperty(kIOMACAddress, ...)
    ret = _fCommandGate->runAction(prepareBSDGated, this);     // внутри: queue->inGate() && !queue->onThread()
                                                               //         interface->prepareBSDInterface(getIfnet(), 0)
    isAttach = true; interface->registerService();

getProvider() const  { return isAttach ? interface : super::getProvider(); }   // анти-паника SkywalkFamily
setLinkState(state)  { ifnet_set_flags(IFF_UP|IFF_RUNNING) ...  }
```

- `getProvider()` подменяется на Skywalk-интерфейс, чтобы приведение типов внутри `IOSkywalkFamily` не паниковало.
- `inputPacket`: перед передачей в сетевой стек приводить mbuf к линейному (`ETHER_ALIGN`, один сегмент), иначе повреждения на
  приёме (коммит `cad1841` «Fix receive mbuf ownership and Skywalk packet handling»).
- `createInterface()` контроллера возвращает этот подкласс (`initWithSkywalkInterfaceAndProvider(this, fNetIf)`).

---

## 9. Обязательные ответы контроллера и интерфейса

### 9.1 Контроллер (`IO80211Controller`)

Чисто виртуальные, обязаны быть реализованы: `isCommandProhibited(int)`, `handleCardSpecific(...)`, `getDRIVER_VERSION`,
`getHARDWARE_VERSION`, `getCARD_CAPABILITIES`, `getPOWER`, `setPOWER`, `getCOUNTRY_CODE`, `setCOUNTRY_CODE`,
`setGET_DEBUG_INFO`, `getLogger() const`, `getFaultReporterFromDriver()`.

Сопутствующие переопределения референса: `createWorkQueue`, `getWorkQueue`, `monitorModeSetEnabled` (вернуть 0),
`requiresExplicitMBufRelease` / `flowIdSupported` (оба `false`), `requestQueueSizeAndTimeout`, `enableFeature`,
`getLogPipes`, `newVendorString`, `newModelString`, `getFeatures`, `setHardwareAddress`, `getHardwareAddress`,
`outputPacket`, `outputStart` (`__PRIVATE_SPI__`).

### 9.2 `getCARD_CAPABILITIES` в WCL-сборке [КОД]

Байты `capabilities[]` (`apple80211_capability_data`), как в референсе для Sequoia:

| Байт | Значение |
|---|---|
| `[0]` | `AES_CCM` и `TKIP`, только при `IEEE80211_C_RSN` (TKIP как групповой шифр, иначе Apple отвергает WPA2-сети с TKIP-group) |
| `[1]` | `SHSLOT`, `SHPREAMBLE`, `WPA2`, `TKIPMIC`; **бит WPA1 снят** |
| `[2]` | `WME`, `SHORT_GI_40MHZ`, `SHORT_GI_20MHZ` |
| `[5]` | `0x40` — «Scan completion events» |
| `[17]` бит 7 | HE (`WCLDeviceConfiguration::isHeSupported`), только при `IEEE80211_C_HE` |

Не заявлять то, чего драйвер не умеет: WPA3 в Sonoma-версии подменялся на WPA2, в WCL версии для WPA2/WPA3-transition
выбирается WPA2-PSK (`selectWPA2TransitionMode`, коммит `a9d1ba9`).

### 9.3 `IO80211InfraProtocol` — 190 слотов

Большая часть возвращает `kIOReturnUnsupported`. **[КОД]** реально реализуются в референсе (по `WCL.cpp` и `AirportItlwmSkywalkInterface.cpp`):

| Группа | Методы |
|---|---|
| Скан | `setWCL_SCAN_REQ`, `setWCL_SCAN_ABORT`, `setWCL_SET_SCAN_HOME_AWAY_TIME` |
| Подключение | `setWCL_ASSOCIATE`, `setWCL_JOIN_ABORT`, `setWCL_LEAVE_NETWORK`, `setWCL_LINK_STATE_UPDATE`, `setWCL_UPDATE_FAST_LANE` |
| Сведения о сети | `getWCL_BSS_INFO`, `getWCL_EXTENDED_BSS_INFO`, `getBEACON_INFO`, `getWCL_LOW_LATENCY_INFO` |
| Каналы | `getWCL_CHANNELS_INFO`, `getCHANNELS_INFO`, `getWCL_VALID_CHANNEL_COUNT` |
| Статистика | `getWCL_TRAFFIC_COUNTERS` |
| Ключи/RSN | `installWCLKey`, `accessWCLRSN` (get/set), `setCLEAR_PMKSA_CACHE` |
| MAC | `getHW_ADDR`, `setMacAddress` (`ether_addr&` на 15.2, `mloAddrArray&` на новее) |

Метод `setWCL_JOIN_ABORT` на 15.2 имеет сигнатуру `(void*)`, на новее — `(apple80211_wcl_abort_join*)`:
под `__IO80211_TARGET` нужны ветки `#if`.

Все такие вызовы пробрасываются в один диспетчер `wclCommand(...)` через `_fCommandGate->runAction` (коды команд 0–15 внутри референса).

---

## 10. Протокол WCL: сканирование, подключение, события

### 10.1 События драйвер → Family

Единственный способ: `instance->postMessage(interface, code, data, size, true)` (метод контроллера
`IOReturn postMessage(IO80211SkywalkInterface*, unsigned, void*, unsigned long, bool)`). **[КОД]** коды и структуры:

| Код | Имя | Структура (размер) | Когда |
|---|---|---|---|
| 49 | `ResetInterface` | `uint32` (0 — начало, 1 — готово) | сброс адаптера |
| 55 | `DriverAvailable` | `DriverAvailability` (`0xf8`; `version=3`, `available`, `reason`) | прошивка готова/остановлена |
| 39 | `LqmUpdate` | 15.2: `SequoiaLqmUpdate` (`0x150`, `rssiValid`, `rssi@4`); новее: `LqmBeaconUpdate` (`0x1dc`) | раз в 8 маяков в состоянии «подключён» |
| 201 | `ScanResult` | `BeaconMetadata` (`0x40` на 15.2, `0x44` новее) + IE | каждый найденный BSS |
| 203 | `Deauth` | `DeauthEvent` (`0x14`) | деаутентификация |
| 211 | `AssocComplete` | `AssociationEvent` (`0x1c`) | ассоциация завершена (status ≠ 0 — ошибка) |
| 212 | `FirstBeacon` | `FirstBeaconEvent` (`0x14`) | первый маяк после ассоциации |
| 213 | `ConnectComplete` | `ConnectionEvent` (`0xa4`) | итог подключения |
| 214 | `JoinAbortComplete` | — | отмена join |
| 216 | `LinkStatus` | `LinkStatusEvent` (16, `up@6`) | линк up/down |
| 237 | `ScanDone` | `IOReturn` | скан завершён (4 байта) |

Поля в `BeaconMetadata`: `ieLength`, `channelSpec` (`канал | 0xd000` для 5 ГГц, `| 0x1000` для 2.4), `ssid[32]`, `ssidLength`,
`channel`, `bssid[6]` (по смещению `0x29`), `rssi` (`0x30`), `noise`, `snr`, `interval`, `capability`, `flags`
(`SSIDPresent = 1<<1`, `RSSIValid = 1<<14`; на 15.2 по `0x3c`, на новее по `0x40`). Дальше сами IE.

### 10.2 Запрос скана Family → драйвер

`setWCL_SCAN_REQ(apple80211ScanRequest*)` — буфер **`0x1550` байт**, декодер в референсе:

| Смещение | Поле |
|---|---|
| `0x00` | `identifier` |
| `0x14` | `bssid[6]` |
| `0x1c` | `ssidLength` |
| `0x20` | `ssid[32]` |
| `0x40` | `type` (1..4; `2` — пассивный скан) |
| `0x54` | `channelCount` (≤ 400) |
| `0x58` | массив `apple80211_channel` по 12 байт: `version`, `channel`, `flags` |

Правила из референса:
- `type == 2` ⇒ SSID не используется, скан без probe-запросов.
- Флаги канала: `0x8` — только 2.4, `0x10` — только 5, `0x2000` — 6 ГГц (пропускается).
- Пока идёт скан/join или ассоциация — вернуть `kIOReturnBusy`; если `IFF_RUNNING` нет — `kIOReturnNotReady`.
- В `RUN` скан делается как фоновый (`ieee80211_begin_cache_bgscan`), иначе `ic_newstate(IEEE80211_S_SCAN)`.
- Таймаут скана 20 с на `scanSource`; завершение — `ScanDone` через `postMessage`.

### 10.3 Подключение

`setWCL_ASSOCIATE(apple80211AssocCandidates*)` — декодер ожидает буфер не короче `0x218` байт:

| Смещение | Поле |
|---|---|
| `0x1c` | `ssidLength` |
| `0x44` | `keyLength` (≤ 32) |
| `0xd4` | `rsnLength` (u16, ≤ 257) |
| `0x214` | `count` кандидатов (1..10) |
| `0x21c` | первый кандидат: `bssid[6]` и дальше, шаг 18 байт |

Классификация аутентификации (`lowerAuth` должен быть `1`):
`upperAuth == 0` — Open или WEP (длина ключа 5 или 13); WPA/WPA2-Personal — ключ 32 байта (PMK, шифр 6 или 7);
Enterprise — ключ либо отсутствует, либо PMK 32 байта; смесь Personal+Enterprise — ошибка.
RSN-override (`rsn[]`) допустим только как RSN IE (id 48, версия 1) или WPA IE (id 221, OUI `00:50:f2`, тип 1).

Последовательность событий (в `handleWCLEvent`):

```
setWCL_ASSOCIATE  → join в net80211 (ic_wcl_join_requested), joinTimer
STA_ASSOC_DONE    → AssocComplete (status = ic_assoc_status); при ошибке → finishJoin
BEACON (BSSID=joinBSSID, первый) → LinkStatus(up=1) + FirstBeacon
port authorized   → finishWCLJoin(0,0) → ConnectComplete
STA_DEAUTH        → Deauth + finishJoin(1, reason)
setWCL_LEAVE_NETWORK / JOIN_ABORT → leaveWCLNetwork / abortWCLJoin (+ JoinAbortComplete)
```

PTK/GTK драйвер не принимает: на Sequoia ключи устанавливаются самим net80211 драйвера (в `installWCLKey` валидируются
только PMK/MSK, шифры 6/7/9, длина 32).

### 10.4 Ответы на запросы состояния

- `getWCL_CHANNELS_INFO` / `getCHANNELS_INFO`: структура `NativeChannelInfo` (`0x2720`; `country@8`, `count@0xc`,
  `channelSpec@0xe`, `channel@0x32e`, `indoor@0x4be`, `dfs@0x64e`, `passive@0x7de`, `supports40MHz@0x96e`, `supports80MHz@0xafe`).
- `getWCL_BSS_INFO` / `getBEACON_INFO`: отдают последний маяк подключённого BSS (с растущим TSF). Family опрашивает
  `BEACON_INFO`, чтобы отличить живой приём от «залипшей» записи.
- `getWCL_TRAFFIC_COUNTERS`: `TrafficCounters` (`0x38`, `timestampNanoseconds@0x30`).
- `getHW_ADDR`: `HardwareAddress` (12 байт: `version=1`, `address@4`).

---

## 11. Качество линка (`setLQM`): без этого не работают iMessage/FaceTime/AirDrop

**[КОД]** Каждые N маяков и при смене состояния вызывается (под gate):

```cpp
quality = -2;                                                    // нет данных
if (portAuthorized && linkState()==Up && IFF_UP|IFF_RUNNING && ic_state==RUN && bssid==joinBSSID) {
    rssi = IWM_MIN_DBM + ni_rssi;
    quality = rssi >= -70 ? 100 : (rssi >= -85 ? 50 : 20);
}
setLQM((unsigned long long)(long long)quality);
```

Коммит `a01d1d5` «Fix WCL link quality reporting for iServices». Параллельно шлётся `LqmUpdate` (раздел 10.1). Вторичный источник
(`hackdoc/15test`, [README]): без `setLQM` ключ `State:/Network/Interface/<if>/LinkQuality` остаётся «no signal», `apsd` отвергает интерфейс.

---

## 12. DMA и VT-d (AppleVTD)

**[README, форум]** на Sequoia/Tahoe без DisableIOMapper работает только сборка с обработкой IOMapper (AppleVTD),
**[КОД]** это `itl80211/ItlDma.cpp` + `AIRPORT_VTD`.

Суть, как сделано в референсе:

- `owner->setProperty("IOPCIUseDeviceMapper", true)`, `device->open(owner)`.
- `mapper = IOMapper::copyMapperForDevice(device)`; если нет — `IOMapper::gSystem`; если у устройства есть `iommu-parent`, а
  mapper не найден — ошибка. Режимы пишутся в свойство `ItlwmDMAMapper`: `device` / `system` / `direct`.
- Память: `IOBufferMemoryDescriptor::inTaskWithPhysicalMask(kernel_task, kIODirectionInOut | kIOMemoryHostPhysicallyContiguous | kIOMemoryMapperNone, BlockSize, mask)`.
- Адреса для карты — не `getPhysicalAddress()`, а IOVA из `IODMACommand::withSpecification(kIODMACommandOutputHost64, bits, ..., mapper)` +
  `gen64IOVMSegments`; проверки: один сегмент, выравнивание страницы, адрес ≤ `bits` (36 или 64).
- Пул блоков (`BlockCount = 32`), аллокатор по страницам, **отложенное освобождение**: после остановки шины (`reclaim()` проверяет
  `kIOPCICommandBusMaster`), чтобы карта не обратилась в уже освобождённую область.

У SimpleMtkWlan [КОД, `compat.cpp`] DMA сделан через `IOBufferMemoryDescriptor` и `getPhysicalAddress()` — адреса «физические».
При включённом VT-d это даёт DMA-ошибки; обход: `DisableIOMapper`.

---

## 13. Питание, прерывания, watchdog

- Wrapper регистрирует power driver (`PMinit`, `registerPowerDriver` на 2 состояния, `joinPMtree`) — **до** старта контроллера.
- Контроллер: `registerWithPolicyMaker`, `setPowerState`, `setWakeOnMagicPacket`, потоки включения/выключения
  (`powerOnThreadCall` / `powerOffThreadCall`).
- MSI включается в `probe()` wrapper (MSI-X отключается), без MSI/MSI-X устройство отвергается.
- Watchdog 1 с (`kWatchDogTimerPeriod = 1000`), на своём `IOWorkLoop`.

---

## 14. SimpleMtkWlan: что отличается от рабочей Sequoia-сборки

Сверено построчно по `AirportMtkWlan.cpp/.hpp`, `AirportMtkWlanSkywalkInterface.cpp/.hpp`, `IOPCIEDeviceWrapper.*`,
`AirportMtkWlanEthernetInterface.cpp`, `compat.cpp`, `MtkMwx.cpp`. Приоритет [ВЫВОД].

### 14.1 Причины падения в `IO80211InfraInterface::start`

| # | Отличие | Референс | Порт |
|---|---|---|---|
| 1 | `ExpansionData` перед `start()` | заполняются `mExpansionData*` (+0xb8/+0x108), `RegistrationInfo` = `0x130` | только `initRegistrationInfo` на локальной переменной; полей в заголовках нет (`_abi_pad`) |
| 2 | Двойная инициализация интерфейса | `IO80211InfraInterface::init()` **и** `IO80211SkywalkInterface::init(provider, &mac)` | только `IO80211InfraInterface::init()` |
| 3 | `startPipe()` для трёх CCPipe | вызывается для каждого | нет ни одного вызова `startPipe` |
| 4 | Fault reporter | `IO80211FaultReporter::allocWithParams(CCFaultReporter)`, проверка `CommonFaultReporter` | возвращается «сырой» `CCFaultReporter` (`IO80211FaultReporter` в заголовках отсутствует) |
| 5 | `getWorkLoop() const` | переопределён, возвращает `_fWorkloop` (wrapper) | не переопределён в контроллере |
| 6 | Регистрация BSD | `attachInterface(&bsdInterface, false)` + `bsdInterface->registerService()` в конце | `attachInterface(..., true)` |
| 7 | Вызов `fNetIf->start()` | синхронно в `start()`, при `false` — откат | через `thread_call` с задержкой 90 с (`MtkDelaySec`), результат не проверяется |
| 8 | Ethernet-интерфейс | `setInterfaceSubType(3)`, `prepareBSDInterface` под gate | вызывается напрямую, без gate, без `setInterfaceSubType` |
| 9a | Флаги сборки | `__IO80211_TARGET=__MAC_15_2`, `AIRPORT_WCL`, `AIRPORT_VTD` | `__IO80211_TARGET=__MAC_14_4`, без `AIRPORT_WCL`/`AIRPORT_VTD` |

Эти отличия не взаимоисключающие: первые четыре — прямые кандидаты на NULL-разыменование внутри Apple-кода.
Какая именно сработала, без panic-лога сказать нельзя.

### 14.2 Что не будет работать, даже если `start` пройдёт

| # | Что | Почему |
|---|---|---|
| 9 | Протокол WCL | в порте нет `setWCL_SCAN_REQ/ASSOCIATE/…`, события шлются старыми `APPLE80211_M_*` через `fNetIf->postMessage(...)`. Sequoia WCL их не использует |
| 10 | Сообщения 49/55/201/211–216/237 | не отправляются, меню не получит ни скан-листа, ни статуса линка |
| 11 | Capabilities | байты Sonoma (`[2]=0xFF`, `[3]=0x2B`, `[6]=0xC`…), а не WCL-набор из раздела 9.2 |
| 12 | `enable()` | в порте `enableFromInterface` — обычный метод, никто его не вызывает |
| 13 | LQM | нет `setLQM`/`LqmUpdate` ⇒ iServices отвергает интерфейс |
| 14 | DMA | физические адреса, не IOMapper ⇒ нужен `DisableIOMapper` |
| 15 | `getFaultReporterFromDriver()` тип | см. пункт 4 |

---

## 15. Порядок работ

1. **Подключить рабочие заголовки.** Взять `include/Airport/macOS15/*` (GPLv2) или сверить сгенерированные из KC с ними.
   Должны совпасть размеры и смещения из раздела 5; добавить `static_assert` на них.
2. **Довести `start()`** до раздела 6 (пункты 14.1 №1–8). Без задержки `thread_call`, с проверкой результата `fNetIf->start()`.
3. **Бисекция по `MtkStage`** (уже есть в порте): после правок сначала «стадия 7» (всё до `fNetIf->start()`), затем сам `start`.
   Раздел 16 — как получить бектрейс.
4. **Показать интерфейс системе:** `Wi-Fi` в `networksetup -listallhardwareports`, `ifconfig`, `ioreg -l -w0 | grep -i airport`.
5. **Реализовать WCL минимум:** `getCARD_CAPABILITIES` (раздел 9.2), `getWCL_CHANNELS_INFO`, `setWCL_SCAN_REQ` + `ScanResult`/`ScanDone`,
   `getWCL_BSS_INFO`. На этом шаге в меню должен появиться список сетей.
6. **Подключение:** `setWCL_ASSOCIATE` + события 211/212/216/213, затем пакеты.
7. **LQM** (раздел 11) — чтобы работали сервисы Apple.
8. **VT-d** (раздел 12) — убрать зависимость от `DisableIOMapper`.
9. После этого — шифры (WPA3 и MFP в референсе не поддерживаются), HE, AWDL (в референсе не поддерживаются).

---

## 16. Отладка

- **Пока нет панического лога:** `keepsyms=1 debug=0x100 -v`, фото экрана/serial. По бектрейсу видно функцию Apple и
  адрес сбоя: малое значение (`0x0–0x1ff`) указывает на NULL-поле.
- **Бисекция запуска:** свойство `MtkStage` в личности (уже реализовано в порте), `MtkDelaySec=0`.
- **Диагностика в ioreg:** референс публикует `ItlwmDMARevision`, `ItlwmDMAMapper`, `ItlwmDMAAddressBits`, `ItlwmDMAPoolBytes`;
  порт — `MtkLog`, `MtkHB` (в `-diag` сборке).
- **Свой лог-кольцо:** порт уже содержит `mtk_ringlog_start/stop`.
- **Проверка слотов:** `vtable_dump.py` по `IO80211InfraProtocol` и классу интерфейса Apple (`AppleBCMWLANCore`) +
  `check_vtable.py` против собранного kext.
- **Что смотреть в бектрейсе:** если падение в `IOSkywalkEthernetInterface::start` / `IOSkywalkNetworkInterface::start` —
  раздел 6.3; в `IO80211InfraInterface::start` — 6.2 / 6.1; в `CCPipe`/`CCStream`/`CCLogStream` — 6.1.

---

## 17. Неизвестное и непроверенное

- Точное содержимое `IO80211InfraInterface::start` / `IOSkywalk*::start` на Sequoia 15.8 — не дизассемблировал.
- Смещения `0xb8`, `0x108` и размер `0x130` взяты из заголовков референса, который, по README, работает на 15.8. Для других
  минорных версий 15.x не проверялись.
- `IO80211InfraProtocol` `sizeof == 0x120` — assert только в порте.
- Остальные группы `getWCL_*`/`setWCL_*`, которые референс оставляет в `kIOReturnUnsupported`, могут потребоваться
  функциям, не проверенным мной (roaming, background scan, FastLane).
- Тайминги и поведение при глубоком сне, WoW, P2P/AWDL — вне исследования.
- Все «работает» — со слов README и форума InsanelyMac, не из моего запуска.

---

## 18. Ссылки

- laobamac/itlwm: <https://github.com/laobamac/itlwm> — `AirportItlwm/AirportItlwmV2.cpp`, `AirportItlwm/WCL/WCL.{cpp,hpp}`,
  `AirportItlwm/AirportItlwmSkywalkInterface.{cpp,hpp}`, `AirportItlwm/AirportItlwmEthernetInterface.cpp`,
  `AirportItlwm/IOPCIEDeviceWrapper.*`, `AirportItlwm/WCL/Sequoia-Info.plist`, `include/Airport/macOS15/*`, `itl80211/ItlDma.*`.
- OpenIntelWireless/itlwm (апстрим): <https://github.com/OpenIntelWireless/itlwm> — Sonoma-эталон `AirportItlwmV2.cpp`.
- OverlordDev/SimpleMtkWlan: <https://github.com/OverlordDev/SimpleMtkWlan> — `experimental/AirportMtkWlan`, `experimental/sequoia_abi`.
- InsanelyMac, обсуждение Sequoia/Tahoe: <https://www.insanelymac.com/forum/topic/363312-airportitlwm-for-macos-sequoia-and-tahoe/>.
- hackdoc/15test (форк про iServices и `setLQM`): <https://github.com/hackdoc/15test>.
- Black Hat USA 2020, «Dive into Apple IO80211FamilyV2»: <https://i.blackhat.com/USA-20/Thursday/us-20-Wang-Dive-into-Apple-IO80211FamilyV2.pdf>.
- Acidanthera MacKernelSDK: <https://github.com/acidanthera/MacKernelSDK>.
