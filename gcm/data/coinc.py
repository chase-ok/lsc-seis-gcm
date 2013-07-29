
from gcm.data import make_data_path, make_dtype, hdf5, triggers as tr
from gcm import utils
import numpy as np
from itertools import combinations, permutations
from os.path import join

COINC_DIR = "coincidences/"

def make_coinc_h5_path(group):
    return make_data_path(join(COINC_DIR, "{0.name}.h5".format(group)))


coinc_dtype = make_dtype(dt=np.float32,
                         time=np.float32,
                         freq=np.float32,
                         snr=np.float32,
                         trigger1_id=np.int32,
                         trigger2_id=np.int32,
                         chain_id=np.int32)

def get_chain_dtype(group):
    return make_dtype(dt=np.float32,
                      time=np.float32,
                      freq=np.float32,
                      snr=np.float32,
                      num_coinc=np.uint16,
                      channel_ids=(len(group.channels), np.int32))

def get_coinc_table(channels):
    name = "coincidences" + "_".join(str(c.id) for c in channels)
    return hdf5.GenericTable(name,
                             dtype=coinc_dtype,
                             chunk_size=2**10,
                             initial_size=2**14)

def open_coinc(group, channels, **kwargs):
    return hdf5.open_table(make_coinc_h5_path(group), 
                           get_coinc_table(channels),
                           **kwargs)

def get_chain_table(group):
    name = "coincidence_chains" + "_".join(str(c.id) for c in group.channels)
    return hdf5.GenericTable(name,
                             dtype=get_chain_dtype(group),
                             chunk_size=2**8,
                             initial_size=2**12)

def open_chains(group, **kwargs):
    return hdf5.open_table(make_coinc_h5_path(group), get_chain_table(group),
                           **kwargs)

DEFAULT_WINDOW = 0.1

def calculate_coinc_pairs(group, channel1, channel2, window):
    pair = [channel1, channel2]
    with open_coinc(group, pair, mode='w', reset=True) as coinc_table:
        with tr.open_clusters(channel1, mode='r') as trigger_table1:
            with tr.open_clusters(channel2, mode='r') as trigger_table2:
                _calculate_coinc(coinc_table, trigger_table1, trigger_table2,
                                 window)

def calculate_coinc_group(group, window=DEFAULT_WINDOW):
    assert len(group.channels) >= 2
    
    # pairs for base
    for channel1, channel2 in permutations(group.channels, 2):
        print channel1, channel2
        calculate_coinc_pairs(group, channel1, channel2, window)
    
    for chain_len in range(3, len(group.channels)):
        for channels in combinations(group.channels, chain_len):
            print channels
            append_coinc_chain(group, list(channels[:-1]), channels[-1], window)


def _calculate_coinc(output_table, trigger_table1, trigger_table2, window):
    average = lambda match, base: base*0.5 + match*0.5
    
    trigger_times = trigger_table2.columns.time_min
    
    trigger_start = 0
    trigger_end = 0
    for row, base in enumerate(trigger_table1.iterdict()):
        if row % 10000 == 0: print row, len(trigger_table1)
        
        start_time = base['time_min']
        end_time = base['time_min'] + window
        
        for trigger_start in xrange(trigger_start, len(trigger_table2)):
            if trigger_times[trigger_start] >= start_time:
                break
        
        for trigger_end in xrange(trigger_end, len(trigger_table2)):
            if trigger_times[trigger_end] > end_time:
                break    
        
        if trigger_start == trigger_end: continue
        
        matches = trigger_table.dataset[trigger_start:trigger_end]
        block = np.empty(matches.size, dtype=coinc_dtype)
        block['dt'] = matches['time_min'] - base['time_min']
        block['time'] = average(matches['time_min'], base['time_min'])
        block['snr'] = average(matches['snr'], base['snr'])
        block['freq'] = average(matches['freq'], base['freq'])
        block['trigger1_id'] = row
        block['trigger2_id'] = np.arange(trigger_start, trigger_end)
        block['chain_id'] = -1
        output_table.append_array(block)

def _find_chains(group, window=DEFAULT_WINDOW):
    channels = set(group.channels)
    
    # open the pair tables
    tables = {}
    contexts = []
    try:
        for pair in permutations(channels, 2):
            context = open_coinc(group, pair, mode='w')
            tables[pair] = context.__enter__()
            contexts.append(context)
        
        chain_id = 0
        
        for channel in channels:
            chains = []
            
            for next_channel in group:
                if channel is next_channel: continue
                coincs = tables[channel, next_channel]
                
                row = 0
                while row < len(coincs):
                    coinc = coincs[row]
                    if coinc.chain_id != -1:
                        row += 1
                        continue
                    
                    # otherwise, we're starting a chain
                    end_time = coinc.time + window
                    for end in range(row+1, len(coincs)):
                        if coincs[end].time > end_time:
                            break
                    
                    base_coincs = coincs.dataset[row:end]
                    coincs.columns.chain_id[row:end] = chain_id
                    
                    chain = {'dt': np.mean(base_coincs['dt']),
                             'time': base_coincs[0]['time'],
                             'freq': np.mean(base_coincs['freq']),
                             'snr': np.max(base_coincs['snr']),
                             'num_coinc': base_coincs.size,
                             'id': chain_id}
                    chains.append(chain)
                    chain_id += 1
            
            # start looking for chains of length 3, 4, 5...
            
            for chain in chains:
                chain_table.append(chain)
            
            
            
            
            
        for pair in permutations(group.channels, 2):
            for coinc in tables[pair]:
                if coinc.chain_id is not -1: continue
                
                
        
    finally:
        for context in contexts:
            context.__exit__()

def _find_links(channel, id, coinc, tables_to_check):
    dt = starting_coinc['dt']
    time = starting_coinc['time']
    freq = starting_coinc['freq']
    snr = starting_coinc['snr']
    num_triggers = 1
    channel_ids = set([channel.id])
    
    for table in tables_to_check:
        
    
    
    
