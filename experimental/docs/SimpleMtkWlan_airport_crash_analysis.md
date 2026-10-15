# AirportMtkWlan на Sequoia 15.x: почему не работает нативное меню Wi-Fi

Репозиторий: <https://github.com/OverlordDev/SimpleMtkWlan> (форк laobamac/SimpleMtkWlan), каталог `experimental/`.
Эталон для сравнения: `OpenIntelWireless/itlwm` → `AirportItlwm/AirportItlwmV2.cpp`,
`AirportItlwm-Sonoma-Info.plist`, `include/Airport/IOSkywalk*.h` (это Sonoma-ветка, из неё и сделан порт).

Симптом (из README форка): драйвер доходит до `IO80211Controller::start`, загрузки прошивки, init/attach
интерфейса и регистрации BSD-интерфейса, затем ядро падает внутри `IO80211SkywalkInterface::start` /
`IO80211InfraInterface::start`, панический лог не успевает записаться.

## ОБНОВЛЕНИЕ: найден рабочий Sequoia-референс (laobamac/itlwm)

Пока писался первый вариант файла, нашёлся настоящий эталон именно для Sequoia: <https://github.com/laobamac/itlwm>
(ветка `main`, цель `AirportItlwm-Sequoia`, релиз `v2.4.0-alpha` от 2026-10-11, README: «Darwin 24.2.0–24.99.99», проверено на 15.8).
Автор тот же, что у SimpleMtkWlan. Я читал исходники (`AirportItlwm/AirportItlwmV2.cpp`, `include/Airport/macOS15/*`),
сборку не запускал; «работает» — со слов README и форума InsanelyMac.

Что это меняет:

- **Пункт 1 подтверждён кодом.** В `AirportItlwmV2.cpp::start()` (ветка `AIRPORT_WCL`, строки ~420–443) перед `fNetIf->start(this)`
  выделяются и заполняются `mExpansionData->fRegistrationInfo` и `mExpansionData2->fRegistrationInfo`, затем `deferBSDAttach(true)`.
  Смещения для Sequoia из их заголовков: `mExpansionData` = `0xB8` (в `IOSkywalkNetworkInterface`), `mExpansionData2` = `0x108`
  (в `IOSkywalkEthernetInterface`); `ExpansionData { RegistrationInfo *fRegistrationInfo; ifnet_t fBSDInterface; }`;
  `RegistrationInfo` = `0x130` байт (у порта `pad[304]` = `0x130`, совпадает).
- **Пункт 2 в основном снят.** `static_assert` у них те же: `IOSkywalkInterface 0xb0`, `IOSkywalkNetworkInterface 0xd0`,
  `IOSkywalkEthernetInterface 0x110`, `IO80211SkywalkInterface 0x118`, `IO80211InfraInterface 0x120`. Размеры в порте, скорее всего, верные.
- **Новые отличия, которых я раньше не видел:**
  - `IONetworkController::attachInterface(&bsdInterface, false)` и `bsdInterface->registerService()` в конце `start()`;
    в порте `attachInterface(..., true)`.
  - `fNetIf->start()` вызывается синхронно, без задержки; при `false` — `super::stop` и выход.
  - Проверка `version_major == 24 && version_minor >= 2` (то есть 15.2+).
  - Отдельный слой `AirportItlwm/WCL/` (скан-тайминги, link quality, channel info, traffic counters) и
    коммиты про `setLQM`/link quality для iServices.
  - `Info.plist` Sequoia не отличается от Sonoma (тот же `IOPCIEDeviceWrapper`), значит матчинг не причина.

Итог: падение, скорее всего, лечится заполнением `ExpansionData` перед `start()`. Остальное из списка ниже — вторично.

---

## Как читать

| Метка | Значение |
|---|---|
| **ФАКТ** | видно в коде двух репозиториев, сравнено построчно |
| **ВЕРОЯТНО** | следует из фактов, но не проверено на железе/дизассемблере |
| **ГИПОТЕЗА** | возможно, нужна проверка |

Не проверялось: я не запускал драйвер, у меня нет panic-лога и дизассемблера ядра Sequoia.
Прочитаны только файлы `AirportMtkWlan*.cpp/hpp`, `IOPCIEDeviceWrapper.*`, `Info.plist`, сгенерированные
заголовки `experimental/include/Sequoia/**` и `sequoia_abi/README.txt`. Весь репозиторий не просматривался.

---

## 1. Не заполнены `ExpansionData` / `fRegistrationInfo` у Skywalk-интерфейса — самая вероятная причина

**ФАКТ.** В эталонном `AirportItlwmV2.cpp::start()` между `initRegistrationInfo` и `fNetIf->start(this)` есть вставка:

```cpp
fNetIf->mExpansionData->fRegistrationInfo  = IOMalloc(sizeof(IOSkywalkNetworkInterface::RegistrationInfo));
fNetIf->mExpansionData2->fRegistrationInfo = IOMalloc(sizeof(IOSkywalkEthernetInterface::RegistrationInfo));
memcpy(fNetIf->mExpansionData->fRegistrationInfo,  &registInfo, sizeof(registInfo));
memcpy(fNetIf->mExpansionData2->fRegistrationInfo, &registInfo, sizeof(registInfo));
```

Это ручное воспроизведение того, что делает `registerEthernetInterface()`: `start()` в Family читает
`fRegistrationInfo` из этих структур. В `include/Airport/IOSkywalkEthernetInterface.h` апстрима
`mExpansionData2` лежит по смещению `0x108`, а `mExpansionData` — в `IOSkywalkNetworkInterface` (размер `0xD0`).

**ФАКТ.** В `AirportMtkWlan::start()` (стадии 9–10) вызывается только `initRegistrationInfo(&registInfo, 1, sizeof(registInfo))`
и `deferBSDAttach(true)`. `registInfo` — локальная переменная, дальше она не используется, в `ExpansionData` ничего не пишется.
В переписанных заголовках Sequoia (`IOSkywalkNetworkInterface.h`, `IOSkywalkEthernetInterface.h`) полей `mExpansionData*` нет:
вместо них `uint8_t _abi_pad_*[...]`, так что код физически не может их заполнить.
По файлам, которые я читал, упоминаний `mExpansion*` / `fRegistrationInfo` в драйвере нет.

**ВЕРОЯТНО.** Тогда `IOSkywalk*Interface::start` (внутри `IO80211InfraInterface::start`) разыменует NULL
`fRegistrationInfo` — это совпадает с «падает в `start` на ранней стадии». Для NULL-разыменования в panic-логе
обычно виден адрес сбоя вида `0x0..0x1ff`.

**Оговорка.** На Sequoia механизм мог измениться: смещения `0xC8`/`0x108` не обязаны совпадать с Sonoma,
а сам `start()` мог уже звать `registerEthernetInterface`. Поэтому «просто скопировать код из Sonoma» может не сработать.

**Как проверить.**
1. `sequoia_abi/dis.py` на `IOSkywalkEthernetInterface::start`, `IOSkywalkNetworkInterface::start`,
   `IOSkywalkEthernetInterface::initRegistrationInfo` и `registerEthernetInterface`: куда пишут / откуда читают поле.
2. Если читают `[this+off]` из pad-области, добавить заполнение по найденному смещению перед `fNetIf->start()`.
3. Либо вызвать штатный `registerEthernetInterface(&registInfo, queues, n, pool, pool, opts)`
   (объявлен в `IOSkywalkEthernetInterface.h`, но в драйвере не вызывается) — как это делает драйвер Apple.

---

## 2. Размеры классов и смещения полей не подтверждены (после обновления: размеры совпали с рабочим референсом)

**ФАКТ.** В `sequoia_abi/README.txt` сказано, что восстановлены **vtable** (слоты и сигнатуры). О размерах и смещениях
полей там ничего нет. При этом в заголовках стоят `static_assert(sizeof(...) == 0xb0 / 0xd0 / 0x110 / 0x118 / 0x120)` —
для первых трёх это ровно значения из Sonoma-заголовков апстрима.

**ВЕРОЯТНО / ГИПОТЕЗА.** Если реальный `sizeof(IO80211InfraProtocol)` на Sequoia больше `0x120`, поля
`AirportMtkWlanSkywalkInterface` (`instance`, `fHalService`, `scanSource`, …) наложатся на внутренние поля Apple.
Класс ломается тихо, а падение случается в первом же месте, где Apple читает своё поле, то есть в `start`.

**Как проверить.** В KC найти конструктор метакласса (`OSMetaClass::OSMetaClass(name, super, size)`) для
`IO80211SkywalkInterface`, `IO80211InfraInterface`, `IO80211InfraProtocol`, `IOSkywalkEthernetInterface`:
третий аргумент и есть `sizeof`. Сравнить с `static_assert`.

---

## 3. Подкласс `IO80211InfraProtocol` не проверен против реального порядка слотов

**ФАКТ.** Драйверный интерфейс наследует `IO80211InfraProtocol` (190 чисто виртуальных слотов 465–654 из
`gen/IO80211InfraProtocol.inc`). В списке дампов vtable в README (`vtables_IO80211_IOSkywalk_*`) перечислены
`IO80211SkywalkInterface`, `IO80211InfraInterface`, `IO80211Controller`, `IOSkywalkNetworkInterface`,
`IOSkywalkEthernetInterface` — `IO80211InfraProtocol` в этом списке нет. Результат работы `check_vtable.py`
(clang-vs-kernel) в репозитории не записан.

**ГИПОТЕЗА.** Если слотов в ядре больше/меньше или порядок отличается, Apple вызовет не тот метод:
в лучшем случае вернётся `kIOReturnUnsupported` из заглушки, в худшем — переход в чужую функцию с неверными аргументами.

**Как проверить.** Прогнать `vtable_dump.py` по `IO80211InfraProtocol` и по конкретному классу интерфейса эталонного драйвера
Apple (в репозитории уже есть `vtables_AppleBCMWLANCore_*`), затем `check_vtable.py` против собранного kext.

---

## 4. Отложенный `fNetIf->start()` меняет порядок инициализации

**ФАКТ.** В эталоне `fNetIf->start(this)` вызывается прямо в `AirportItlwm::start()`, перед `registerService()`.
В порт-версии `start()` откладывается на 90 с через `thread_call_enter_delayed` (`MtkDelaySec`), потом вызывается
`setLinkStatus(kIONetworkLinkValid)` и `registerService()`.
Это отладочная мера: «упадёт — останется .panic».

**ГИПОТЕЗА.** Family может рассчитывать, что интерфейс стартует в рамках `start()` контроллера (пока контроллер не
зарегистрирован и нет клиентов). За 90 с после `attachInterface` в систему уже могут прийти запросы к ещё не
запущенному интерфейсу. Ещё `thread_call` исполняется вне workloop/command gate. Это может как порождать
падение, так и менять его место. Из репозитория не видно, проверяли ли вариант с `MtkDelaySec=0` на тех же условиях.

**Как проверить.** Запустить с `MtkDelaySec=0` и сравнить место падения с задержкой 90 с.

---

## 5. Не вызывается `enable()` интерфейса из Family

**ФАКТ.** В эталоне переопределён `AirportItlwm::enable(IO80211SkywalkInterface*)` / `disable(...)`. В порте они
переименованы в `enableFromInterface` / `disableFromInterface` — это обычные методы, не виртуальные слоты.
В списке слотов Controller для Sequoia (`gen/IO80211Controller.inc`, 394–462) `enable(IO80211SkywalkInterface*)` отсутствует.

**ВЕРОЯТНО.** Это не причина падения в `start`, но если `start` починить, `enableFromInterface` никто не вызовет.
Адаптер не будет включён из Family, и «link up» не появится. Нужно найти, какой слот теперь отвечает за включение
(кандидат — `setInterfaceEnable(bool)`, слот 293 в `IO80211InfraInterface.inc`; это именно кандидат, не проверено).

---

## 6. Окружение: ядро падает раньше, чем успевает записаться лог

**ФАКТ.** README: «no panic report survives». Это не причина сбоя, а причина слепоты: диск на ранней стадии
ещё недоступен, поэтому приходится гадать по `MtkStage`.

**Что можно сделать** (стандартные средства, не из репозитория):
- boot-args `keepsyms=1 debug=0x100 -v`, чтобы в бектрейсе были символы и watchdog не мешал;
- последовательный/сетевой вывод panic (netdump / serial) либо фото экрана с бектрейсом;
- по бектрейсу сразу видно, в каком `IO80211*::start` и по какому адресу сбой — это быстро разделяет пункты 1 и 2.

---

## 7. Контекст: апстрим сам не гарантирует работу на Sequoia

Выдача поиска (форумные заметки, вторичные источники) — AirportItlwm 2.3.0, собранный под Sonoma 14.4, на macOS 15 beta
«не работал». Это стоит учитывать: даже эталон может быть несовместим, и тогда сравнивать нужно с реальным
`AppleBCMWLANCore` на целевой системе, а не с itlwm.

---

## Порядок проверки (от самого дешёвого)

1. Бектрейс с `keepsyms=1` → адрес сбоя и функция (разводит 1 / 2 / 3).
2. Дизассемблировать `IOSkywalkEthernetInterface::start` / `registerEthernetInterface` → есть ли чтение `fRegistrationInfo`.
3. Сверить `sizeof` через метаклассы (пункт 2).
4. Завершить `check_vtable.py` для `IO80211InfraProtocol` (пункт 3).
5. Прогнать с `MtkDelaySec=0` (пункт 4).
6. Только после успешного `start` разбираться с `enable` (пункт 5), `registerService` и отображением в меню.

## Поправка к предыдущему ответу

Предыдущий раз я сравнивал порт с `AirportItlwm.cpp` (ветка до Sonoma). Правильный эталон — `AirportItlwmV2.cpp`
и `AirportItlwm-Sonoma-Info.plist`. Двухступенчатый матчинг через `IOPCIEDeviceWrapper` (`IOMatchCategory=WiFiDriver`,
`IONetworkRootType=airport`, `IOResourceMatch=IOBSD`) подтверждён и там: в портированном `Info.plist` он совпадает с эталоном
один к одному, так что причина не в матчинге.
