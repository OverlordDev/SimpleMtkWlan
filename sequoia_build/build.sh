#!/bin/bash
# Сборка SimpleMtkWlan.kext под macOS Sequoia БЕЗ Xcode (хватает Command Line Tools).
#
# Собирает исходники из бэкапа так же, как Xcode-конфигурация Debug из SimpleMtkWlan.xcodeproj,
# на которой кекст работал на Tahoe:
#   -O0, DEBUG=1, deployment target 10.9, заголовки MacKernelSDK, x86_64, тот же набор макросов.
# (Сборка с -O2 и target 10.12 даёт другой бинарь: в vtable попадает IOService::init вместо
#  IORegistryEntry::init, а код оптимизируется иначе. Это ровно то, что было в первых попытках.)
#
# Какие исходники (SOURCES="best stageB", по умолчанию оба):
#   best    ../sources/source_current.tgz                  = 1_BEST_kext_with_54M_tx_fix (режимы a/g, ~20 Мбит/с)
#   stageB  ../sources/source_stageB_vht80.tgz    = HT20/HT40/VHT80 + приём агрегированных кадров (A-MPDU RX)
#
# Патчи для Sequoia (применяются ко всем, к копии исходников; сами tgz не меняются):
#   1. Загрузка прошивки: куски по 4096 байт + заголовок давали mbuf в 4160 байт, для него
#      mbuf_allocpacket() просит 16KB jumbo-кластер, а неблокирующий запрос на него на Sequoia
#      проваливается (ENOMEM = 12), прошивка не грузится, драйвер не садится на карту.
#      Куски прошивки идут без TXD, поэтому выделяем ровно len байт (хватает 4KB-кластера).
#   2. Сообщения драйвера (MWX_LOG) не дублируются через printf в журнал ядра: на 1 Гц это шум и
#      замедление загрузки (так же поправлено в твоём рабочем дереве ~/Desktop/desk/SimpleMtkWlan).
#   3. Режим из Info.plist (без boot-args): ключ MtkMode = vht80 (по умолчанию) | ht40 | ht20 | legacy.
#   4. Агрегация отправки (TX A-MPDU), см. patch_txagg.py. Выключатель: NoTxAmpdu=true в Info.plist или boot-arg -notxampdu.
#   5. BSS RLM (канал/ширина/потоки) при подключении, см. patch_rlm.py: без него прошивка не выходит за HT MCS7 1SS.
#
# Результат (для каждого источника):
#   out/<источник>/SimpleMtkWlan.kext        обычный кекст
#   out/<источник>/SimpleMtkWlan-diag.kext   то же + дублирование лога драйвера в журнал ядра (MTKDBG ...)
#                                            и свойство MtkLog на узле WL00 (читать: ioreg -w0 -rn WL00 -l)
#
# Запуск:  bash build.sh                 (оба источника)
#          SOURCES=stageB bash build.sh  (только один)
set -e

# Работаем через Command Line Tools: не зависим от того, какой Xcode выбран в xcode-select и принята ли его лицензия.
[ -d /Library/Developer/CommandLineTools ] && export DEVELOPER_DIR="${DEVELOPER_DIR:-/Library/Developer/CommandLineTools}"

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
if [ -n "${SRC_DIR:-}" ]; then
    BACKUP="$SRC_DIR"
else
    # исходное дерево лежит в корне репозитория: пакуем его во временный tgz, как ожидает остальной скрипт
    BACKUP="$(mktemp -d)"
    tar czf "$BACKUP/source_stageB_vht80.tgz" -C "$REPO" SimpleMtkWlan mtk80211 include SimpleMtkWlan.xcodeproj
fi
SOURCES="${SOURCES:-stageB}"
MKS="${MKS:-$HERE/MacKernelSDK}"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
WORK="$HERE/build"
OUT="$HERE/out"
JOBS="$(sysctl -n hw.ncpu)"
BUNDLE_ID="com.laobamac.SimpleMtkWlan"
VERSION="1.0.0"

tgz_for() {
    case "$1" in
        best)   echo "$BACKUP/source_current.tgz" ;;
        stageB) echo "$BACKUP/source_stageB_vht80.tgz" ;;
        older)  echo "$BACKUP/source_older_stable_legacy6M.tgz" ;;
        *) echo "неизвестный источник: $1" >&2; exit 1 ;;
    esac
}

[ -f "$MKS/Library/x86_64/libkmod.a" ] || { echo "Нет MacKernelSDK: $MKS"; exit 1; }
command -v clang >/dev/null || { echo "Нет clang. Поставь Command Line Tools: xcode-select --install"; exit 1; }
for s in $SOURCES; do [ -f "$(tgz_for "$s")" ] || { echo "Нет исходников: $(tgz_for "$s")"; exit 1; }; done

echo "SDK:    $SDK"
echo "clang:  $(clang --version | head -1)"

rm -rf "$WORK"
mkdir -p "$WORK" "$OUT"

# ---------------------------------------------------------------------------------------------
# патч для diag-варианта
# ---------------------------------------------------------------------------------------------
cp "$HERE/patch_diag.py" "$WORK/patch_diag.py"

# ---------------------------------------------------------------------------------------------
# патчи для Sequoia (все варианты)
# ---------------------------------------------------------------------------------------------
cp "$HERE/patch_sequoia.py" "$WORK/patch_sequoia.py"

# ---------------------------------------------------------------------------------------------
# kmod_info (в Xcode его генерирует отдельный шаг; без него OpenCore отвергает кекст: "Invalid Parameter")
# _start/_stop определены в ieee80211.c, а он компилируется как C++, поэтому имена C++-манглированные.
# ---------------------------------------------------------------------------------------------
cat > "$WORK/SimpleMtkWlan_info.cpp" <<EOF
#include <mach/mach_types.h>
extern kern_return_t _start(kmod_info_t *ki, void *data);
extern kern_return_t _stop(kmod_info_t *ki, void *data);
__attribute__((visibility("default"))) KMOD_EXPLICIT_DECL($BUNDLE_ID, "$VERSION", _start, _stop)
__private_extern__ kmod_start_func_t *_realmain = 0;
__private_extern__ kmod_stop_func_t *_antimain = 0;
__private_extern__ int _kext_apple_cc = __APPLE_CC__;
EOF

build_variant() {
    local src="$1" diag="$2"
    local kind; kind="$([ "$diag" = 1 ] && echo diag || echo plain)"
    local name="$src-$kind"
    local P="$WORK/$name/src" O="$WORK/$name/obj"
    local TGZ; TGZ="$(tgz_for "$src")"
    mkdir -p "$P" "$O"
    tar xzf "$TGZ" -C "$P"
    python3 -I "$WORK/patch_sequoia.py" "$P"
    python3 -I "$HERE/patch_txagg.py" "$P"
    python3 -I "$HERE/patch_rlm.py" "$P"
    if [ "$diag" = 1 ]; then
        python3 -I "$WORK/patch_diag.py" "$P"
    fi

    # флаги = то, что даёт Xcode для Debug-конфигурации этого проекта
    cat > "$WORK/$name/flags.rsp" <<EOF
-arch x86_64
-isysroot $SDK
-mmacosx-version-min=10.9
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
-DSMTW_VERSION=\"$VERSION\"
-DGIT_COMMIT=\"\"
-isystem $P/mtk80211/openbsd
-isystem $P/mtk80211
-isystem $P/include
-I$P/mtk80211/linux
-I$P/mtk80211/openbsd/crypto
-I$P
-I$P/SimpleMtkWlan
-I$P/SimpleMtkWlan/hal_mwx
-I$MKS/Headers
-include $P/SimpleMtkWlan/PrivateSPI.pch
EOF
    [ "$diag" = 1 ] && echo "-DMTK_DIAG_IOLOG" >> "$WORK/$name/flags.rsp"

    echo "[$name] компиляция..."
    ( cd "$P" && find SimpleMtkWlan mtk80211 include \( -name '*.c' -o -name '*.cpp' \) | sort ) > "$WORK/$name/files.txt"
    # clang -x c++ для всех файлов, как GCC_INPUT_FILETYPE=sourcecode.cpp.cpp в проекте
    cat > "$WORK/$name/compile_one.sh" <<'EOS'
#!/bin/bash
# compile_one.sh <flags.rsp> <objdir> <file>
f="$3"; o="$2/$(echo "$f" | tr / _).o"
if ! clang @"$1" -c "$f" -o "$o" 2> "$o.log"; then echo "ОШИБКА: $f"; head -20 "$o.log"; exit 255; fi
EOS
    ( cd "$P" && xargs -P "$JOBS" -I{} bash "$WORK/$name/compile_one.sh" "$WORK/$name/flags.rsp" "$O" {} < "$WORK/$name/files.txt" )
    clang @"$WORK/$name/flags.rsp" -c "$WORK/SimpleMtkWlan_info.cpp" -o "$O/zz_kmod_info.o"

    echo "[$name] линковка..."
    local K="$OUT/$src/$([ "$diag" = 1 ] && echo SimpleMtkWlan-diag || echo SimpleMtkWlan).kext"
    rm -rf "$K"
    mkdir -p "$K/Contents/MacOS"
    clang -arch x86_64 -isysroot "$SDK" -mmacosx-version-min=10.9 -nostdlib -Xlinker -kext \
        "$O"/*.o "$MKS/Library/x86_64/libkmod.a" -o "$K/Contents/MacOS/SimpleMtkWlan"

    # Info.plist: подстановка переменных Xcode в исходный plist проекта
    sed -e 's/\$(DEVELOPMENT_LANGUAGE)/en/' \
        -e 's/\$(EXECUTABLE_NAME)/SimpleMtkWlan/' \
        -e "s/\\\$(PRODUCT_BUNDLE_IDENTIFIER)/$BUNDLE_ID/" \
        -e 's/\$(PRODUCT_NAME)/SimpleMtkWlan/' \
        -e 's/\$(PRODUCT_BUNDLE_PACKAGE_TYPE)/KEXT/' \
        -e "s/\\\$(MODULE_VERSION)/$VERSION/g" \
        "$P/SimpleMtkWlan/Info.plist" > "$K/Contents/Info.plist"
    # канонический XML без комментариев (парсеры вроде OpenCore не любят комментарий перед DOCTYPE)
    plutil -convert xml1 "$K/Contents/Info.plist"
    plutil -lint "$K/Contents/Info.plist" >/dev/null

    # патченные исходники рядом с кекстом: по номерам строк из лога ("return false at line N") находится место
    mkdir -p "$OUT/$src/patched-sources-$kind"
    cp "$P/SimpleMtkWlan/SimpleMtkWlan.cpp" "$P/mtk80211/compat.cpp" "$P/SimpleMtkWlan/hal_mwx/MtkMwx.cpp" "$OUT/$src/patched-sources-$kind/"
    echo "[$name] готово: $K"
}

for s in $SOURCES; do
    rm -rf "$OUT/$s"
    build_variant "$s" 0
    build_variant "$s" 1
done

# ---------------------------------------------------------------------------------------------
# проверки
# ---------------------------------------------------------------------------------------------
echo
echo "=== проверка ==="
for K in $(for s in $SOURCES; do echo "$OUT/$s/"*.kext; done); do
    B="$K/Contents/MacOS/SimpleMtkWlan"
    echo "--- ${K#$OUT/}"
    nm -U "$B" | grep -q ' _kmod_info$' && echo "kmod_info:        есть" || { echo "kmod_info:        НЕТ"; exit 1; }
    nm -U "$B" | grep -q '__Z6_startP9kmod_infoPv' && echo "_start/_stop:     есть" || { echo "_start/_stop:     НЕТ"; exit 1; }
    nm -u "$B" | awk '{print $1}' | sort -u > "$WORK/u.txt"
    kmutil libraries -p "$K" --arch x86_64 2>/dev/null | awk '/^\t\t/{print $1}' | sort -u > "$WORK/r.txt"
    # _RESERVED* слоты vtable kmutil в список не выводит, они резолвятся ядром
    MISSING="$(comm -23 "$WORK/u.txt" "$WORK/r.txt" | grep -v '_RESERVED' | grep -v -E '^(_OSKextGetCurrent|_kmod_info|__realmain|__antimain)' || true)"
    if [ -n "$MISSING" ]; then echo "НЕ РЕЗОЛВИТСЯ в ядре Sequoia:"; echo "$MISSING"; exit 1; fi
    echo "символы:          все $(wc -l < "$WORK/u.txt" | tr -d ' ') внешних символов найдены в ядре этой системы"
    echo "sha1:             $(shasum "$B" | cut -c1-40)"
    echo "uuid:             $(dwarfdump -u "$B" | awk '{print $2}')"
done
[ "${KEEP_BUILD:-0}" = 1 ] || rm -rf "$WORK"
echo
echo "Готово. Кексты лежат в $OUT"
