
from gcm.io import root
from gcm.coinc import find_coincidences

def test_coinc():
    path = "/home/chase.kernan/H1:HPI-HAM3_SENSCOR_X_FIR_IN1_DQ_1055900080_704.root"
    triggers = root.read_triggers(path)
    return find_coincidences(triggers, triggers)