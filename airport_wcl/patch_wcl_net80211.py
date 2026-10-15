#!/usr/bin/env python3
"""Минимальные изменения net80211 (mtk80211) под слой WCL из laobamac/itlwm (AirportItlwm Sequoia).
Применяется к копии исходников: patch_wcl_net80211.py <root>. Все правки под #ifdef AIRPORT_WCL."""
import sys
root = sys.argv[1]
N = root + "/mtk80211/openbsd/net80211/"
def rd(p): return open(p, encoding="utf-8").read()
def wr(p, s): open(p, "w", encoding="utf-8").write(s)
def rep(f, old, new, tag):
    s = rd(N + f)
    assert s.count(old) >= 1, "%s: не найдено (%s)" % (f, tag)
    wr(N + f, s.replace(old, new, 1))

# --- ieee80211_var.h
rep("ieee80211_var.h",
    "    void            (*ic_update_chw)(struct ieee80211com *);\n",
    "    void            (*ic_update_chw)(struct ieee80211com *);\n"
    "#ifdef AIRPORT_WCL\n"
    "    bool ic_wcl_mac_reconfig;\n    bool ic_wcl_enterprise;\n    bool ic_wcl_join_requested;\n"
    "    bool ic_wcl_scan_requested;\n    bool ic_wcl_scan_active;\n    uint8_t ic_wcl_scan_ssid_length;\n"
    "    uint8_t ic_wcl_scan_ssid[32];\n    bool ic_wcl_scan_restricted;\n    uint8_t ic_wcl_scan_channels[32];\n"
    "    uint32_t ic_wcl_scan_away_time_ms;\n    uint64_t ic_wcl_tx_packets[4];\n    uint64_t ic_wcl_rx_packets[4];\n"
    "#endif\n", "ic_update_chw")
s = rd(N + "ieee80211_var.h")
if "IEEE80211_C_HE" not in s:
    anchor = "#define IEEE80211_C_QOS"
    assert anchor in s
    s = s.replace(anchor, "#define IEEE80211_C_HE 0x00200000 /* CAPABILITY: initialized HE support */\n" + anchor, 1)
if "ieee80211_wcl_ac" not in s:
    i = s.rindex("#endif")
    s = s[:i] + '''#ifdef AIRPORT_WCL
static inline unsigned ieee80211_wcl_ac(unsigned tid)
{
    static const unsigned categories[8] = {
        EDCA_AC_BE, EDCA_AC_BK, EDCA_AC_BK, EDCA_AC_BE,
        EDCA_AC_VI, EDCA_AC_VI, EDCA_AC_VO, EDCA_AC_VO
    };
    return tid < 8 ? categories[tid] : EDCA_AC_BE;
}
#define IEEE80211_EVT_BEACON 5
#define IEEE80211_EVT_DRIVER_READY 6
#define IEEE80211_EVT_DRIVER_STOPPED 7
#define IEEE80211_EVT_DRIVER_RESET_BEGIN 8
struct ieee80211_beacon_event {
    const struct ieee80211_node *node;
    const uint8_t *ies;
    size_t length;
    const uint8_t *frame;
    size_t frame_length;
};
#endif
''' + s[i:]
wr(N + "ieee80211_var.h", s)

# --- ieee80211_node.h : поля HE, которые читает слой интерфейса
rep("ieee80211_node.h", "    uint8_t         ni_he_optional[8];\n",
    "    uint8_t         ni_he_optional[8];\n    uint8_t         ni_he_mu_edca[13];\n    uint32_t        ni_he_txrate_kbps;\n"
    "    uint8_t         ni_he_tx_nss;\n    uint8_t         ni_he_requested;\n", "ni_he_optional")

# --- ieee80211_node.c : автоподключение только по запросу WCL
rep("ieee80211_node.c",
    "    u_int8_t rate;\n    int fail;\n    \n    fail = 0;\n",
    "    u_int8_t rate;\n    int fail;\n    \n#ifdef AIRPORT_WCL\n    if (!ic->ic_wcl_join_requested)\n        return IEEE80211_NODE_ASSOCFAIL_ESSID;\n#endif\n    fail = 0;\n",
    "match_bss")

# --- ieee80211_input.c
rep("ieee80211_input.c",
    "#if NBPFILTER > 0\n            /* copy to listener after decrypt */\n            if (ic->ic_rawbpf)\n                bpf_mtap(ic->ic_rawbpf, m, BPF_DIRECTION_IN);\n#endif\n            \n",
    "#if NBPFILTER > 0\n            /* copy to listener after decrypt */\n            if (ic->ic_rawbpf)\n                bpf_mtap(ic->ic_rawbpf, m, BPF_DIRECTION_IN);\n#endif\n            \n"
    "#ifdef AIRPORT_WCL\n            if (ic->ic_opmode == IEEE80211_M_STA)\n                ++ic->ic_wcl_rx_packets[hasqos ? ieee80211_wcl_ac(tid) : EDCA_AC_BE];\n#endif\n",
    "rx counters")
rep("ieee80211_input.c",
    "#ifdef USE_APPLE_SUPPLICANT\n            ml_enqueue(ml, m);\n#else\n#ifdef IO80211FAMILY_V2\n",
    "#if defined(AIRPORT_WCL)\n            if (ic->ic_wcl_enterprise) {\n                mbuf_t eapCopy = NULL;\n"
    "                if (mbuf_dup(m, MBUF_DONTWAIT, &eapCopy) == 0 && eapCopy)\n                    ml_enqueue(ml, eapCopy);\n            }\n"
    "            ieee80211_eapol_key_input(ic, m, ni);\n#elif defined(USE_APPLE_SUPPLICANT)\n            ml_enqueue(ml, m);\n#else\n#ifdef IO80211FAMILY_V2\n",
    "eapol")
rep("ieee80211_input.c",
    "    ieee80211_setup_rates(ic, ni, rates, xrates, IEEE80211_F_DOSORT);\n",
    "    ieee80211_setup_rates(ic, ni, rates, xrates, IEEE80211_F_DOSORT);\n"
    "#ifdef AIRPORT_WCL\n    if (ic->ic_event_handler) {\n        const uint8_t *ies = (const uint8_t *)&wh[1] + 12;\n"
    "        const uint8_t *end = mtod(m, const uint8_t *) + mbuf_len(m);\n        if (end >= ies) {\n"
    "            struct ieee80211_beacon_event event = {ni, ies, (size_t)(end - ies),\n"
    "                (const uint8_t *)wh, (size_t)(end - (const uint8_t *)wh)};\n"
    "            ic->ic_event_handler(ic, IEEE80211_EVT_BEACON, &event);\n        }\n    }\n#endif\n",
    "beacon event")
rep("ieee80211_input.c",
    "        uint32_t tlv_len = (mtod(m, u_int8_t *) + mbuf_len(m)) - (u_int8_t *)&wh[1] + 1 - 8 - 2 - 2;\n",
    "#ifdef AIRPORT_WCL\n        uint32_t tlv_len = (mtod(m, u_int8_t *) + mbuf_len(m)) - (u_int8_t *)&wh[1] - 8 - 2 - 2;\n#else\n"
    "        uint32_t tlv_len = (mtod(m, u_int8_t *) + mbuf_len(m)) - (u_int8_t *)&wh[1] + 1 - 8 - 2 - 2;\n#endif\n",
    "tlv_len")
rep("ieee80211_input.c",
    "    ic->ic_assoc_status = status;\n    if (status == IEEE80211_STATUS_SUCCESS) {\n",
    "    ic->ic_assoc_status = status;\n#ifndef AIRPORT_WCL\n    if (status == IEEE80211_STATUS_SUCCESS)\n#endif\n    { // WCL должен получать и неудачные ответы ассоциации\n",
    "assoc done")

# --- ieee80211_proto.c : линк вверх без RSN сразу
rep("ieee80211_proto.c",
    "#ifdef USE_APPLE_SUPPLICANT\n            {\n#elif (defined IO80211FAMILY_V2)\n",
    "#if defined(AIRPORT_WCL)\n            if (!(ic->ic_flags & IEEE80211_F_RSNON)) {\n#elif defined(USE_APPLE_SUPPLICANT)\n            {\n#elif (defined IO80211FAMILY_V2)\n",
    "link up")

# --- ieee80211.h : helper пересечения HE MCS (читает слой WCL)
s = rd(N + "ieee80211.h")
if "ieee80211_he_mcs_intersection" not in s:
    anchor = "static inline uint8_t\nieee80211_he_mcs_nss_size("
    assert anchor in s
    s = s.replace(anchor, """static inline uint16_t
ieee80211_he_mcs_intersection(uint16_t a, uint16_t b)
{
    uint16_t result = 0;
    for (unsigned i = 0; i < 8; i++) {
        unsigned x = (a >> (2 * i)) & 3, y = (b >> (2 * i)) & 3;
        result |= ((x == 3 || y == 3) ? 3 : (x < y ? x : y)) << (2 * i);
    }
    return result;
}

""" + anchor, 1)
    wr(N + "ieee80211.h", s)

# --- HAL: setScanHomeAwayTime (виртуальный, по умолчанию - не поддерживается)
H = root + "/include/HAL/MtkHalService.hpp"
h = open(H, encoding="utf-8").read()
if "setScanHomeAwayTime" not in h:
    a = "    virtual struct ieee80211com *get80211Controller() = 0;\n"
    assert a in h
    h = h.replace(a, a + "#ifdef AIRPORT_WCL\n    virtual IOReturn setScanHomeAwayTime(uint32_t) { return kIOReturnUnsupported; }\n#endif\n", 1)
    open(H, "w", encoding="utf-8").write(h)

# --- HAL MtkMwx: события драйвера для Family (как ItlIwm/mac80211.cpp): READY после init, STOPPED после stop
M = root + "/SimpleMtkWlan/hal_mwx/MtkMwx.cpp"
m = open(M, encoding="utf-8").read()
if "IEEE80211_EVT_DRIVER_READY" not in m:
    a = '\tMWX_DEV_LOG(sc, "init begin scan returned state=%d flags=0x%x sc_flags=0x%x\\n",\n\t    ic->ic_state, ifp->if_flags, sc->sc_flags);\n'
    assert a in m, "MtkMwx: нет конца mwx_init"
    m = m.replace(a, a + "#ifdef AIRPORT_WCL\n\tif (ic->ic_event_handler)\n\t\tic->ic_event_handler(ic, IEEE80211_EVT_DRIVER_READY, NULL);\n#endif\n", 1)
    i = m.index("\nmwx_stop(struct ifnet *ifp)\n{")
    j = m.index("{", i)
    depth = 0; k = j
    while True:
        c = m[k]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: break
        k += 1
    ins = "#ifdef AIRPORT_WCL\n\tif (ic->ic_event_handler)\n\t\tic->ic_event_handler(ic, IEEE80211_EVT_DRIVER_STOPPED, NULL);\n#endif\n"
    m = m[:k] + ins + m[k:]
    open(M, "w", encoding="utf-8").write(m)

# --- HAL MtkMwx: параметры скана из WCL (каналы, SSID, активный/пассивный)
m = open(M, encoding="utf-8").read()
if "scanChannelSelected" not in m:
    inc = '#include "mtk80211/compat.h"'
    # заголовок WCL: включаем в начало файла после первого #include
    first = m.index("#include")
    m = m[:first] + "#ifdef AIRPORT_WCL\n#include \"../../AirportMtkWlan/WCL/WCL.hpp\"\n#endif\n" + m[first:]
    a = "\treq->scan_type = /* sreq->n_ssids ? 1 : 0 */ 0;\n"
    a = "\treq->scan_type = /* sreq->n_ssids ? 1 : */ 0;\n\treq->probe_req_num = /* sreq->n_ssids ? 2 : */ 0;\n"
    assert a in m, "MtkMwx: scan_type"
    m = m.replace(a, a + """#ifdef AIRPORT_WCL
\t{
\t\tbool wcl_active = AirportWCL::scanUsesProbes(ic->ic_wcl_scan_requested, ic->ic_wcl_scan_active);
\t\tif (wcl_active && !bgscan) {
\t\t\treq->scan_type = 1;
\t\t\treq->probe_req_num = 2;
\t\t}
\t}
#endif
""", 1)
    b = "\treq->ssid_type = n_ssids ? 0x4 : 0x1;\n"
    assert b in m, "MtkMwx: ssid_type"
    m = m.replace(b, """#ifdef AIRPORT_WCL
\tif (ic->ic_wcl_scan_requested && ic->ic_wcl_scan_ssid_length > 0 &&
\t    ic->ic_wcl_scan_ssid_length <= 32) {
\t\treq->ssids[0].ssid_len = htole32(ic->ic_wcl_scan_ssid_length);
\t\tmemcpy(req->ssids[0].ssid, ic->ic_wcl_scan_ssid, ic->ic_wcl_scan_ssid_length);
\t\tn_ssids = 1;
\t}
#endif
""" + b, 1)
    c = "\t\tif (c->ic_flags == 0)\n\t\t\tcontinue;\n\n\t\tif (nchan < 32)\n"
    assert c in m, "MtkMwx: chan loop"
    m = m.replace(c, """\t\tif (c->ic_flags == 0)
\t\t\tcontinue;
#ifdef AIRPORT_WCL
\t\tif (!AirportWCL::scanChannelSelected(ic->ic_wcl_scan_channels,
\t\t    ic->ic_wcl_scan_requested && ic->ic_wcl_scan_restricted,
\t\t    ieee80211_chan2ieee(ic, c)))
\t\t\tcontinue;
#endif

\t\tif (nchan < 32)
""", 1)
    open(M, "w", encoding="utf-8").write(m)
print("wcl-патч net80211 применён")

# --- HAL MtkMwx: собственный адрес = ifnet lladdr (приватный MAC от Family), как у itlwm (mac80211.cpp)
m = open(M, encoding="utf-8").read()
if "AIRPORT_WCL own addr" not in m:
    a = '\tMWX_DEV_LOG(sc, "init start opmode=%d flags=0x%x ic_state=%d\\n",\n'
    assert a in m, "MtkMwx: нет начала mwx_init"
    m = m.replace(a, "#ifdef AIRPORT_WCL\n\t/* AIRPORT_WCL own addr */\n\tIEEE80211_ADDR_COPY(ic->ic_myaddr, ((struct arpcom *)ifp)->ac_enaddr);\n#endif\n" + a, 1)
    b = "\tmemcpy(dev_req.tlv.omac_addr, sc->sc_lladdr, ETHER_ADDR_LEN);\n"
    assert b in m
    m = m.replace(b, "#ifdef AIRPORT_WCL\n\tmemcpy(dev_req.tlv.omac_addr, sc->sc_ic.ic_myaddr, ETHER_ADDR_LEN);\n#else\n" + b + "#endif\n", 1)
    open(M, "w", encoding="utf-8").write(m)
