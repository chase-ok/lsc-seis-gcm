
from rootpy.io import root_open
from gcm import structs
import numpy as np

def read_triggers(path):
    with root_open(path) as f:
        tree = f.triggers
        tree.create_buffer()
        buffer = tree._buffer
        
        triggers = np.empty(len(tree), dtype=structs.trigger)
        for trigger, _ in zip(triggers, tree):
            # need to also iterate the tree, hence the zip
            print buffer['time']
            
            trigger['time'] = buffer['time']
            trigger['time_min'] = buffer['tstart']
            trigger['time_max'] = buffer['tend']
            trigger['freq'] = buffer['frequency']
            trigger['freq_min'] = buffer['fstart']
            trigger['freq_max'] = buffer['fend']
            trigger['amplitude'] = buffer['amplitude']
            trigger['snr'] = buffer['snr']
            trigger['q'] = buffer['q']
    
    return triggers