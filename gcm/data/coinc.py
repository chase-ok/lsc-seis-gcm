
from gcm.data import make_data_path, make_dtype, hdf5, triggers as tr
from gcm import utils
import numpy as np
from itertools import combinations
from os.path import join

COINC_DIR = "coincidences/"

def make_coinc_h5_path(group):
    return make_data_path(join(COINC_DIR, "{0.name}.h5".format(group)))


coinc_dtype = make_dtype(dt=np.float32,
                         time=np.float32,
                         freq=np.float32,
                         snr=np.float32,
                         trigger_id=np.int32,
                         prev_coinc_id=np.int32)

def get_coinc_table(channels):
    name = "coincidences" + "_".join(str(c.id) for c in channels)
    return hdf5.GenericTable(name,
                             dtype=coinc_dtype,
                             chunk_size=2**10,
                             initial_size=2**14)

def open_coinc(channels, **kwargs):
    return hdf5.open_table(make_coinc_h5_path(channel), 
                           get_coinc_table(channels),
                           **kwargs)

DEFAULT_WINDOW = 0.25

def calculate_coinc_pairs(group, channel1, channel2, window):
    with open_coinc([channel1, channel2], mode='w', reset=True) as coinc_table:
        with tr.open_triggers(channel1, mode='r') as trigger_table1:
            with tr.open_triggers(channel2, mode='r') as trigger_table2:
                _calculate_coinc(coinc_table, trigger_table1, trigger_table2, 2,
                                 window, time_attr='time_min')

def append_coinc_chain(group, prev_channels, next_channel, window):
    channels = prev_channels + [next_channel]
    with open_coinc(channels, mode='w', reset=True) as coinc_table:
        with open_coinc(prev_channels, mode='r') as prev_coinc_table:
            with tr.open_triggers(next_channel, mode='r') as trigger_table:
                _calculate_coinc(coinc_table, prev_coinc_table, trigger_table,
                                 window, len(channels))

def calculate_coinc_group(group, window=DEFAULT_WINDOW):
    assert len(group.channels) >= 2
    
    # pairs for base
    for channel1, channel2 in combinations(group.channels, 2):
        print channel1, channel2
        calculate_coinc_pairs(group, channel1, channel2, window)
    
    for chain_len in range(3, len(group.channels)):
        for channels in combinations(group.channels, chain_len):
            print channels
            append_coinc_chain(group, list(channels[:-1]), channels[-1], window)


def _calculate_coinc(output_table, base_table, trigger_table, chain_len, window,
                     time_attr='time'):
    base_scale = (chain_len-1.0)/chain_len
    match_scale = 1.0/chain_len
    average = lambda match, base: base*base_scale + match*match_scale
    
    trigger_times = trigger_table.columns.time_min
    
    trigger_start = 0
    trigger_end = 0
    for row, base in enumerate(base_table.iterdict()):
        if row % 10000 == 0: print row, len(base_table)
        
        start_time = base[time_attr] - window
        end_time = base[time_attr] + window
        
        for trigger_start in xrange(trigger_start, len(trigger_table)):
            if trigger_times[trigger_start] >= start_time:
                break
        
        for trigger_end in xrange(trigger_end, len(trigger_table)):
            if trigger_times[trigger_end] > end_time:
                break    
        
        if trigger_start == trigger_end: continue
        
        matches = trigger_table.dataset[trigger_start:trigger_end+1]
        block = np.empty(matches.size, dtype=coinc_dtype)
        block['dt'] = matches['time_min'] - base[time_attr]
        block['time'] = average(matches['time_min'], base[time_attr])
        block['snr'] = average(matches['snr'], base['snr'])
        block['freq'] = average(matches['freq'], base['freq'])
        block['trigger_id'] = np.arange(trigger_start, trigger_end + 1)
        block['prev_coinc_id'] = row
        output_table.append_array(block)
