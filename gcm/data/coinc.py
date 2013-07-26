
from gcm.data import make_data_path, make_dtype, hdf5, triggers as tr
from gcm import utils
import numpy as np
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


def calculate_coinc_pairs(group, channel1, channel2, window=0.5):
    with hdf5.write_h5(make_coinc_h5_path(group)) as h5:
        coinc_table = get_coinc_table([channel1, channel2])
        coinc_table = coinc_table.attach(h5, reset=True)
        
        with hdf5.read_h5(tr.make_trigger_h5_path(channel1)) as h5c1:
            trigger_table1 = tr.trigger_table.attach(h5c1)
            
            with hdf5.read_h5(tr.make_trigger_h5_path(channel2)) as h5c2:
                trigger_table2 = tr.trigger_table.attach(h5c2)
                
                _calculate_coinc(coinc_table, trigger_table1, trigger_table2, 2,
                                 time_attr='time_min', window=window)

def append_coinc_chain(group, prev_channels, next_channel, window=0.5):
    with hdf5.write_h5(make_coinc_h5_path(group)) as h5:
        coinc_table = get_coinc_table(prev_channels + [next_channel])
        coinc_table = coinc_table.attach(h5, reset=True)
        prev_coinc_table = get_coinc_table(prev_channels).attach(h5)
        
        with hdf5.read_h5(tr.make_trigger_h5_path(next_channel)) as h5c:
            trigger_table = tr.trigger_table.attach(h5c)
            
            _calculate_coinc(coinc_table, prev_coinc_table, trigger_table,
                             len(prev_channels) + 1, window=window)

def calculate_coinc_group(group):
    # pairs
    for channel1, channel2 in zip(group.channels, group.channels[1:]):
        print channel1, channel2
        calculate_coinc_pairs(group, channel1, channel2)


def _calculate_coinc(output_table, base_table, trigger_table, chain_len,
                     time_attr='time', window=0.5):
    match_times = trigger_table.columns.time_min
    match_snrs = trigger_table.columns.snr
    match_freqs = trigger_table.columns.freq
    match_rows = np.arange(num_triggers)
    
    base_scale = (chain_len-1.0)/chain_len
    match_scale = 1.0/chain_len
    average = lambda match, base: base*base_scale + match*match_scale
    
    for row, base in enumerate(base_table.iterdict()):
        if row % 100 == 0: print row, len(base_table)
        dt = match_times - base[time_attr]
        in_window = np.abs(dt) < window
        
        block = np.empty(in_window.sum(), dtype=coinc_dtype)
        block['dt'] = dt[in_window]
        block['time'] = average(match_times[in_window], base[time_attr])
        block['snr'] = average(match_snrs[in_window], base['snr'])
        block['freq'] = average(match_freqs[in_window], base['freq'])
        block['trigger_id'] = match_rows[in_window]
        block['prev_coinc_id'] = row
        
        if len(output_table) > 0:
            output_table.append_array(block)
