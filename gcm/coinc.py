
from gcm import structs
import numpy as np


def find_coincidences(triggers1, triggers2, window=5.0, time_attr='time_min'):
    n1, n2 = len(triggers1), len(triggers2)
    
    match_times = triggers2[time_attr]
    match_snrs = triggers2['snr']
    match_freqs = triggers2['freq']
    match_rows = np.arange(n2)
    
    blocks = []
    for row, current in enumerate(triggers1):
        dt = match_times - current[time_attr]
        in_window = np.abs(dt) < window
        
        block = np.empty(in_window.sum(), dtype=structs.coincidence)
        block['dt'] = dt[in_window]
        block['mean_time'] = (match_times[in_window] + current[time_attr])/2
        block['mean_snr'] = (match_snrs[in_window] + current['snr'])/2
        block['mean_freq'] = (match_freqs[in_window] + current['freq'])/2
        block['trigger1'] = row
        block['trigger2'] = match_rows[in_window]
        blocks.append(block)
    
    return np.concatenate(blocks)
