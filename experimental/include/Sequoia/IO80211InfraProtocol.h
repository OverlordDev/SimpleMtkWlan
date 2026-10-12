//
//  IO80211InfraProtocol.h
//  itlwm
//
//  Created by qcwap on 2023/6/14.
//  Copyright © 2023 钟先耀. All rights reserved.
//

#ifndef IO80211InfraProtocol_h
#define IO80211InfraProtocol_h

#include <IOKit/IOService.h>
#include <Airport/apple80211_var.h>
#include <Airport/apple80211_ioctl.h>

struct apple80211_sta_ie_data;
struct apple80211_sta_stats_data;
struct apple80211_rssi_bounds_data;
struct apple80211_rate_set_data;
struct apple80211_power_debug_info;
struct apple80211_bgscan_cached_network_data_list;
struct apple80211_private_mac_data;
struct apple80211_dbg_guard_time_params;
struct apple80211_ranging_enable_request_t;
struct apple80211_gas_result_t;
struct apple80211_ranging_start_request_t;
struct apple80211_leaky_ap_setting;
struct apple80211_rsdb_capability;
struct apple80211_tko_params;
struct apple80211_tko_dump;
struct apple80211_thermal_index_t;
struct apple80211_btcoex_max_nss_for_ap_data;
struct apple80211_btcoex_2g_chain_disable;
struct apple80211_power_budget_t;
struct apple80211_ranging_capabilities_t;
struct apple80211_suppress_scans_t;
struct apple80211_host_ap_mode_hidden_t;
struct apple80211_lqm_config_t;
struct apple80211_trap_mini_dump_data;
struct apple80211_beacon_info_t;
struct apple80211_softap_params;
struct apple80211_chip_power_limit;
struct apple80211_softap_stats;
struct apple80211_nss_data;
struct apple80211_hw_mac_address;
struct apple80211_he_mcs_index_set_data;
struct appl80211_chip_diags_data;
struct apple80211_hp2p_ctrl;
struct apple80211_assoc_ready;
struct apple80211_txrx_chain_info;
struct apple80211_mimo_status;
struct apple80211_dynsar_detail;
struct apple80211_mac_randomisation_status;
struct apple80211_colocated_network_scope_id
{
    uint32_t version;
    uint32_t id1;
    uint32_t id2;
};
struct apple80211_slow_wifi_feature_enabled;
struct apple80211_interface_cca_data;
struct apple80211_timesync_info;
struct apple80211_sensing_data_t;
struct apple80211_country_band_support;
struct apple80211_fw_hot_channels;
struct apple80211_low_latency_info;
struct apple80211_beacon_msg;
struct apple80211_wcl_traffic_counters;
struct apple80211_ssid_transition_feature_enabled;
typedef enum {
    
} p2pStatusForScan;
struct apple80211ChannelInfo;
struct apple80211_p2p_steering_metrics;;
struct apple80211_rsn_xe_data;
struct apple80211_sib_coex_status;
struct apple80211_extended_bss_info;
struct apple80211_wcl_low_latency_stats;
struct apple80211_noise_per_ant_t;
struct apple80211_blocked_bands;
struct apple80211_disassoc_data;
struct apple80211_bgscan_data;
struct apple80211_sta_authorize_data;
struct apple80211_sta_disassoc_data;
struct apple80211_rsn_conf_data;
struct apple80211_country_channel_data;
struct apple80211_awdl_forced_roam_config;
struct apple80211_offload_arp_data;
struct apple80211_offload_ndp_data;
struct apple80211_offload_scan_data;
struct apple80211_gas_query_t;
struct apple80211_gas_peer_t;
struct apple80211_btcoex_profile;
struct apple80211_btcoex_profile_active_data;
struct apple80211_trap_info_data;
struct apple80211_he_capability;
struct apple80211_pmk;
struct apple80211_wow_test_data;
struct apple80211_reset_command;
struct apple80211_crash_command;
struct apple80211_ranging_authenticate_request_t;
struct apple80211_softap_csa_params;
struct apple80211_softap_wifi_network_info;
struct apple80211_scan_control_params;
struct apple80211_usb_host_notification_data;
struct apple80211_set_mac_address;
struct apple80211_abort_scan;
struct apple80211_set_property_unserialized_data;
struct apple80211_roam_cache_data;
struct apple80211_pm_mode;
struct apple80211_wifi_assertion_data;
struct apple80211_capture_debug_info_t;
struct apple80211_linkdown_debounce_status;
struct apple80211_softap_extended_capabilities_info;
struct apple80211_sensing_enable_t;
struct apple80211_sensing_disable_t;
struct apple80211_nan_link_association_info;
struct apple80211_6G_mode;
struct apple80211_leave_network;
struct apple80211_reassoc;
struct apple80211_set_roam_lock;
struct apple80211_roam_profile_config;
struct apple80211_roam_profile_configV1;
struct apple80211_user_roam_cache;
struct apple80211_set_multi_ap_env;
struct apple80211_wcl_real_time_mode;
struct apple80211_wcl_garp_mode;
struct triggerCC;
struct apple80211ScanRequest;
struct apple80211_assoc_candidates;
struct apple80211_wcl_protect_ip_mode;
struct scanHomeAndAwayTime;
struct apple80211_wcl_voluntary_network_disconnect;
struct apple80211_wcl_update_link_state;
struct apple80211_wcl_ulofdma_state;
struct apple80211_wcl_action_frame;
struct apple80211_wcl_real_time_policy;
struct apple80211_feature_flags;
struct apple80211_dhcp_renewal_data;
struct apple80211_network_flags;
struct apple80211_battery_ps_config;
struct apple80211_mimo_config;
struct apple80211_bg_motion_profile;
struct apple80211_bg_network;
struct apple80211_bg_scan;
struct apple80211_bg_params;
typedef UInt apple80211_offload_tcpka_enable_t;

class IO80211InfraProtocol : public IO80211InfraInterface {
    OSDeclareAbstractStructors(IO80211InfraProtocol)
public:
#include "gen/IO80211InfraProtocol.inc"
};
static_assert(sizeof(IO80211InfraProtocol) == 0x120, "IO80211InfraProtocol size");
#endif
