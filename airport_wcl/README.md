# AirportMtkWlan — native Wi‑Fi (WCL) build for macOS Sequoia 15.x

MT7921/MT7922 as the **system Wi‑Fi** (menu bar toggle, network list, WPA2), via the
IO80211Family Skywalk/WCL path (`IO80211InfraProtocol`), instead of a plain Ethernet-type interface.

- `src/` — controller/interface glue (AirportMtkWlan*), ported from laobamac/itlwm `AirportItlwm` (GPL‑2.0), HAL = SimpleMtkWlan `MtkMwx`.
- `include/Airport/` — IO80211/Skywalk headers (reference set from itlwm incl. macOS15).
- `patch_wcl_net80211.py` — adds WCL hooks to the net80211 layer / MtkMwx at build time (all under `AIRPORT_WCL`).
- `build_airport_wcl.sh` — clang-only build (no Xcode), deployment target 15.2; needs `../sequoia_build` patches + MacKernelSDK.
- `install_airport_to_stick.sh` — installs into an OpenCore USB EFI under the existing SimpleMtkWlan.kext path, with backup/`restore`.

Notes: deployment target must be 15.2 (otherwise `IO80211InterfaceRole` is never published); HAL must emit
`DRIVER_READY`/`DRIVER_STOPPED`; the interface's own address must follow the ifnet lladdr (private Wi‑Fi address).
Status: scan, association, WPA2, DHCP and traffic work on MT7921 / Sequoia 15.8.1 (x86_64 Hackintosh).

Fast start / scanning (v1.1):
- MCU command waits poll the interrupt themselves: `enable`/`disable` run under the command gate on the same workloop
  as the interrupt handler, so responses used to be processed only after a 3 s timeout (long start, 9 s stop).
- Firmware deep sleep is disabled right after firmware load (waking it took ~2 s).
- Scans requested from the Wi-Fi menu are allowed while associated; automatic background scans stay suppressed.
- A never-rolling `MtkBoot` ioreg property keeps the start-up log of the driver.

Not supported: AirDrop/AWDL (needs a separate awdl0 interface).
