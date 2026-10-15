#ifndef AirportMtkWlanSkywalkInterface_hpp
#define AirportMtkWlanSkywalkInterface_hpp

/* ni_rssi is dBm + 100 in this driver (mwx_dbm_to_rssi), the same normalisation as iwm/iwx */
#ifndef IWM_MIN_DBM
#define IWM_MIN_DBM (-100)
#endif

#include <Airport/Apple80211.h>

class AirportMtkWlan;

/* Класс интерфейса для Sequoia 15.8.1: наследник IO80211InfraProtocol (слоты и сигнатуры из ядра, см. sequoia_abi/) */
class AirportMtkWlanSkywalkInterface : public IO80211InfraProtocol {
    OSDeclareDefaultStructors(AirportMtkWlanSkywalkInterface)

public:
    bool initWithController(IOService *provider);

    void associateSSID(uint8_t *ssid, uint32_t ssid_len, const struct ether_addr &bssid, uint32_t authtype_lower, uint32_t authtype_upper, uint8_t *key, uint32_t key_len, int key_index);
    void setPTK(const u_int8_t *key, size_t key_len);
    void setGTK(const u_int8_t *key, size_t key_len, u_int8_t kid, u_int8_t *rsc);

    /* бывшие виртуальные методы Sonoma 14.4, в Sequoia их обрабатывает само Family; логика остаётся как вспомогательная */
    IOReturn getSSID(apple80211_ssid_data *);
    IOReturn getAUTH_TYPE(apple80211_authtype_data *);
    IOReturn getBSSID(apple80211_bssid_data *);
    IOReturn getSCAN_RESULT(apple80211_scan_result *);
    IOReturn getSTATE(apple80211_state_data *);
    IOReturn getPHY_MODE(apple80211_phymode_data *);
    IOReturn getNOISE(apple80211_noise_data *);
    IOReturn getLOCALE(apple80211_locale_data *);
    IOReturn getDEAUTH(apple80211_deauth_data *);
    IOReturn getRATE_SET(apple80211_rate_set_data *);
    IOReturn getRSN_IE(apple80211_rsn_ie_data *);
    IOReturn getAP_IE_LIST(apple80211_ap_ie_data *);
    IOReturn getASSOCIATION_STATUS(apple80211_assoc_status_data *);
    IOReturn getMCS_INDEX_SET(apple80211_mcs_index_set_data *);
    IOReturn getCURRENT_NETWORK(apple80211_scan_result *);
    IOReturn getLINK_CHANGED_EVENT_DATA(apple80211_link_changed_event_data *);
    IOReturn getVHT_MCS_INDEX_SET(apple80211_vht_mcs_index_set_data *);
    IOReturn getCOLOCATED_NETWORK_SCOPE_ID(apple80211_colocated_network_scope_id *);
    IOReturn setAUTH_TYPE(apple80211_authtype_data *);
    IOReturn setSCAN_REQ(apple80211_scan_data *);
    IOReturn setASSOCIATE(apple80211_assoc_data *);
    IOReturn setDISASSOCIATE(apple80211_disassoc_data *);
    IOReturn setDEAUTH(apple80211_deauth_data *);
    IOReturn setRSN_IE(apple80211_rsn_ie_data *);
    IOReturn setSCANCACHE_CLEAR(void *);

    /* слоты Sequoia: объявлены сгенерированным gen/pure_decl_infra.inc, реализованные - в .cpp, остальные - заглушки с логом */
#define MTK_DECL_PURE_STUBS 1
#include "gen/pure_decl_infra.inc"

private:
    AirportMtkWlan *instance;
    MtkHalService *fHalService;
    
    //IO80211
    struct ieee80211_node *fNextNodeToSend;
    IOTimerEventSource *scanSource;
    bool fScanResultWrapping;
    
    u_int32_t current_authtype_lower;
    u_int32_t current_authtype_upper;
    bool disassocIsVoluntary;
};

#endif
