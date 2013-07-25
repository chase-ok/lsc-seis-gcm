
from gcm.io import root
from gcm.coinc import find_coincidences

def test_coinc():
    base = "/home/scott.dossa/omicron/triggers/H1/1058400000_1058500000"
    triggers1 = root.read_triggers(base + "H1:ISI-ETMY_ST1_BLND_Y_T240_CUR_IN1_DQ")
    triggers2 = root.read_triggers(base + "H1:ISI-ETMY_ST2_BLND_Y_GS13_CUR_IN1_DQ")
    return triggers1, triggers2, find_coincidences(triggers1, triggers2)