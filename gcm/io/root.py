
from rootpy.io import root_open
from gcm import structs
import numpy as np

def read_triggers(path):
    with root_open(path) as f:
        triggers = np.empty(len(f.triggers), dtype=structs.trigger)
        for row, raw in enumerate(f.triggers):
            triggers[row]['time'] = raw.time
            triggers[row]['time_min'] = raw.tstart
            triggers[row]['time_max'] = raw.tend
            triggers[row]['freq'] = raw.frequency
            triggers[row]['freq_min'] = raw.fstart
            triggers[row]['freq_max'] = raw.fend
            triggers[row]['amplitude'] = raw.amplitude
            triggers[row]['snr'] = raw.snr
            triggers[row]['q'] = raw.q
    
    return triggers