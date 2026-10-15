SimpleMtkWlan под macOS Sequoia 15.x (сборка без Xcode, только Command Line Tools)

Что это
  Сборка исходников из ../ прямо на Sequoia. Оригиналы (tgz, готовые кексты) не тронуты.
  Источники:
    best    ../sources/source_current.tgz               = 1_BEST_kext_with_54M_tx_fix (режимы a/g)
    stageB  ../sources/source_stageB_vht80.tgz = HT20/HT40/VHT80 + приём агрегированных кадров (A-MPDU RX)

Как собрать
  bash build.sh                    оба источника
  SOURCES=stageB bash build.sh     только один
  Результат в out/<источник>/:
    SimpleMtkWlan.kext         обычный кекст
    SimpleMtkWlan-diag.kext    то же + лог драйвера: свойство MtkLog/MtkHB/MtkKeep на узле WL00 в ioreg
                               и строки MTKDBG в журнале ядра
    patched-sources-*/         исходники после патчей: по номерам строк из лога ("return false at line N")
  Скрипт сам выставляет DEVELOPER_DIR на Command Line Tools, так что работает, даже если xcode-select
  смотрит на Xcode с непринятой лицензией.

Как положить на флешку
  bash install_to_stick.sh <кекст> [режим]
    кекст: stageB-diag | stageB | best-diag | best | original
    режим: vht80 (по умолчанию) | ht40 | ht20 | legacy     (ключ MtkMode в Info.plist кекста на флешке)
  Скрипт делает бэкап в ~/Desktop/desk_backup_sequoia/flash_<время>/, меняет только бинарь (и MtkMode),
  config.plist не трогает. Потом перезагрузка с флешки как обычно.

Как проверить
  ioreg -w0 -r -c SimpleMtkWlan | head                         узел есть -> драйвер сел на карту
  ioreg -w0 -rn WL00 -l | grep -o '"MtkHB" = ".*' | tail -c 3000      (diag-сборка) счётчики раз в секунду
  Строка "HB rxrates ..." (stageB) показывает, на каких скоростях роутер шлёт кадры карте.

Чем эти сборки отличаются от первых попыток на Sequoia
  Первые сборки были -O2 и с deployment target 10.12. Xcode-сборка, которая работала на Tahoe, была
  Debug: -O0, DEBUG=1, deployment target 10.9 (в заголовках MacKernelSDK это меняет vtable:
  IORegistryEntry::init вместо IOService::init). Здесь повторены именно эти настройки.
  Проверка против бинаря 1_BEST: набор внешних символов совпадает 1:1, набор своих символов совпадает
  1:1 (1257), размеры секций __cstring, __got, __mod_init_func те же, у 935 из 1021 функций размер кода
  совпадает. Остальные отличаются только числом вызовов логирования.

Патчи под Sequoia (build.sh, к копии исходников)
  1. Загрузка прошивки. Куски по 4096 байт + заголовок TXD (64 байта) = 4160 байт в одном mbuf, для этого
     mbuf_allocpacket() берёт 16KB jumbo-кластер, и неблокирующий запрос на него на Sequoia не проходит
     (ENOMEM = 12): "patch send failed index=0 error=12", драйвер не садился на карту. Теперь для кусков
     прошивки буфер выделяется ровно под len байт (заголовка у них всё равно нет), хватает 4KB-кластера.
  2. MWX_LOG не дублируется через printf в журнал ядра (как в рабочем дереве ~/Desktop/desk/SimpleMtkWlan).
  3. Режим работы из Info.plist (MtkMode), чтобы переключать vht80/ht40/ht20/legacy без пересборки.
  4. BSS сообщает прошивке согласованные HT/VHT (раньше только legacy a/b/g), и VHT явно включается в net80211
     (в этапе B флаг IEEE80211_F_VHTON нигде не выставлялся). Итог: приём на VHT80, отправка перестала быть 54 Мбит/с.
  5. Агрегация отправки (TX A-MPDU), patch_txagg.py: caps QoS+TX_AMPDU, net80211 шлёт ADDBA, по ответу роутера
     прошивка программируется (WTBL_BA + STA_REC_BA в роли originator, как в Linux mt76), агрегирует железо.
     Выключить: NO_TX_AGG=1 bash install_to_stick.sh stageB-diag  (ключ NoTxAmpdu) или boot-arg -notxampdu.
  6. BSS RLM (patch_rlm.py): канал, центральный канал, ширина и число потоков BSS сообщаются прошивке после подключения
     (в mt76 это отдельный запрос после BSS basic; в порте был пропущен). Без него отправка не выходила за HT MCS7, 1 поток.

Откат
  Бэкап лежит в ~/Desktop/desk_backup_sequoia/flash_<время>/ (SimpleMtkWlan.kext.before и config.plist).
  Быстро вернуть сборку BEST: bash install_to_stick.sh best-diag

История проверок на железе (2026-10-08)
  07:38  best-diag без патча прошивки: драйвер на карту не садится, "patch send failed ... error=12".
  07:46  best-diag с патчом прошивки: Wi-Fi работает. 5 ГГц, канал 36, режимы a/g.
         Замер через en3: скачивание ~13 Мбит/с, отдача ~19 Мбит/с (роутер умеет VHT80, драйвер не использует).

История проверок (продолжение)
  2026-10-08  stageB vht80 + phymode: скачивание ~90 Мбит/с, отдача ~27, приём на VHT80 2SS MCS4-9, отправка HT MCS7 1SS.
  2026-10-10  + TX A-MPDU: соглашение BA поднимается (HB tx ba ... rv=0), скачивание ~300 Мбит/с одним потоком,
              отдача ~60 Мбит/с, networkQuality 310/60 Мбит/с. Отправка всё ещё HT MCS7 1SS -> патч BSS RLM.
