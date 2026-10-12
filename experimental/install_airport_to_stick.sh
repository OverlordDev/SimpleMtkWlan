#!/bin/bash
# Кладёт AirportMtkWlan (системное Wi-Fi) на флешку ВМЕСТО SimpleMtkWlan.
# Путь/имя файла в EFI/OC/Kexts/SimpleMtkWlan.kext остаются прежними, поэтому config.plist НЕ меняется.
# Перед заменой полный бэкап кекста и config.plist в ~/Desktop/desk_backup_sequoia/airport_<время>/.
# Откат:  bash install_airport_to_stick.sh restore <папка бэкапа>
#   bash install_airport_to_stick.sh [diag|plain] [том]      по умолчанию diag, том MACOSINSTAL
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-diag}"
if [ "$MODE" = restore ]; then
    BK="$2"; VOL="/Volumes/${3:-MACOSINSTAL}"
    [ -d "$BK/SimpleMtkWlan.kext.before" ] || { echo "Нет $BK/SimpleMtkWlan.kext.before"; exit 1; }
    rm -rf "$VOL/EFI/OC/Kexts/SimpleMtkWlan.kext"
    cp -R "$BK/SimpleMtkWlan.kext.before" "$VOL/EFI/OC/Kexts/SimpleMtkWlan.kext"
    sync; echo "Восстановлен SimpleMtkWlan из $BK"; exit 0
fi
VOL="/Volumes/${2:-MACOSINSTAL}"
case "$MODE" in
    diag)  K="$HERE/out/AirportMtkWlan-diag.kext" ;;
    plain) K="$HERE/out/AirportMtkWlan.kext" ;;
    *) echo "использование: $0 [diag|plain] [том] | restore <бэкап> [том]"; exit 1 ;;
esac
DST="$VOL/EFI/OC/Kexts/SimpleMtkWlan.kext"
[ -f "$K/Contents/MacOS/AirportMtkWlan" ] || { echo "Нет сборки $K (сначала bash build_airport.sh)"; exit 1; }
[ -d "$DST" ] || { echo "На флешке нет $DST"; exit 1; }
BK="$HOME/Desktop/desk_backup_sequoia/airport_$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
cp -R "$DST" "$BK/SimpleMtkWlan.kext.before"
cp "$VOL/EFI/OC/config.plist" "$BK/config.plist"
echo "Бэкап: $BK"
cp "$K/Contents/MacOS/AirportMtkWlan" "$DST/Contents/MacOS/SimpleMtkWlan"
cp "$K/Contents/Info.plist" "$DST/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleExecutable SimpleMtkWlan" "$DST/Contents/Info.plist"
# отладка: MTK_STAGE=N останавливает start() драйвера на стадии N (1..8), без переменной - полный запуск
PB=/usr/libexec/PlistBuddy; PERS=":IOKitPersonalities:NetworkController:MtkStage"
if [ -n "${MTK_STAGE:-}" ]; then $PB -c "Set $PERS $MTK_STAGE" "$DST/Contents/Info.plist" 2>/dev/null || $PB -c "Add $PERS integer $MTK_STAGE" "$DST/Contents/Info.plist"; echo "MtkStage = $MTK_STAGE"; fi
plutil -lint "$DST/Contents/Info.plist" >/dev/null || { echo "Info.plist испорчен, откатываю"; rm -rf "$DST"; cp -R "$BK/SimpleMtkWlan.kext.before" "$DST"; exit 1; }
sync
A="$(shasum "$K/Contents/MacOS/AirportMtkWlan" | cut -c1-40)"; B="$(shasum "$DST/Contents/MacOS/SimpleMtkWlan" | cut -c1-40)"
[ "$A" = "$B" ] || { echo "Контрольные суммы не совпали!"; exit 1; }
echo "Записан AirportMtkWlan ($MODE), sha1 $A"
i=0
while BP="$(/usr/libexec/PlistBuddy -c "Print :Kernel:Add:$i:BundlePath" "$VOL/EFI/OC/config.plist" 2>/dev/null)"; do
    [ "$BP" = "SimpleMtkWlan.kext" ] && echo "config.plist: SimpleMtkWlan.kext Enabled = $(/usr/libexec/PlistBuddy -c "Print :Kernel:Add:$i:Enabled" "$VOL/EFI/OC/config.plist")  ExecutablePath = $(/usr/libexec/PlistBuddy -c "Print :Kernel:Add:$i:ExecutablePath" "$VOL/EFI/OC/config.plist")"
    i=$((i+1))
done
echo
echo "Откат (одной командой): bash $HERE/install_airport_to_stick.sh restore $BK"
echo "Если macOS не поднялась/паника: перезагрузись и выбери ВНУТРЕННИЙ EFI диска (там рабочий SimpleMtkWlan)."
