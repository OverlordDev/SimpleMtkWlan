#!/usr/bin/env python3
"""
TX A-MPDU (block ack originator) для SimpleMtkWlan на MT7921.

Применяется build.sh к КОПИИ исходников (stageB), сам tgz не меняется.
Пропускается для источников без RX-блока BA (best): там нет HT вообще.

Что делает:
  1. caps: IEEE80211_C_QOS | IEEE80211_C_TX_AMPDU. Без них net80211 никогда не просит ADDBA.
  2. ic_ampdu_tx_start / ic_ampdu_tx_stop. net80211 сам шлёт ADDBA request, а когда роутер соглашается,
     зовёт ic_ampdu_tx_start. Прошивку программируем из очереди задач (MCU-команды спят),
     потом принимаем или отклоняем соглашение.
  3. mt7921_mcu_uni_tx_ba(): WTBL_BA + STA_REC_BA в роли originator (раскладка как в Linux mt76,
     mt76_connac_mcu_sta_ba с tx=true). Агрегирует и повторяет кадры уже железо.
  4. net80211: размер окна из ADDBA response сохраняется (раньше терялся).
  5. Переключатель: ключ NoTxAmpdu (bool) в Info.plist или boot-arg -notxampdu отключает агрегацию отправки.
"""
import os
import sys

root = sys.argv[1]


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def tabify(block):
    """4 пробела в начале строки -> табуляция (исходники драйвера с табами)."""
    out = []
    for line in block.split("\n"):
        n = len(line) - len(line.lstrip(" "))
        out.append("\t" * (n // 4) + " " * (n % 4) + line[n:])
    return "\n".join(out)


def replace_once(s, old, new, what):
    assert s.count(old) == 1, "не нашёл (или не один) якорь: " + what
    return s.replace(old, new, 1)


p = root + "/SimpleMtkWlan/hal_mwx/MtkMwx.cpp"
s = read(p)

if "mwx_ba_task" not in s:
    print("txagg: нет RX-блока BA в этом источнике, пропускаю")
    sys.exit(0)

# ---- 1) структура задачи BA: направление ------------------------------------------------------------
s = replace_once(
    s,
    "struct mwx_ba_task_arg {\n\tstruct ieee80211_node\t*ni;\n\tint\t\t\ttid;\n\tint\t\t\tstart;\n};",
    "struct mwx_ba_task_arg {\n\tstruct ieee80211_node\t*ni;\n\tint\t\t\ttid;\n\tint\t\t\tstart;\n"
    "\tint\t\t\ttx;\t/* 1: originator (TX) agreement, 0: recipient (RX) */\n};",
    "struct mwx_ba_task_arg")

# ---- 2) прототипы ---------------------------------------------------------------------------------------
s = replace_once(
    s,
    "int\tmt7921_mcu_uni_rx_ba(struct mwx_softc *, struct ieee80211_node *, int, int);\n",
    "int\tmt7921_mcu_uni_rx_ba(struct mwx_softc *, struct ieee80211_node *, int, int);\n"
    "int\tmwx_ampdu_tx_start(struct ieee80211com *, struct ieee80211_node *, uint8_t);\n"
    "void\tmwx_ampdu_tx_stop(struct ieee80211com *, struct ieee80211_node *, uint8_t);\n"
    "int\tmt7921_mcu_uni_tx_ba(struct mwx_softc *, struct ieee80211_node *, int, int);\n",
    "прототипы BA")

# ---- 3) задача BA: ветка originator -------------------------------------------------------------------
s = replace_once(
    s,
    "\t\tint tid = a->tid, start = a->start;\n"
    "\n"
    "\t\tsc->sc_ba_tail = (sc->sc_ba_tail + 1) % nitems(sc->sc_ba_arg);\n"
    "\t\tif (start) {\n",
    tabify(
        "        int tid = a->tid, start = a->start, tx = a->tx;\n"
        "\n"
        "        sc->sc_ba_tail = (sc->sc_ba_tail + 1) % nitems(sc->sc_ba_arg);\n"
        "        if (tx) {\n"
        "            /* originator: program the firmware, then accept or refuse the agreement */\n"
        "            if (start) {\n"
        "                int rv = EIO;\n"
        "\n"
        "                if (ic->ic_state == IEEE80211_S_RUN && ni == ic->ic_bss)\n"
        "                    rv = mt7921_mcu_uni_tx_ba(sc, ni, tid, 1);\n"
        "                if (rv == 0)\n"
        "                    ieee80211_addba_resp_accept(ic, ni, tid);\n"
        "                else\n"
        "                    ieee80211_addba_resp_refuse(ic, ni, tid,\n"
        "                        IEEE80211_STATUS_UNSPECIFIED);\n"
        "            } else if (ic->ic_state == IEEE80211_S_RUN && ni == ic->ic_bss) {\n"
        "                mt7921_mcu_uni_tx_ba(sc, ni, tid, 0);\n"
        "            }\n"
        "            continue;\n"
        "        }\n"
        "        if (start) {\n") ,
    "mwx_ba_task")
# tabify оставил ведущие 8 пробелов как 2 таба — но исходная строка начинается с 2 табов, значит ок

# ---- 4) RX start/stop явно ставят tx = 0 ----------------------------------------------------------------
s = replace_once(s, "\ta->start = 1;\n\tsc->sc_ba_cur", "\ta->start = 1;\n\ta->tx = 0;\n\tsc->sc_ba_cur",
                 "mwx_ampdu_rx_start")

# ---- 5) TX start/stop + mt7921_mcu_uni_tx_ba: после mwx_ampdu_rx_stop ----------------------------------
old_tail = ("\ta->start = 0;\n"
            "\tsc->sc_ba_cur = (sc->sc_ba_cur + 1) % nitems(sc->sc_ba_arg);\n"
            "\ttask_add(sc->sc_nswq, &sc->sc_ba_task);\n"
            "}\n")
new_funcs = tabify('''
/*
 * TX A-MPDU (block ack originator). net80211 sends the ADDBA request itself and calls
 * ic_ampdu_tx_start once the AP has accepted. MCU commands sleep, so the firmware setup
 * (WTBL_BA + STA_REC_BA, layout as in Linux mt76) runs from the task queue and the agreement is
 * accepted or refused afterwards. The hardware then builds the A-MPDUs and handles the block
 * ack scoreboard and the retries.
 */
int
mwx_ampdu_tx_start(struct ieee80211com *ic, struct ieee80211_node *ni,
    uint8_t tid)
{
    struct mwx_softc *sc = (struct mwx_softc *)ic->ic_softc;
    struct mwx_ba_task_arg *a;

    if ((sc->sc_ba_cur + 1) % nitems(sc->sc_ba_arg) == sc->sc_ba_tail)
        return ENOSPC;
    a = &sc->sc_ba_arg[sc->sc_ba_cur];
    a->ni = ni;
    a->tid = tid;
    a->start = 1;
    a->tx = 1;
    sc->sc_ba_cur = (sc->sc_ba_cur + 1) % nitems(sc->sc_ba_arg);
    task_add(sc->sc_nswq, &sc->sc_ba_task);
    return EBUSY;    /* task accepts or refuses the agreement */
}

void
mwx_ampdu_tx_stop(struct ieee80211com *ic, struct ieee80211_node *ni,
    uint8_t tid)
{
    struct mwx_softc *sc = (struct mwx_softc *)ic->ic_softc;
    struct mwx_ba_task_arg *a;

    if ((sc->sc_ba_cur + 1) % nitems(sc->sc_ba_arg) == sc->sc_ba_tail)
        return;
    a = &sc->sc_ba_arg[sc->sc_ba_cur];
    a->ni = ni;
    a->tid = tid;
    a->start = 0;
    a->tx = 1;
    sc->sc_ba_cur = (sc->sc_ba_cur + 1) % nitems(sc->sc_ba_arg);
    task_add(sc->sc_nswq, &sc->sc_ba_task);
}

int
mt7921_mcu_uni_tx_ba(struct mwx_softc *sc, struct ieee80211_node *ni, int tid,
    int enable)
{
    static const uint16_t ba_range[] = { 4, 8, 12, 24, 36, 48, 54, 64 };
    struct mwx_node *mn = (struct mwx_node *)ni;
    struct mwx_vif *mvif = &sc->sc_vif;
    struct ieee80211_tx_ba *tba = &ni->ni_tx_ba[tid];
    struct sta_rec_wtbl *wtbl;
    struct wtbl_ba *wba;
    struct sta_rec_ba *sba;
    struct mbuf *m;
    uint16_t tlvnum = 0, wnum = 0;
    uint16_t winsize = tba->ba_winsize;
    uint16_t ssn = tba->ba_winstart;
    int i, rv;

    if (winsize == 0 || winsize > IEEE80211_BA_MAX_WINSZ)
        winsize = IEEE80211_BA_MAX_WINSZ;

    /* 1. WTBL block ack entry (originator) */
    m = mwx_alloc_sta_req_tlv(sizeof(struct sta_req_hdr));
    if (m == NULL)
        return ENOBUFS;
    wtbl = (struct sta_rec_wtbl *)mwx_append_tlv(m, &tlvnum, STA_REC_WTBL,
        sizeof(*wtbl));
    wtbl->wlan_idx_lo = mn->wcid & 0xff;
    wtbl->wlan_idx_hi = mn->wcid >> 8;
    wtbl->operation = WTBL_SET;

    wba = (struct wtbl_ba *)mwx_append_tlv(m, &wnum, WTBL_BA, sizeof(*wba));
    wba->tid = tid;
    wba->ba_type = MT_BA_TYPE_ORIGINATOR;
    if (enable) {
        wba->sn = htole16(ssn);
        wba->ba_winsize = htole16(winsize);
        wba->ba_en = 1;
        for (i = 7; i > 0; i--)
            if (winsize >= ba_range[i])
                break;
        wba->ba_winsize_idx = i;
    }

    wtbl->tlv_num = htole16(wnum);
    wtbl->len = htole16(le16toh(wtbl->len) + sizeof(*wba));

    m = mwx_fill_sta_req_hdr(m, mvif, mvif->omac_idx, mn->wcid, tlvnum);
    if (m == NULL)
        return ENOBUFS;
    rv = mwx_mcu_send_mbuf_wait(sc, MCU_UNI_CMD_STA_REC_UPDATE, m);
    MWX_DEV_LOG(sc, "HB tx ba wtbl tid=%d en=%d win=%u ssn=%u wcid=%u rv=%d\\n",
        tid, enable, winsize, ssn, mn->wcid, rv);
    if (rv)
        return rv;

    /* 2. station record block ack */
    tlvnum = 0;
    m = mwx_alloc_sta_req_tlv(sizeof(struct sta_req_hdr));
    if (m == NULL)
        return ENOBUFS;
    sba = (struct sta_rec_ba *)mwx_append_tlv(m, &tlvnum, STA_REC_BA,
        sizeof(*sba));
    sba->tid = tid;
    sba->ba_type = MT_BA_TYPE_ORIGINATOR;
    sba->winsize = htole16(winsize);
    sba->ssn = htole16(ssn);
    sba->ba_en = enable ? (1U << tid) : 0;
    sba->amsdu = 0;

    m = mwx_fill_sta_req_hdr(m, mvif, mvif->omac_idx, mn->wcid, tlvnum);
    if (m == NULL)
        return ENOBUFS;
    rv = mwx_mcu_send_mbuf_wait(sc, MCU_UNI_CMD_STA_REC_UPDATE, m);
    MWX_DEV_LOG(sc, "HB tx ba sta tid=%d en=%d rv=%d\\n", tid, enable, rv);
    return rv;
}
''')
s = replace_once(s, old_tail, old_tail + new_funcs, "конец mwx_ampdu_rx_stop")

# ---- 6) caps: QoS + TX A-MPDU (net80211 сам пошлёт ADDBA, поэтому без ADDBA_OFFLOAD) -------------------
s = replace_once(
    s,
    "#if NOTYET\n"
    "\t    IEEE80211_C_QOS | IEEE80211_C_TX_AMPDU | /* A-MPDU */\n"
    "\t    IEEE80211_C_ADDBA_OFFLOAD | /* device sends ADDBA/DELBA frames */\n"
    "#endif\n",
    "\t    IEEE80211_C_QOS | IEEE80211_C_TX_AMPDU | /* A-MPDU */\n",
    "ic_caps")

# ---- 7) хуки ----------------------------------------------------------------------------------------------
s = replace_once(
    s,
    "\tic->ic_ampdu_rx_stop = mwx_ampdu_rx_stop;\n",
    "\tic->ic_ampdu_rx_stop = mwx_ampdu_rx_stop;\n"
    "\tic->ic_ampdu_tx_start = mwx_ampdu_tx_start;\n"
    "\tic->ic_ampdu_tx_stop = mwx_ampdu_tx_stop;\n",
    "хуки tx_start/stop")
write(p, s)

# ---- 8) net80211: запомнить размер окна из ADDBA response ----------------------------------------------
p = root + "/mtk80211/openbsd/net80211/ieee80211_input.c"
s = read(p)
s = replace_once(
    s,
    "    /* notify drivers of this new Block Ack agreement */\n"
    "    if (ic->ic_ampdu_tx_start != NULL)\n"
    "        err = ic->ic_ampdu_tx_start(ic, ni, tid);\n",
    "    /* the AP may grant a smaller window than we asked for */\n"
    "    if (bufsz != 0 && bufsz < ba->ba_winsize)\n"
    "        ba->ba_winsize = bufsz;\n"
    "\n"
    "    /* notify drivers of this new Block Ack agreement */\n"
    "    if (ic->ic_ampdu_tx_start != NULL)\n"
    "        err = ic->ic_ampdu_tx_start(ic, ni, tid);\n",
    "ADDBA response -> tx_start")
write(p, s)

# ---- 9) выключатель: Info.plist NoTxAmpdu или boot-arg -notxampdu ---------------------------------------
p = root + "/SimpleMtkWlan/SimpleMtkWlan.cpp"
if not os.path.exists(p):
    print("txagg-патч применён (без выключателя: нет SimpleMtkWlan.cpp)")
    sys.exit(0)
s = read(p)
anchor = "            XYLog(\"MtkMode=%s\\n\", mm);\n"
assert s.count(anchor) == 1, "SimpleMtkWlan.cpp: нет блока MtkMode (сначала должен примениться patch_sequoia)"
marker = "        if (modeStr != NULL) {\n"
assert s.count(marker) == 1
switch = (
    "        {\n"
    "            OSBoolean *noagg = OSDynamicCast(OSBoolean, getProperty(\"NoTxAmpdu\"));\n"
    "            int dummy = 0;\n"
    "\n"
    "            if ((noagg != NULL && noagg->isTrue()) ||\n"
    "                PE_parse_boot_argn(\"-notxampdu\", &dummy, sizeof(dummy))) {\n"
    "                mic->ic_caps &= ~IEEE80211_C_TX_AMPDU;\n"
    "                XYLog(\"TX A-MPDU disabled\\n\");\n"
    "            }\n"
    "        }\n"
    "\n")
# вставляем перед "if (modeStr != NULL) {" внутри нашего блока
s = s.replace(marker, switch + marker, 1)
write(p, s)
print("txagg-патч применён")
