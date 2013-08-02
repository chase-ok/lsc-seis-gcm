
from gcm.data import make_data_path, make_dtype, hdf5, triggers as tr
from gcm import utils
import numpy as np
from itertools import combinations, permutations
import bisect
from os.path import join
from math import ceil

COINC_DIR = "coincidences/"

def make_coinc_h5_path(group):
    return make_data_path(join(COINC_DIR, "{0.name}.h5".format(group)))

NULL = -1

def get_coinc_dtype(group):
    num_channels = len(group.channels)
    return make_dtype(times=(np.float64, (num_channels,)),
                      freqs=(np.float32, (num_channels,)),
                      snrs=(np.float32, (num_channels,)),
                      amplitudes=(np.float64, (num_channels,)),
                      channel_ids=(np.int32, (num_channels,)),
                      length=np.uint16,
                      id=np.uint32)

def get_coinc_table(group):
    return hdf5.GenericTable("coincidences",
                             dtype=get_coinc_dtype(group),
                             chunk_size=2**8,
                             initial_size=2**10)

def open_coincs(group, **kwargs):
    return hdf5.open_table(make_coinc_h5_path(group),
                           get_coinc_table(group),
                           **kwargs)

def coincs_to_list(group):
    coincs = []
    with open_coincs(group, mode='r') as coinc_table:
        for coinc in coinc_table.iterdict():
            length = coinc['length']
            coinc['times'] = coinc['times'][:length]
            coinc['freqs'] = coinc['freqs'][:length]
            coinc['snrs'] = coinc['snrs'][:length]
            coinc['channel_ids'] = coinc['channel_ids'][:length]
            coinc['amplitudes'] = coinc['amplitudes'][:length]
            coinc['id'] = coinc['id']
            coincs.append(coinc)
    return coincs


def find_coincidences(group, window=0.05):
    num_channels = len(group.channels)
    with open_coincs(group, mode='w', reset=True) as coincs:
        def to_array(values, dtype):
            array = NULL*np.ones(num_channels, dtype=dtype)
            array[:len(values)] = values
            return array

        def append(coinc): 
            coincs.append_dict(times=to_array(coinc['times'], np.float64),
                               freqs=to_array(coinc['freqs'], np.float32),
                               snrs=to_array(coinc['snrs'], np.float32),
                               amplitudes=to_array(coinc['amplitudes'], np.float64),
                               channel_ids=to_array(coinc['channel_ids'], np.int32),
                               length=coinc['length'],
                               id=coinc['id'])

        _find_coincidences(group, append, window)

def get_coincidences_with_offsets(group, window, time_offsets):
    coincs = []
    _find_coincidences(group, coincs.append, window, time_offsets)
    return coincs

def analyze_coincidences(group, coincs):
    from scipy.stats import pearsonr, spearmanr

    num_pairs = sum(c['length']-1 for c in coincs)
    dts = np.empty(num_pairs, np.float64)
    freqs = np.empty((num_pairs, 2), np.float32)
    snrs = np.empty((num_pairs, 2), np.float32)

    lengths = np.empty(len(coincs), dtype=np.uint8)
    channel_counts = dict((c.id, 0) for c in group.channels)

    pair_index = 0
    for coinc_index, coinc in enumerate(coincs):
        lengths[coinc_index] = coinc['length']

        for id in coinc['channel_ids']:
            channel_counts[id] += 1

        for t1 in range(coinc['length']-1):
            t2 = t1 + 1
            dts[pair_index] = coinc['times'][t2] - coinc['times'][t1]
            freqs[pair_index, :] = coinc['freqs'][t1], coinc['freqs'][t2]
            snrs[pair_index, :] = coinc['snrs'][t1], coinc['snrs'][t2]
            pair_index += 1

    def describe_dist(dist):
        return {'mean': dist.mean(),
                'median': np.median(dist),
                'std': dist.std(),
                'max': float(dist.max()),
                'min': float(dist.min())}

    def describe_diff_dist(pairs):
        return describe_dist(np.abs(pairs[:, 0] - pairs[:, 1]))

    def describe_correl(pairs):
        return {'pearsonr': pearsonr(pairs[:, 0], pairs[:, 1]),
                'spearmanr': spearmanr(pairs[:, 0], pairs[:, 1])}

    return {'n': len(coincs), 
            'lengths': describe_dist(lengths),
            'dts': describe_dist(dts),
            'channel_counts': channel_counts,
            'freqs': {'diffs': describe_diff_dist(freqs),
                      'correl': describe_correl(freqs)},
            'snrs': {'diffs': describe_diff_dist(snrs),
                     'correl': describe_correl(snrs)}}

def scan_windows(group, windows, num_rand=10, output_dir='data/coinc/'):
    import json
    from random import random

    data = []
    for window in windows:
        print group.name, window
        
        actual = get_coincidences_with_offsets(group, window, None)

        rand_coincs = []
        for _ in range(num_rand):
            offsets = dict((c, random()*1000) for c in group.channels)
            rand_coincs.append(get_coincidences_with_offsets(group, window, offsets))
        
        def analyze(coincs): return analyze_coincidences(group, coincs)
        data.append({'window': window, 
                     'actual': analyze(actual),
                     'rand': map(analyze, rand_coincs)})

    file_name = "windows-{0.id}.json".format(group)
    with open(join(output_dir, file_name), 'wb') as f:
        json.dump(data, f, default=str)


def _find_coincidences(group, append_func, window, time_offsets=None):
    channels = group.channels
    num_channels = len(channels)
    assert num_channels > 1

    channel_order = dict((channel, i) for i, channel in enumerate(channels))
    def compare_times(item1, item2, epsilon=1e-6):
        time_diff = item1[1] - item2[1]
        if abs(time_diff) < epsilon:
            return channel_order[item1[0]] - channel_order[item2[0]]
        else:
            return -1 if time_diff < 0 else 1

    triggers, contexts = _open_all_triggers(channels)
    try:
        # in case of no triggers...
        channels = [c for c in channels if len(triggers[c]) > 0]

        rows = dict((c, 0) for c in channels)
        ends = dict((c, len(triggers[c])) for c in channels)
        times = dict((c, triggers[c][0].time_min) for c in channels)

        if time_offsets:
            for channel, offset in time_offsets.iteritems():
                times[channel] += offset

        coinc_id = 0
        while times:
            times_sorted = sorted(times.iteritems(),
                                  cmp=compare_times)

            starting_channel, starting_time = times_sorted[0]
            linked_channels = [starting_channel]

            window_end = starting_time + window
            for match_channel, match_time in times_sorted[1:]:
                if match_time < window_end:
                    linked_channels.append(match_channel)
                    window_end = match_time + window
                else:
                    break

            if len(linked_channels) > 1:
                linked_triggers = [triggers[c][rows[c]] for c in linked_channels]
                append_func(dict(times=[times[c] for c in linked_channels],
                                 freqs=[t.freq for t in linked_triggers],
                                 snrs=[t.snr for t in linked_triggers],
                                 amplitudes=[t.amplitude for t in linked_triggers],
                                 channel_ids=[c.id for c in linked_channels],
                                 length=len(linked_channels),
                                 id=coinc_id))
                coinc_id += 1

            for channel in linked_channels:
                row = rows[channel] + 1
                rows[channel] = row
                if row < ends[channel]:
                    times[channel] = triggers[channel][row].time_min
                    if time_offsets and channel in time_offsets:
                        times[channel] += time_offsets[channel]
                else:
                    del times[channel]

    finally:
            _close_all_triggers(contexts)

# TODO: this is a poor context management implementation
# maybe use contextlib instead?

def _open_all_triggers(channels):
    triggers = {}
    contexts = []
    for channel in channels:
        context = tr.open_clusters(channel, mode='r')
        triggers[channel] = context.__enter__()
        contexts.append(context)
    return triggers, contexts

def _close_all_triggers(contexts):
    for context in contexts:
        context.__exit__(None, None, None)
