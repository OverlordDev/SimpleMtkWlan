#!/bin/bash
# Кладёт Tahoe-сборку AirportMtkWlan на флешку КАК ОТДЕЛЬНЫЙ кекст EFI/OC/Kexts/AirportMtkWlan-Tahoe.kext.
# Рабочий SimpleMtkWlan.kext (Sequoia) и config.plist НЕ меняются: пока в config.plist нет записи, OpenCore этот кекст не грузит.
# Запуск:  bash install_airport_tahoe_to_stick.sh [diag|o2|f|plain] [том]     (по умолчанию diag, том MACOSINSTAL)
# Откат:   rm -rf /Volumes/<том>/EFI/OC/Kexts/AirportMtkWlan-Tahoe.kext   (и убрать запись из config.plist, если добавляли)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-diag}"; VOL="/Volumes/${2:-MACOSINSTAL}"
case "$MODE" in
    diag)  K="$HERE/out_tahoe/AirportMtkWlan-diag.kext" ;;
    plain) K="$HERE/out_tahoe/AirportMtkWlan.kext" ;;
    o2)    K="$HERE/out_tahoe/AirportMtkWlan-diag-O2.kext" ;;
    f)     K="$HERE/out_tahoe/AirportMtkWlan-diag-F.kext" ;;   # -O2 только для файлов из OPT_FILES
    *) echo "использование: $0 [diag|o2|f|plain] [том]"; exit 1 ;;
esac
[ -f "$K/Contents/MacOS/AirportMtkWlan" ] || { echo "Нет сборки $K (сначала bash build_airport_tahoe.sh)"; exit 1; }
[ -d "$VOL/EFI/OC/Kexts" ] || { echo "Не найден $VOL/EFI/OC/Kexts (флешка не подключена?)"; exit 1; }
DST="$VOL/EFI/OC/Kexts/AirportMtkWlan-Tahoe.kext"
rm -rf "$DST"; cp -R "$K" "$DST"; sync
A="$(shasum "$K/Contents/MacOS/AirportMtkWlan" | cut -c1-40)"; B="$(shasum "$DST/Contents/MacOS/AirportMtkWlan" | cut -c1-40)"
[ "$A" = "$B" ] || { echo "Контрольные суммы не совпали!"; exit 1; }
echo "Записан $DST (sha1 $A)"
cat <<TXT

config.plist не тронут. Чтобы OpenCore грузил кекст только на Tahoe (Darwin 25), а Sequoia-кекст только на Sequoia (Darwin 24),
в $VOL/EFI/OC/config.plist нужны две правки в Kernel -> Add (сделай копию файла перед этим):
  1) у записи SimpleMtkWlan.kext:           MaxKernel = 24.99.99
  2) новая запись (скопируй запись SimpleMtkWlan.kext и поменяй поля):
       BundlePath = AirportMtkWlan-Tahoe.kext, ExecutablePath = Contents/MacOS/AirportMtkWlan,
       PlistPath = Contents/Info.plist, MinKernel = 25.0.0, Enabled = true
  Порядок: новая запись после Lilu и после SimpleMtkBtFw, как и у Sequoia-кекста.
TXT
