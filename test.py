

def add_etmy_channels():
    from gcm.data import channels as chn
    channels = [chn.add_channel("H1", "HPI-ETMY", "SENSCOR_Y_FIR_IN1_DQ"),
                chn.add_channel("H1", "HPI-ETMY", "BLND_L4C_Y_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST1_BLND_Y_L4C_CUR_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST1_BLND_Y_T240_CUR_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST2_BLND_Y_GS13_CUR_IN1_DQ"),
                chn.add_channel("H1", "SUS-ETMY", "M0_ISIWIT_L_DQ")]
    etmy = chn.add_group("H1-ETMY", channels)

def sync_scott():
    from gcm.data import channels as chn
    from gcm.io import triggers as tr
    
    group = chn.get_group(0)
    print group
    tr.default_source.sync(group)

def calculate_etmy_coinc():
    from gcm.data import channels as chn, coinc
    
    group = chn.get_group(0)
    coinc.calculate_coinc_group(group)
    
def analyze_coinc(group_num=0):
    from gcm.data import channels as chn, coinc as co
    import numpy as np
    windows = np.linspace(0, 1.0, 50)
    co.scan_windows(chn.get_group(group_num), windows, 5)

if __name__ == '__main__':
    import sys
    group_num = int(sys.argv[1])
    analyze_coinc(group_num)