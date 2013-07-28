
from gcm.data import make_data_path, make_dtype, hdf5
from gcm import utils
import numpy as np
from os.path import join

TRIGGER_DIR = "triggers/"

def make_trigger_h5_path(channel):
    name = "{0.ifo}-{0.subsystem}-{0.name}.h5".format(channel)
    return make_data_path(join(TRIGGER_DIR, name))


trigger_dtype = make_dtype(time=np.float32,
                           time_min=np.float64,
                           time_max=np.float64,
                           freq=np.float32,
                           freq_min=np.float64,
                           freq_max=np.float64,
                           snr=np.float32,
                           amplitude=np.float64,
                           q=np.float32)
                           
trigger_table = hdf5.GenericTable("triggers",
                                  dtype=trigger_dtype,
                                  chunk_size=2**10,
                                  initial_size=2**14)

def open_triggers(channel, mode='r'):
    return hdf5.open_table(make_trigger_h5_path(channel), trigger_table,
                           mode=mode)


def append_triggers(channel, triggers, snr_threshold=5):
    assert triggers.dtype == trigger_dtype
    
    with open_triggers(channel, mode='w') as table:
        if snr_threshold > 0:
            triggers = triggers[triggers['snr'] >= snr_threshold]
        if len(triggers) > 0:
            table.append_array(triggers)


def time_to_trigger_index(table, time, low=0, high=None):
    if low < 0: raise ValueError('low must be non-negative')
    if high is None: high = len(table)
    while low < high:
        mid = (low + high)//2
        if table[mid].time_min < time: low = mid + 1
        else: high = mid
    return low
    


