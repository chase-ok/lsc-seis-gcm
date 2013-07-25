
from rootpy.io import root_open
from gcm import structs
import numpy as np

_ATTR_MAP = dict(time='time',
                 time_min='tstart', time_max='tend',
                 freq='frequency',
                 freq_min='fstart', freq_max='fend',
                 amplitude='amplitude',
                 snr='snr',
                 q='q')

def read_triggers(path):
    with root_open(path) as f:
        tree = f.triggers
        tree.create_buffer()
        buffer = tree._buffer
        
        triggers = np.empty(len(tree), dtype=structs.trigger)        
        for i, _ in enumerate(tree):
            # need to iterate the tree, hence the _ enumerate result
            for attr, mapped in _ATTR_MAP.iteritems():
                triggers[i][attr] = buffer[mapped].value
    
    return triggers