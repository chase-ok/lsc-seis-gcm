
from gcm.io import root
from gcm.coinc import find_coincidences

def test_coinc():
    print "Hello!"
    triggers1 = root.read_triggers("/home/scott.dossa/omicron/triggers/H1/1058400000_1058500000/H1:ISI-ETMY_ST1_BLND_Y_L4C_CUR_IN1_DQ/H1:ISI-ETMY_ST1_BLND_Y_L4C_CUR_IN1_DQ_1058400080_704.root")
    triggers2 = root.read_triggers("/home/scott.dossa/omicron/triggers/H1/1058400000_1058500000/H1:ISI-ETMY_ST1_BLND_Y_T240_CUR_IN1_DQ/H1:ISI-ETMY_ST1_BLND_Y_T240_CUR_IN1_DQ_1058400080_704.root")
    return triggers1, triggers2, find_coincidences(triggers1, triggers2)
