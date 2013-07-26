
from gcm.io import root
from gcm.coinc import find_coincidences

def add_etmy_channels():
    from gcm.data import channels as chn
    channels = [chn.add_channel("H1", "HPI-ETMY", "BLND_L4C_Y_IN1_DQ"),
                chn.add_channel("H1", "HPI-ETMY", "SENSCOR_Y_FIR_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST1_BLND_Y_L4C_CUR_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST1_BLND_Y_T240_CUR_IN1_DQ"),
                chn.add_channel("H1", "ISI-ETMY", "ST2_BLND_Y_GS13_CUR_IN1_DQ"),
                chn.add_channel("H1", "SUS-ETMY", "M0_ISIWIT_L_DQ")]
    etmy = chn.add_group("H1-ETMY", channels)

def sync_scott():
    from gcm.data import triggers, channels as chn
    
    group = chn.get_group(0)
    print group
    triggers.scott_triggers.sync(group)

def test_coinc():
    print "Hello!"
    triggers1 = root.read_triggers("/home/scott.dossa/omicron/triggers/H1/1058400000_1058500000/H1:ISI-ETMY_ST1_BLND_Y_L4C_CUR_IN1_DQ/H1:ISI-ETMY_ST1_BLND_Y_L4C_CUR_IN1_DQ_1058400080_704.root")
    triggers2 = root.read_triggers("/home/scott.dossa/omicron/triggers/H1/1058400000_1058500000/H1:ISI-ETMY_ST1_BLND_Y_T240_CUR_IN1_DQ/H1:ISI-ETMY_ST1_BLND_Y_T240_CUR_IN1_DQ_1058400080_704.root")
    return triggers1, triggers2, find_coincidences(triggers1, triggers2)
