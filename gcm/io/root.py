
from rootpy.io import root_open
from gcm import structs
import numpy as np

def read_triggers(path):
    with root_open(path) as f:
        tree = f.triggers
        tree.create_buffer(ignore_unsupported=True)
        
        triggers = np.empty(len(tree), dtype=structs.trigger)
        for trigger, raw in zip(triggers, tree):
            trigger['time'] = raw.time
            trigger['time_min'] = raw.tstart
            trigger['time_max'] = raw.tend
            trigger['freq'] = raw.frequency
            trigger['freq_min'] = raw.fstart
            trigger['freq_max'] = raw.fend
            trigger['amplitude'] = raw.amplitude
            trigger['snr'] = raw.snr
            trigger['q'] = raw.q
    
    return triggers