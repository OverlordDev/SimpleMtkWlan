# Передача: правки старта AirportMtkWlan под Sequoia (для Claude на macOS)

Репозиторий: <https://github.com/OverlordDev/SimpleMtkWlan>, база — коммит `a5cb94a`
(«Sequoia (macOS 15.x) port: fw chunk alloc fix, HT/VHT80 …»). Правки только в `experimental/`.
Цель: чтобы Skywalk-интерфейс Family стартовал без паники ядра и карта появилась как нативное Wi-Fi.

## 0. Что это и чего это НЕ делает

- Это набор исправлений **порядка и состава `start()`**, сверенных построчно с рабочей Sequoia-сборкой
  `laobamac/itlwm` (ветка `main`, цель `AirportItlwm-Sequoia`, 15.8 / 24H23, ветка `AIRPORT_WCL`).
- **Ни разу не компилировалось и не запускалось.** Проверено только статически скриптом
  `experimental/check_airport_start.py` (43 правила) и его самопроверкой на 13 намеренных поломках
  (`check_airport_start_selftest.py`, все 13 пойманы).
- Это **не** реализация протокола WCL: сканирование и подключение через меню Wi-Fi после этих правок всё ещё не
  заработают (раздел 6). Цель этой пачки — пережить `fNetIf->start()`.

## 1. Как применить

```bash
git clone https://github.com/OverlordDev/SimpleMtkWlan.git && cd SimpleMtkWlan
git checkout a5cb94a
git apply --check 0001-airport-sequoia-start-fixes.patch && git apply 0001-airport-sequoia-start-fixes.patch
python3 -I experimental/check_airport_start.py .          # ожидается: нарушено: 0
python3 -I experimental/check_airport_start_selftest.py . # ожидается: непойманных: 0
```

Патч в LF. Если нужен просто файл, лежат полные копии в `files/` (тоже LF, пути как в репозитории).
Коммит — от владельца (OverlordDev), без упоминаний ассистента; пуш только с отдельного разрешения владельца.

## 2. Что изменено (по файлам)

| Файл | Что | Основание в референсе |
|---|---|---|
| `include/Sequoia/IOSkywalkNetworkInterface.h` | `_abi_pad` заменён полями: `_layout0[0x8]`, `ExpansionData *mExpansionData` (**+0xb8**), `_layout1[0x10]`; `static_assert` на смещение и `sizeof(RegistrationInfo)==0x130` | `include/Airport/macOS15/IOSkywalkNetworkInterface.h` |
| `include/Sequoia/IOSkywalkEthernetInterface.h` | то же: `_layout0[0x38]`, `ExpansionData *mExpansionData2` (**+0x108**) | `…/macOS15/IOSkywalkEthernetInterface.h` |
| `include/Sequoia/CCStream.h` | объявлены `CommonFaultReporter`, `IO80211FaultReporter::allocWithParams(CCFaultReporter*)` | `…/macOS15/FaultReporter.h` |
| `AirportMtkWlan/AirportMtkWlan.cpp/.hpp` | см. п. 2.1 | `AirportItlwm/AirportItlwmV2.cpp` (ветка `AIRPORT_WCL`) |
| `AirportMtkWlan/AirportMtkWlanSkywalkInterface.cpp` | `initWithController`: после `IO80211InfraInterface::init()` вызывается `IO80211SkywalkInterface::init(provider, &mac)` | `AirportItlwmSkywalkInterface.cpp::init` |
| `AirportMtkWlan/AirportMtkWlanEthernetInterface.cpp/.hpp` | `setInterfaceSubType(3)` до `super::attachToDataLinkLayer`; `prepareBSDInterface` под gate очереди IO80211 | `AirportItlwmEthernetInterface.cpp` (ветка `AIRPORT_WCL`) |
| `build_airport.sh` | перед сборкой запускается `check_airport_start.py` | — |
| `check_airport_start.py`, `…_selftest.py` | новые | — |

### 2.1 `AirportMtkWlan.cpp` подробно

1. **ExpansionData** (главное). Перед `fNetIf->start(this)` в `mExpansionData->fRegistrationInfo` и
   `mExpansionData2->fRegistrationInfo` выделяется (`IOMalloc`) и копируется `registInfo`. Без этого `start()` Skywalk-интерфейса
   разыменует NULL. Перед записью указатели проверяются функцией `mtkLooksLikeKernelPtr()` (>= `0xffffff8000000000`),
   чтобы при несовпадении смещения получить лог и `return false`, а не панику.
2. **`initCCLogs()`** переписан: три вызова `driverXxxPipe->CCPipe::startPipe()` (фабрика только инициализирует pipe),
   логгер из пустых `CCStreamOptions`, fault reporter в три шага (`CCStream` stream_type 1 → `CCFaultReporter::withStreamWorkloop`
   → `IO80211FaultReporter::allocWithParams`) с проверкой `OSDynamicCast(CommonFaultReporter, …)`.
   При любой неудаче вызывается `releaseCCLogs()`.
3. **`releaseCCLogs()`** (новая): release репортёров/потоков, `stopPipe()` только для стартованных pipe-ов, release pipe-ов.
4. **`getWorkLoop() const`** переопределён и возвращает `_fWorkloop`.
5. **`IONetworkController::attachInterface(&bsdInterface, false)`** вместо `true`; `bsdInterface->registerService()` вызывается в
   новой `finishStart()`, затем `registerService()` контроллера.
6. **Старт интерфейса.** Ключ `MtkDelaySec` (по умолчанию **90**, как было): `0` — синхронно в `start()` с проверкой результата
   (как в референсе); `>0` — отложенно через `thread_call` (отладочный режим). В отложенном пути при `false` контроллер больше
   не регистрируется.
7. `releaseCCLogs()` добавлен в пути неудачи `super::start()` и `MtkStage == 1`.

## 3. Что я НЕ знаю и что может не собраться (проверить первым делом)

| # | Риск | Как проверить / обойти |
|---|---|---|
| 1 | `setInterfaceSubType(3)` может не быть в вашем MacKernelSDK | `grep -rn setInterfaceSubType sequoia_build/MacKernelSDK/Headers`. Обход: добавить `-DMTK_SEQUOIA_BSD_ATTACH=0` в `flags.rsp` (старое поведение) |
| 2 | `__offsetof(...)` внутри `static_assert` на классах с виртуальными методами | в референсе та же конструкция компилируется этим же тулчейном; при ошибке заменить на `offsetof` или убрать assert, сохранив арифметику |
| 3 | Не резолвятся новые символы: `IO80211FaultReporter::allocWithParams`, `CommonFaultReporter::metaClass`, `CCPipe::startPipe/stopPipe` | `build_airport.sh` сам печатает блок «НЕ РЕЗОЛВИТСЯ в ядре Sequoia». Это ожидаемая точка отказа, имена брать из `kmutil libraries` |
| 4 | `ExpansionData` по `+0xb8`/`+0x108` на вашей минорной версии 15.x | включено защитой `mtkLooksLikeKernelPtr`: увидите в логе `ExpansionData pointers are not kernel addresses` |
| 5 | `mtk_ringlog_start/stop` | уже были в исходниках до правок (из `patch_diag.py`); для `plain`-сборки не менялись |
| 6 | Класс-основа `CCFaultReporter` в заголовке порта — `OSObject`, в референсе — `IOService` | на ABI не влияет (объявления), но при странностях с `OSDynamicCast` сверить с `macOS15/FaultReporter.h` |

## 4. План запуска

1. `bash experimental/build_airport.sh` (результат `experimental/out/AirportMtkWlan-diag.kext`).
2. Первый прогон с **`MtkDelaySec` по умолчанию (90)**: если ядро упадёт, к моменту +90 с диск жив и останется `.panic`
   с бектрейсом. Boot-args: `keepsyms=1 debug=0x100 -v` (стандартные).
3. Если за 90 с паники нет и в логе есть `delayed: fNetIf->start() returned 1` — правки работают, следующий прогон с
   `MtkDelaySec = 0` (ключ в `experimental/AirportMtkWlan/Info.plist`, личность `NetworkController`):
   ```xml
   <key>MtkDelaySec</key><integer>0</integer>
   ```
4. Диагностика бисекцией уже есть: `MtkStage` (1–7), остановка `start()` на стадии N.

### 4.1 Какие строки лога что значат

| Строка | Смысл |
|---|---|
| `driverLogPipeStarted 1`, `…DataPathPipeStarted 1`, `…SnapshotsPipeStarted 1` | pipe-ы стартованы |
| `driverFaultReporterRet <ptr>` и нет `is not a CommonFaultReporter` | обёртка получена |
| `MAC aa:bb:…` из `initWithController` | вторая init вызвана с реальным MAC |
| `mExpansionData=… mExpansionData2=… pre-reg=…` | диагностика ExpansionData; оба указателя должны быть адресами ядра |
| `stage10a registration info installed` | ключевая запись выполнена |
| `stage12 iface start OK` / `delayed: fNetIf->start() returned 1` | `IO80211InfraInterface::start` прошёл |

### 4.2 Если всё равно падает

| Где бектрейс | Что смотреть |
|---|---|
| `IOSkywalkEthernetInterface::start` / `IOSkywalkNetworkInterface::start` | смещения ExpansionData на вашей версии (дизассемблировать эти функции: `experimental/sequoia_abi/dis.py`); возможно, Family читает не `fRegistrationInfo`, а вызывает `registerEthernetInterface()` |
| `IO80211InfraInterface::start`, адрес сбоя малый (`0x0–0x1ff`) | какое-то поле интерфейса или контроллера NULL: сопоставить с `gen/IO80211Controller.inc` — приватные слоты (`getPostOffice`, `CreatePostOffice`, `getPLATFORM_CONFIG`, `allocIO80211RecursiveLock`) |
| `CCPipe::*`, `CCLogStream::*` | разобраться с порядком `startPipe` и типом логгера |
| `IO80211SkywalkInterface::init` | подтвердить сигнатуру слота 412 (`init(IOService*, ether_addr*)`) по `vtable_dump.py` |
| `IOSkywalkFamily` приведение типов | проверить `AirportMtkWlanEthernetInterface::getProvider()` (подмена на Skywalk-интерфейс) и `isAttach` |

### 4.3 Настройки OpenCore для первого запуска

Собрано из `5T33Z0/OCLP4Hackintosh` (`Enable_Features/WiFi_BT_Sonoma+.md`, раздел про Intel), `perez987/Intel-AX210-…` и README
`laobamac/itlwm`. Это проверенные чужие настройки для **Intel**-сборки, для MTK — по аналогии, не проверено.

| Что | Значение | Зачем |
|---|---|---|
| `Kernel → Add`, запись нашего kext | `MinKernel = 24.2.0`, `MaxKernel = 24.99.99` | рабочая Sequoia-сборка принципиально для Darwin 24.2–24.99 (15.2+) |
| `Kernel → Quirks → DisableIoMapper` | `true` | драйвер MTK отдаёт карте физические адреса (`getPhysicalAddress()`); без IOMapper-обработки при включённом VT-d DMA ломается. После того как всё заработает, можно проверить, нужен ли он |
| `Kernel → Block` | **не** блокировать `com.apple.iokit.IOSkywalkFamily` | эта блокировка — часть Broadcom/OCLP-схемы; у нативного драйвера Skywalk-семейство нужно штатное |
| Лишние kext-ы | отключить `IOSkywalk.kext`, `IO80211FamilyLegacy.kext`, `AirPortBrcmNIC.kext`, `itlwm.kext` | остатки OCLP/Intel-схем конфликтуют с нативным драйвером; `itlwm` и `AirportItlwm` вместе вообще нельзя |
| Корневые патчи OCLP | не нужны; если уже стоят только ради Wi-Fi — `Post-Install Root Patch → Revert Root Patches` | нативная сборка работает без них |
| `NVRAM boot-args` | `-v debug=0x100 keepsyms=1` | символы в бектрейсе, без перезагрузки по watchdog |
| Версия ОС | на 15.7.5 (24G624) и 15.8.1 `IO80211Family` = 1200.13.1, `IOSkywalkFamily` = 1.0 | один и тот же ABI, значит смещения из референса должны подходить к обеим (по логам из PR #1054 в OpenIntelWireless/itlwm, лог с 15.7.5) |

Что в этих репозиториях **не** пригодилось для кода: `sap24601/Native-Wifi-for-Hackintoshes-…` и `OCLP4Hackintosh` описывают другой путь
(подмена карты под BCM4360 + OCLP root patch + AirportItlwm **Ventura** поверх восстановленного `IO80211FamilyLegacy`).
Он требует `csr-active-config = 03080000`, `SecureBootModel = Disabled`, AMFIPass, ломает запечатанный системный том и в issues
репозитория есть жалобы «No network found» (#8, #9) и «AirDrop only one-way» (#10). Это запасной путь, не основной.

## 5. Откат

Файл `AirportMtkWlan.cpp` сохраняет прежний отладочный режим. Полностью вернуться к поведению до правок:
`git checkout -- experimental/` или собрать с `-DMTK_SEQUOIA_BSD_ATTACH=0` и `MtkDelaySec=90`
(остальные правки — исправления, не переключатели).

## 6. Что ещё НЕ сделано (без этого меню Wi-Fi не заработает, даже если `start` пройдёт)

Подробности и структуры — в `MACOS_SEQUOIA_NATIVE_WIFI_DRIVER_GUIDE.md` (разделы 9–12, 14.2). Кратко:

1. **Протокол WCL** вместо старой модели `APPLE80211_M_*`: `setWCL_SCAN_REQ`, `setWCL_ASSOCIATE`, `setWCL_JOIN_ABORT`,
   `setWCL_LEAVE_NETWORK`, `getWCL_CHANNELS_INFO`, `getWCL_BSS_INFO`, события 201/211–216/237 через
   `controller->postMessage(interface, code, data, size, true)`.
2. **`getCARD_CAPABILITIES`** в WCL-раскладке (байты `[0]`, `[1]`, `[2]`, `[5]=0x40`, `[17]` бит 7).
3. **`enable()`**: `enableFromInterface` — обычный метод, никто не вызывает; найти актуальный слот включения.
4. **Качество линка** `setLQM` (иначе iMessage/FaceTime отвергают интерфейс).
5. **DMA через IOMapper** (AppleVTD): сейчас физические адреса; до этого в OpenCore нужен `DisableIOMapper`.
6. Флаги сборки `__IO80211_TARGET=__MAC_14_4` (на значение в этих заголовках не влияет, но для Sequoia логичнее `__MAC_15_2`).

## 7. Источники (для сверки)

- `laobamac/itlwm`, `main`: `AirportItlwm/AirportItlwmV2.cpp` (`start()` ~строки 266–469), `AirportItlwm/WCL/WCL.{cpp,hpp}`,
  `AirportItlwm/AirportItlwmSkywalkInterface.cpp` (`init`), `AirportItlwm/AirportItlwmEthernetInterface.cpp`,
  `include/Airport/macOS15/*`.
- `OverlordDev/SimpleMtkWlan`, `experimental/sequoia_abi/README.txt` — реальный ABI Family 1200.13.1 на 15.8.1.
