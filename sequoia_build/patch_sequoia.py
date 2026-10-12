#!/usr/bin/env python3
import os
import sys

root = sys.argv[1]

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

# ---- 1) куски прошивки: выделять ровно len байт ------------------------------------------------
p = root + "/SimpleMtkWlan/hal_mwx/MtkMwx.cpp"
s = read(p)

old = ("\tm = mwx_mcu_alloc_msg(len);\n"
       "\tif (m == NULL)\n"
       "\t\treturn ENOMEM;\n"
       "\n"
       "\tif (len != 0)\n"
       "\t\tmemcpy(mtod(m, caddr_t), data, len);\n"
       "\n"
       "\treturn mwx_mcu_send_mbuf(sc, cmd, m, seqp);")
assert s.count(old) == 1, "MtkMwx.cpp: не нашёл mwx_mcu_send_msg"
new = ("\tif (cmd == MCU_CMD_FW_SCATTER) {\n"
       "\t\t/*\n"
       "\t\t * Sequoia: firmware chunks are sent without a TXD, so the headspace that\n"
       "\t\t * mwx_mcu_alloc_msg() reserves is not needed. With 4096-byte chunks it made the\n"
       "\t\t * mbuf 4096+N bytes, a single-chunk mbuf_allocpacket() then asks for a 16KB jumbo\n"
       "\t\t * cluster and a non-blocking request for one fails with ENOMEM. Ask for exactly\n"
       "\t\t * len bytes: a 4KB cluster is enough.\n"
       "\t\t */\n"
       "\t\tint tries;\n"
       "\n"
       "\t\tm = NULL;\n"
       "\t\tfor (tries = 0; tries < 20 && m == NULL; tries++) {\n"
       "\t\t\tm = MCLGETL(NULL, M_DONTWAIT, len);\n"
       "\t\t\tif (m == NULL)\n"
       "\t\t\t\tdelay(1000);\n"
       "\t\t}\n"
       "\t\tif (m == NULL)\n"
       "\t\t\treturn ENOMEM;\n"
       "\t\tmbuf_setlen(m, len);\n"
       "\t\tmbuf_pkthdr_setlen(m, len);\n"
       "\t} else {\n"
       "\t\tm = mwx_mcu_alloc_msg(len);\n"
       "\t\tif (m == NULL)\n"
       "\t\t\treturn ENOMEM;\n"
       "\t}\n"
       "\n"
       "\tif (len != 0)\n"
       "\t\tmemcpy(mtod(m, caddr_t), data, len);\n"
       "\n"
       "\treturn mwx_mcu_send_mbuf(sc, cmd, m, seqp);")
s = s.replace(old, new, 1)

# ---- 2) MWX_LOG без printf (как в рабочем дереве пользователя) --------------------------------
old = ('#define MWX_LOG(x...) do { printf("SimpleMtkWlan-mwx: " x); mtk_ringlog("SimpleMtkWlan-mwx: " x); } while (0)\n'
       '#define MWX_DEV_LOG(sc, fmt, args...) \\\n'
       '\tdo { printf("SimpleMtkWlan-mwx: %s: " fmt, DEVNAME(sc), ##args); \\\n'
       '\tmtk_ringlog("SimpleMtkWlan-mwx: %s: " fmt, DEVNAME(sc), ##args); } while (0)\n')
assert s.count(old) == 1, "MtkMwx.cpp: не нашёл MWX_LOG"
new = ('/* driver messages go to the IORegistry ring buffers only (printf at 1 Hz floods the kernel log) */\n'
       '#define MWX_LOG(x...) mtk_ringlog("SimpleMtkWlan-mwx: " x)\n'
       '#define MWX_DEV_LOG(sc, fmt, args...) \\\n'
       '\tmtk_ringlog("SimpleMtkWlan-mwx: %s: " fmt, DEVNAME(sc), ##args)\n')
s = s.replace(old, new, 1)

# ---- 2b) BSS phymode: сообщаем прошивке согласованные HT/VHT, а не "только legacy" -----------------------
# Прошивка выбирает скорости передачи только из PHY-типов, перечисленных здесь. С "только A/B/G" все кадры
# (в том числе подтверждения TCP) шли на 54 Мбит/с без агрегации и упирались в ~2200 кадров/с.
old = ("\treq.basic.phymode = is_2ghz ? ((1 << 1) | (1 << 2)) : (1 << 0);\n")
assert s.count(old) == 1, "MtkMwx.cpp: не нашёл phymode в mwx_bss_connect"
new = ("\t/* bits as in mt76: A=0 B=1 G=2 GN=3 AN=4 AC=5; add what was negotiated with the AP */\n"
       "\treq.basic.phymode = is_2ghz ? ((1 << 1) | (1 << 2)) : (1 << 0);\n"
       "\tif (ni->ni_flags & IEEE80211_NODE_HT)\n"
       "\t\treq.basic.phymode |= is_2ghz ? (1 << 3) : (1 << 4);\n"
       "\tif (!is_2ghz && (ni->ni_flags & IEEE80211_NODE_VHT))\n"
       "\t\treq.basic.phymode |= (1 << 5);\n")
s = s.replace(old, new, 1)
write(p, s)

# ---- 3) режим из Info.plist: MtkMode = vht80 | ht40 | ht20 | legacy ---------------------------------
p = root + "/SimpleMtkWlan/SimpleMtkWlan.cpp"
if not os.path.exists(p):
    print("sequoia-патчи применены (без MtkMode: нет SimpleMtkWlan.cpp)")
    sys.exit(0)
s = read(p)
anchor = ("    if (!fHalService->attach(pciNub)) {\n"
          "        XYLog(\"attach fail\\n\");\n"
          "        super::stop(pciNub);\n"
          "        releaseAll();\n"
          "        return false;\n"
          "    }\n")
assert s.count(anchor) == 1, "SimpleMtkWlan.cpp: не нашёл блок attach в start()"
add = ("    {\n"
       "        /* mode switch from the Info.plist personality: <key>MtkMode</key><string>vht80|ht40|ht20|legacy</string> */\n"
       "        OSString *modeStr = OSDynamicCast(OSString, getProperty(\"MtkMode\"));\n"
       "        struct ieee80211com *mic = fHalService->get80211Controller();\n"
       "\n"
       "        /* stage B marks the channels VHT-capable but nothing ever switched VHT on in net80211 */\n"
       "        if ((modeStr == NULL || strcmp(modeStr->getCStringNoCopy(), \"vht80\") == 0) &&\n"
       "            (mic->ic_modecaps & (1 << IEEE80211_MODE_11AC)) &&\n"
       "            (mic->ic_userflags & IEEE80211_F_NOVHT) == 0)\n"
       "            mic->ic_flags |= IEEE80211_F_VHTON;\n"
       "\n"
       "        if (modeStr != NULL) {\n"
       "            const char *mm = modeStr->getCStringNoCopy();\n"
       "\n"
       "            XYLog(\"MtkMode=%s\\n\", mm);\n"
       "            if (strcmp(mm, \"legacy\") == 0) {\n"
       "                mic->ic_flags &= ~IEEE80211_F_HTON;\n"
       "                mic->ic_userflags |= IEEE80211_F_NOVHT;\n"
       "            } else if (strcmp(mm, \"ht20\") == 0) {\n"
       "                mic->ic_htcaps &= ~IEEE80211_HTCAP_CBW20_40;\n"
       "                mic->ic_userflags |= IEEE80211_F_NOVHT;\n"
       "            } else if (strcmp(mm, \"ht40\") == 0) {\n"
       "                mic->ic_userflags |= IEEE80211_F_NOVHT;\n"
       "            }\n"
       "        }\n"
       "    }\n")
s = s.replace(anchor, anchor + add, 1)
write(p, s)
print("sequoia-патчи применены")
