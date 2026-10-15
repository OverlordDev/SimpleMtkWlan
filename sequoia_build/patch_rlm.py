#!/usr/bin/env python3
"""
BSS RLM для SimpleMtkWlan (MT7921): канал, центральный канал, ширина, число потоков.

В Linux mt76 (mt76_connac_mcu_uni_add_bss) после BSS_INFO_BASIC шлётся ещё один запрос BSS_INFO_UPDATE
с TLV UNI_BSS_INFO_RLM. В порте mwx_bss_connect() он пропущен (в заголовке UNI_BSS_INFO_RLM объявлен,
но нигде не используется). Без него у BSS остаются значения по умолчанию, и прошивка не выходит за
HT MCS7, один поток, хотя приём идёт на VHT80 2x2.

Применяется build.sh к копии исходников (только для источников с HT/VHT, т.е. stageB).
"""
import sys

root = sys.argv[1]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


p = root + "/SimpleMtkWlan/hal_mwx/MtkMwx.cpp"
s = read(p)

if "mwx_ba_task" not in s:
    print("rlm: источник без HT/VHT, пропускаю")
    sys.exit(0)

old = ("\tMWX_DEV_LOG(sc, \"bss connect bssid=%s bcn=%u dtim=%u wcid=%u 2ghz=%d\\n\",\n"
       "\t    ether_sprintf(ni->ni_bssid), ni->ni_intval, req.basic.dtim_period,\n"
       "\t    mvif->vif_mn.wcid, is_2ghz);\n"
       "\treturn mwx_mcu_send_wait(sc, MCU_UNI_CMD_BSS_INFO_UPDATE, &req,\n"
       "\t    sizeof(req));\n"
       "}\n")
assert s.count(old) == 1, "MtkMwx.cpp: не нашёл конец mwx_bss_connect"

new = (
    "\tMWX_DEV_LOG(sc, \"bss connect bssid=%s bcn=%u dtim=%u wcid=%u 2ghz=%d\\n\",\n"
    "\t    ether_sprintf(ni->ni_bssid), ni->ni_intval, req.basic.dtim_period,\n"
    "\t    mvif->vif_mn.wcid, is_2ghz);\n"
    "\t{\n"
    "\t\tint rrv;\n"
    "\n"
    "\t\trrv = mwx_mcu_send_wait(sc, MCU_UNI_CMD_BSS_INFO_UPDATE, &req,\n"
    "\t\t    sizeof(req));\n"
    "\t\tif (rrv != 0)\n"
    "\t\t\treturn rrv;\n"
    "\t}\n"
    "\n"
    "\t/*\n"
    "\t * BSS RLM (as the rlm request in mt76_connac_mcu_uni_add_bss): control/centre channel,\n"
    "\t * bandwidth and stream counts. Without it the firmware keeps the BSS at 20 MHz/defaults\n"
    "\t * and its rate control never goes above HT MCS7, one stream.\n"
    "\t */\n"
    "\t{\n"
    "\t\tstruct {\n"
    "\t\t\tstruct {\n"
    "\t\t\t\tuint8_t\t\tbss_idx;\n"
    "\t\t\t\tuint8_t\t\tpad[3];\n"
    "\t\t\t} __packed hdr;\n"
    "\t\t\tstruct {\n"
    "\t\t\t\tuint16_t\ttag;\n"
    "\t\t\t\tuint16_t\tlen;\n"
    "\t\t\t\tuint8_t\t\tcontrol_channel;\n"
    "\t\t\t\tuint8_t\t\tcenter_chan;\n"
    "\t\t\t\tuint8_t\t\tcenter_chan2;\n"
    "\t\t\t\tuint8_t\t\tbw;\n"
    "\t\t\t\tuint8_t\t\ttx_streams;\n"
    "\t\t\t\tuint8_t\t\trx_streams;\n"
    "\t\t\t\tuint8_t\t\tshort_st;\n"
    "\t\t\t\tuint8_t\t\tht_op_info;\n"
    "\t\t\t\tuint8_t\t\tsco;\n"
    "\t\t\t\tuint8_t\t\tpad[3];\n"
    "\t\t\t} __packed rlm;\n"
    "\t\t} rreq;\n"
    "\t\tstruct ieee80211_channel *chan = ni->ni_chan;\n"
    "\t\tint rrv;\n"
    "\n"
    "\t\tmemset(&rreq, 0, sizeof(rreq));\n"
    "\t\trreq.hdr.bss_idx = mvif->idx;\n"
    "\t\trreq.rlm.tag = htole16(UNI_BSS_INFO_RLM);\n"
    "\t\trreq.rlm.len = htole16(sizeof(rreq.rlm));\n"
    "\t\trreq.rlm.control_channel = ieee80211_mhz2ieee(chan->ic_freq, chan->ic_flags);\n"
    "\t\trreq.rlm.center_chan = rreq.rlm.control_channel;\n"
    "\t\trreq.rlm.bw = CMD_CBW_20MHZ;\n"
    "\t\tswitch (ni->ni_chw) {\n"
    "\t\tcase IEEE80211_CHAN_WIDTH_40:\n"
    "\t\t\trreq.rlm.bw = CMD_CBW_40MHZ;\n"
    "\t\t\tbreak;\n"
    "\t\tcase IEEE80211_CHAN_WIDTH_80:\n"
    "\t\t\trreq.rlm.bw = CMD_CBW_80MHZ;\n"
    "\t\t\tbreak;\n"
    "\t\tcase IEEE80211_CHAN_WIDTH_160:\n"
    "\t\t\trreq.rlm.bw = CMD_CBW_160MHZ;\n"
    "\t\t\tbreak;\n"
    "\t\tdefault:\n"
    "\t\t\tbreak;\n"
    "\t\t}\n"
    "\t\tif (rreq.rlm.bw != CMD_CBW_20MHZ && chan->ic_center_freq1 != 0)\n"
    "\t\t\trreq.rlm.center_chan = ieee80211_mhz2ieee(chan->ic_center_freq1,\n"
    "\t\t\t    chan->ic_flags);\n"
    "\t\trreq.rlm.tx_streams = sc->sc_capa.num_streams ? sc->sc_capa.num_streams : 1;\n"
    "\t\trreq.rlm.rx_streams = sc->sc_capa.antenna_mask ? sc->sc_capa.antenna_mask : 1;\n"
    "\t\trreq.rlm.short_st = 1;\n"
    "\t\trreq.rlm.ht_op_info = (rreq.rlm.bw != CMD_CBW_20MHZ) ? 4 : 0;\t/* 40 MHz allowed */\n"
    "\t\tif (rreq.rlm.control_channel < rreq.rlm.center_chan)\n"
    "\t\t\trreq.rlm.sco = 1;\t/* SCA */\n"
    "\t\telse if (rreq.rlm.control_channel > rreq.rlm.center_chan)\n"
    "\t\t\trreq.rlm.sco = 3;\t/* SCB */\n"
    "\n"
    "\t\trrv = mwx_mcu_send_wait(sc, MCU_UNI_CMD_BSS_INFO_UPDATE, &rreq,\n"
    "\t\t    sizeof(rreq));\n"
    "\t\tMWX_DEV_LOG(sc, \"HB bss rlm ctrl=%u center=%u bw=%u tx_streams=%u rx_streams=0x%x sco=%u rv=%d\\n\",\n"
    "\t\t    rreq.rlm.control_channel, rreq.rlm.center_chan, rreq.rlm.bw,\n"
    "\t\t    rreq.rlm.tx_streams, rreq.rlm.rx_streams, rreq.rlm.sco, rrv);\n"
    "\t\treturn rrv;\n"
    "\t}\n"
    "}\n")
s = s.replace(old, new, 1)
write(p, s)
print("rlm-патч применён")
