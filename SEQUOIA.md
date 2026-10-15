# macOS Sequoia port — status, release and build notes

Community build of **SimpleMtkWlan** that runs on **macOS Sequoia 15.x (tested on 15.8.1, x86_64)** with the
MediaTek **MT7921 / MT7961 (PCI `14c3:7961`)** PCIe card, injected by OpenCore.

> Fork of [laobamac/SimpleMtkWlan](https://github.com/laobamac/SimpleMtkWlan) (GPL-2.0). Kernel code — no warranty. Keep a working EFI.

## Status (measured on one laptop, MT7921, 2×2, 5 GHz / 80 MHz AP)

| | before (Tahoe build as-is) | this build |
|---|---|---|
| attaches on Sequoia | no (`patch send failed error=12`) | **yes** |
| download | ~13 Mbit/s | **~300 Mbit/s** (Ookla 302) |
| upload | ~19 Mbit/s | **~226 Mbit/s** |
| PHY | legacy a/g | **VHT80 2SS MCS8–9** both directions |

Works as a plain Ethernet-type interface (`en*`). It does **not** appear in the system Wi-Fi menu (see *Experimental*).

## What was fixed for Sequoia

1. **Firmware load**: firmware chunks are 4096 B + 64 B TXD headspace. `mbuf_allocpacket(len, maxchunks=1)` wants a 16 KB jumbo
   cluster and fails with `ENOMEM` on Sequoia. Chunks are now allocated with their exact length (+ retry).
2. **BSS PHY mode** reported to the firmware includes HT/VHT; `IEEE80211_F_VHTON` is set explicitly.
3. **TX A-MPDU originator** (ADDBA → `WTBL_BA` + `STA_REC_BA`, like Linux mt76).
4. **BSS RLM TLV** (`UNI_BSS_INFO_RLM`: channel/bandwidth/streams) after BSS basic — without it the firmware stayed at HT MCS7 1SS.
5. Reproducible **clang-only build** (Command Line Tools, no Xcode needed).

## Use (OpenCore)

1. Download `SimpleMtkWlan-stageB-sequoia-15.8.1.kext.zip` from Releases (verify `SHA256SUMS.txt`).
2. Put `SimpleMtkWlan.kext` into `EFI/OC/Kexts`, add it to `Kernel → Add` (the kext is built with `OSBundleRequired = Network-Root`).
3. Optional keys in the personality (`Info.plist`): `MtkMode` = `vht80` (default) | `ht40` | `ht20` | `legacy`, `NoTxAmpdu` = `true`.
4. `-diag` build additionally publishes `MtkLog` / `MtkHB` on the PCI node (`ioreg -w0 -rn WL00 -l`).

## Build

```bash
git clone https://github.com/acidanthera/MacKernelSDK sequoia_build/MacKernelSDK
cd sequoia_build && bash build.sh        # needs only Xcode Command Line Tools
# result: sequoia_build/out/stageB/SimpleMtkWlan{,-diag}.kext
```
`build.sh` packs the source tree of this repository, applies `sequoia_build/patch_*.py` to a copy, compiles with the same flags as the
original Debug/Xcode build (-O0, deployment target 10.9, MacKernelSDK) and verifies that all external symbols resolve in the
running kernel (`kmutil libraries`). The upstream Xcode project (`xcodebuild -project SimpleMtkWlan.xcodeproj`) still works; the
Sequoia-specific patches (firmware chunk allocation, MtkMode/NoTxAmpdu switches) are applied only by `build.sh`.

## Experimental: native Wi-Fi (IO80211) on Sequoia — not working yet

`experimental/` contains an AirportItlwm-style port (`AirportMtkWlan`) and tooling that reconstructs the **real Sequoia IO80211Family
ABI** from the kernel collection (vtable dump, disassembler wrapper, header generator, clang-vs-kernel vtable checker).
On hardware the driver gets through Family controller start, firmware, interface init/attach and BSD-interface registration, then the
machine dies inside `IO80211SkywalkInterface::start / IO80211InfraInterface::start` very early in boot (no panic report survives).
Findings are in `experimental/sequoia_abi/README.txt`. Contributions welcome.

## Layout of the additions

```
sequoia_build/      build.sh, patch_*.py, install_to_stick.sh
experimental/       AirportMtkWlan glue, generated Sequoia headers, IO80211 ABI tooling (not working yet)
```
The driver sources (`SimpleMtkWlan/`, `mtk80211/`, `include/`) are upstream's tree plus the changes listed above.
