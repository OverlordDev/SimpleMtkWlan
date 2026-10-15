#!/bin/bash
# Сборка AirportMtkWlan.kext (системное Wi-Fi через IO80211Family) для Sequoia без Xcode.
# Берёт исходники этапа B из бэкапа, накладывает те же патчи, что и sequoia_build, выбрасывает
# Ethernet-обвязку SimpleMtkWlan и вставляет Airport-обвязку из ./AirportMtkWlan.
# Запуск:  bash build_airport.sh [plain]     результат: out/AirportMtkWlan-diag.kext (по умолчанию, с логом) или out/AirportMtkWlan.kext
set -e
[ -d /Library/Developer/CommandLineTools ] && export DEVELOPER_DIR="${DEVELOPER_DIR:-/Library/Developer/CommandLineTools}"

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
# статическая проверка порядка start() и раскладки ABI (см. check_airport_start.py); обходить не нужно,
# она не требует ничего кроме python3 и отрабатывает за долю секунды
python3 -I "$HERE/check_airport_start.py" "$REPO" || { echo "check_airport_start.py: правила нарушены, сборка остановлена"; exit 1; }
SEQ="$REPO/sequoia_build"
TGZ="$(mktemp -d)/source_stageB_vht80.tgz"
tar czf "$TGZ" -C "$REPO" SimpleMtkWlan mtk80211 include SimpleMtkWlan.xcodeproj
MKS="$SEQ/MacKernelSDK"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
WORK="$HERE/build"; OUT="$HERE/out"
JOBS="$(sysctl -n hw.ncpu)"
DIAG=1; [ "$1" = plain ] && DIAG=0
NAME=AirportMtkWlan
BUNDLE_ID=com.laobamac.AirportMtkWlan
P="$WORK/src"; O="$WORK/obj"

rm -rf "$WORK"; mkdir -p "$P" "$O" "$OUT"
tar xzf "$TGZ" -C "$P"

# Ethernet-обвязка не нужна: класс SimpleMtkWlan, клиентский интерфейс, свои PM
rm -f "$P/SimpleMtkWlan/SimpleMtkWlan.cpp" "$P/SimpleMtkWlan/SimpleMtkWlan.hpp" \
      "$P/SimpleMtkWlan/MtkWlanUserClient.cpp" "$P/SimpleMtkWlan/MtkWlanUserClient.hpp" "$P/SimpleMtkWlan/pm.cpp"

for pt in patch_sequoia.py patch_txagg.py patch_rlm.py; do python3 -I "$SEQ/$pt" "$P"; done
[ "$DIAG" = 1 ] && python3 -I "$SEQ/patch_diag.py" "$P"

mkdir -p "$P/AirportMtkWlan" "$P/include/Airport"
cp "$HERE"/AirportMtkWlan/*.cpp "$HERE"/AirportMtkWlan/*.hpp "$P/AirportMtkWlan/"
cp -R "$HERE"/include/Sequoia/. "$P/include/Airport/"
sed 's/%s::/AirportMtkWlanSkywalkInterface::/' "$HERE"/include/Sequoia/gen/pure_def_infra.inc > "$P/AirportMtkWlan/pure_def_iface.inc"
sed 's/%s::/AirportMtkWlan::/' "$HERE"/include/Sequoia/gen/pure_def_controller.inc > "$P/AirportMtkWlan/pure_def_ctl.inc"

cat > "$WORK/info.cpp" <<EOT
#include <mach/mach_types.h>
extern kern_return_t _start(kmod_info_t *ki, void *data);
extern kern_return_t _stop(kmod_info_t *ki, void *data);
__attribute__((visibility("default"))) KMOD_EXPLICIT_DECL($BUNDLE_ID, "1.0.0", _start, _stop)
__private_extern__ kmod_start_func_t *_realmain = 0;
__private_extern__ kmod_stop_func_t *_antimain = 0;
__private_extern__ int _kext_apple_cc = __APPLE_CC__;
EOT

cat > "$WORK/flags.rsp" <<EOT
-arch x86_64
-isysroot $SDK
-mmacosx-version-min=10.12
-std=gnu++14
-x c++
-O0
-g
-mkernel
-fapple-kext
-fno-exceptions
-fno-rtti
-fno-builtin
-fno-common
-nostdinc
-nostdinc++
-Wno-everything
-DKERNEL
-DKERNEL_PRIVATE
-DDRIVER_PRIVATE
-DAPPLE
-DNeXT
-DDEBUG=1
-D__PRIVATE_SPI__
-DIEEE80211_STA_ONLY
-DAIRPORT
-DIO80211FAMILY_V2
-D__IO80211_TARGET=__MAC_14_4
-DITLWM_VERSION=\"1.0.0\"
-DSMTW_VERSION=\"1.0.0\"
-DGIT_COMMIT=\"\"
-isystem $P/mtk80211/openbsd
-isystem $P/mtk80211
-isystem $P/include
-I$P/mtk80211/linux
-I$P/mtk80211/openbsd/crypto
-I$P
-I$P/SimpleMtkWlan
-I$P/SimpleMtkWlan/hal_mwx
-I$P/AirportMtkWlan
-I$P/include/Airport
-I$MKS/Headers
-include $P/SimpleMtkWlan/PrivateSPI.pch
EOT

( cd "$P" && find SimpleMtkWlan/hal_mwx mtk80211 include AirportMtkWlan \( -name '*.c' -o -name '*.cpp' \) | sort ) > "$WORK/files.txt"
cat > "$WORK/compile_one.sh" <<'EOT'
#!/bin/bash
f="$3"; o="$2/$(echo "$f" | tr / _).o"
if ! clang @"$1" -c "$f" -o "$o" 2> "$o.log"; then echo "ОШИБКА: $f"; head -30 "$o.log"; exit 255; fi
EOT
echo "компиляция $(wc -l < "$WORK/files.txt" | tr -d ' ') файлов..."
( cd "$P" && xargs -P "$JOBS" -I{} bash "$WORK/compile_one.sh" "$WORK/flags.rsp" "$O" {} < "$WORK/files.txt" )
clang @"$WORK/flags.rsp" -c "$WORK/info.cpp" -o "$O/zz_kmod_info.o"

SUF=""; if [ "$DIAG" = 1 ]; then SUF=-diag; fi
K="$OUT/$NAME$SUF.kext"
rm -rf "$K"; mkdir -p "$K/Contents/MacOS"
clang -arch x86_64 -isysroot "$SDK" -mmacosx-version-min=10.12 -nostdlib -Xlinker -kext \
    "$O"/*.o "$MKS/Library/x86_64/libkmod.a" -o "$K/Contents/MacOS/$NAME"
cp "$HERE/AirportMtkWlan/Info.plist" "$K/Contents/Info.plist"
plutil -lint "$K/Contents/Info.plist" >/dev/null

echo "=== проверка ==="
B="$K/Contents/MacOS/$NAME"
nm -U "$B" | grep -q ' _kmod_info$' && echo "kmod_info: есть" || { echo "kmod_info: НЕТ"; exit 1; }
nm -u "$B" | awk '{print $1}' | sort -u > "$WORK/u.txt"
kmutil libraries -p "$K" --arch x86_64 2>/dev/null | awk '/^\t\t/{print $1}' | sort -u > "$WORK/r.txt"
MISSING="$(comm -23 "$WORK/u.txt" "$WORK/r.txt" | grep -v '_RESERVED' | grep -v -E '^(_OSKextGetCurrent|_kmod_info|__realmain|__antimain)' || true)"
if [ -n "$MISSING" ]; then echo "НЕ РЕЗОЛВИТСЯ в ядре Sequoia:"; echo "$MISSING"; fi
echo "внешних символов: $(wc -l < "$WORK/u.txt" | tr -d ' '); не найдено: $(echo -n "$MISSING" | grep -c . || true)"
echo "sha1: $(shasum "$B" | cut -c1-40)"; echo "uuid: $(dwarfdump -u "$B" | awk '{print $2}')"
echo "Готово: $K"
