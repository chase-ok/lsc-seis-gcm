

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
    
def test_coinc():
    from gcm.data import channels as chn, coinc as co
    from random import random

    g0 = chn.get_group(0)
    offsets = dict((c, random()*100.0) for c in g0.channels)
    coincs = co.get_coincidences_with_offsets(g0, 0.05, offsets)
    return co.analyze_coincidences(g0, coincs)
