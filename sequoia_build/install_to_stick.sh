#!/bin/bash
# Кладёт кекст на флешку с OpenCore.
# Меняет ТОЛЬКО бинарь SimpleMtkWlan внутри кекста (и, если нужно, ключ MtkMode в его Info.plist).
# config.plist и остальной EFI не трогает. Перед заменой сохраняет старый кекст и config.plist
# в ~/Desktop/desk_backup_sequoia/flash_<время>/.
#
#   bash install_to_stick.sh <кекст> [режим] [том]
#
#   кекст:
#     stageB-diag   HT/VHT80 + приём агрегированных кадров, с логом драйвера (MtkLog на WL00, MTKDBG в журнале)
#     stageB        то же без диагностики
#     best-diag     сборка "1_BEST" (режимы a/g, ~20 Мбит/с) с логом
#     best          то же без диагностики
#
#   режим (необязательно, ключ MtkMode в Info.plist кекста на флешке):
#     vht80 (по умолчанию)  802.11ac, канал до 80 МГц
#     ht40                  802.11n, до 40 МГц
#     ht20                  802.11n, 20 МГц
#     legacy                без HT/VHT (как раньше, режимы a/g)
#
#   том: имя флешки, по умолчанию MACOSINSTAL.
#
#   NO_TX_AGG=1 bash install_to_stick.sh stageB-diag     без агрегации отправки (ключ NoTxAmpdu в Info.plist)
set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
VARIANT="${1:-}"
MODE="${2:-vht80}"
VOL="/Volumes/${3:-MACOSINSTAL}"

# старые имена из прошлой версии скрипта
case "$VARIANT" in
    diag)  VARIANT=best-diag ;;
    plain) VARIANT=best ;;
esac

case "$VARIANT" in
    stageB-diag) SRC="$HERE/out/stageB/SimpleMtkWlan-diag.kext/Contents/MacOS/SimpleMtkWlan" ;;
    stageB)      SRC="$HERE/out/stageB/SimpleMtkWlan.kext/Contents/MacOS/SimpleMtkWlan" ;;
    best-diag)   SRC="$HERE/out/best/SimpleMtkWlan-diag.kext/Contents/MacOS/SimpleMtkWlan" ;;
    best)        SRC="$HERE/out/best/SimpleMtkWlan.kext/Contents/MacOS/SimpleMtkWlan" ;;
    *) sed -n '2,/^set -e/p' "$0" | sed '$d'; exit 1 ;;
esac
case "$MODE" in
    vht80|ht40|ht20|legacy) ;;
    *) echo "Неизвестный режим: $MODE (vht80 | ht40 | ht20 | legacy)"; exit 1 ;;
esac

KEXT="$VOL/EFI/OC/Kexts/SimpleMtkWlan.kext"
DST="$KEXT/Contents/MacOS/SimpleMtkWlan"
PLIST="$KEXT/Contents/Info.plist"

[ -f "$SRC" ]            || { echo "Нет файла $SRC (сначала: bash build.sh)"; exit 1; }
[ -d "$VOL/EFI/OC" ]     || { echo "Флешка не найдена: $VOL/EFI/OC"; exit 1; }
[ -f "$DST" ]            || { echo "На флешке нет $KEXT"; exit 1; }

BK="$HOME/Desktop/desk_backup_sequoia/flash_$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
cp -R "$KEXT" "$BK/SimpleMtkWlan.kext.before"
cp "$VOL/EFI/OC/config.plist" "$BK/config.plist"
echo "Бэкап старого кекста и config.plist: $BK"

cp "$SRC" "$DST"

# режим: по умолчанию (vht80) ключа нет вообще, иначе MtkMode = <режим>
PB=/usr/libexec/PlistBuddy
PERS=":IOKitPersonalities:SimpleMtkWlan:MtkMode"
if [ "$VARIANT" != original ]; then
    if [ "$MODE" = vht80 ]; then
        $PB -c "Delete $PERS" "$PLIST" 2>/dev/null || true
    else
        $PB -c "Set $PERS $MODE" "$PLIST" 2>/dev/null || $PB -c "Add $PERS string $MODE" "$PLIST"
    fi
    NOAGG=":IOKitPersonalities:SimpleMtkWlan:NoTxAmpdu"
    if [ "${NO_TX_AGG:-0}" = 1 ]; then
        $PB -c "Set $NOAGG true" "$PLIST" 2>/dev/null || $PB -c "Add $NOAGG bool true" "$PLIST"
    else
        $PB -c "Delete $NOAGG" "$PLIST" 2>/dev/null || true
    fi
    plutil -lint "$PLIST" >/dev/null || { echo "Info.plist после правки не проходит проверку, откатываю"; cp "$BK/SimpleMtkWlan.kext.before/Contents/Info.plist" "$PLIST"; exit 1; }
fi
sync

A="$(shasum "$SRC" | cut -c1-40)"
B="$(shasum "$DST" | cut -c1-40)"
[ "$A" = "$B" ] || { echo "Контрольные суммы не совпали!"; exit 1; }
echo "Записано: $VARIANT, режим $MODE, агрегация отправки: $([ "${NO_TX_AGG:-0}" = 1 ] && echo выключена || echo включена), sha1 $A"

# только прочитать, что стоит в config.plist (ничего не меняем)
i=0
while BP="$($PB -c "Print :Kernel:Add:$i:BundlePath" "$VOL/EFI/OC/config.plist" 2>/dev/null)"; do
    if [ "$BP" = "SimpleMtkWlan.kext" ]; then
        echo "config.plist: SimpleMtkWlan.kext Enabled = $($PB -c "Print :Kernel:Add:$i:Enabled" "$VOL/EFI/OC/config.plist")"
    fi
    i=$((i+1))
done
echo
echo "Дальше: перезагрузись и выбери эту флешку в OpenCore как обычно (вынимать её не нужно)."
echo "Откат: скопируй содержимое $BK/SimpleMtkWlan.kext.before/Contents/ обратно в $KEXT/Contents/"
