
from gcm.data import make_data_path, make_dtype, hdf5, triggers as tr
from gcm import utils
import numpy as np
from itertools import combinations, permutations
import bisect
from os.path import join

COINC_DIR = "coincidences/"

def make_coinc_h5_path(group):
    return make_data_path(join(COINC_DIR, "{0.name}.h5".format(group)))

NULL = -1

def get_coinc_dtype(group):
    num_channels = len(group.channels)
    return make_dtype(times=(num_channels, np.float32),
                      freqs=(num_channels, np.float32),
                      snrs=(num_channels, np.float32),
                      channel_ids=(num_channels, np.int32)
                      length=np.uint16)

def get_coinc_table(group):
    return hdf5.GenericTable("coincidences",
                             dtype=get_coinc_dtype(group),
                             chunk_size=2**8,
                             initial_size=2**10)

def open_coincs(group, **kwargs):
    return hdf5.open_table(make_coinc_h5_path(group), 
                           get_coinc_table(group),
                           **kwargs)


def find_coincidences(group, window=0.1):
    channels = group.channels
    num_channels = len(channels)
    assert num_channels > 1

    with open_coincs(group, mode='w') as coincs:
        triggers, contexts = _open_all_triggers(channels)
        try:

            rows = dict((c, 0) for c in channels)
            ends = dict((c, len(triggers[c])) for c in channels)
            times = dict((c, triggers[0].time_min) for c in channels)

            while times:
                times_sorted = sorted(times.iteritems(), 
                                      key=lambda item: item[1])

                if rows[channels[0]] % 100 == 0:
                    print rows, times, len(coincs)

                starting_channel, starting_time = times_sorted[0]
                linked_channels = [starting_channel]

                window_end = starting_time + window
                for match_channel, match_time in times_sorted[1:]:
                    if match_time < window_end:
                        linked_channels.append(match_channel)
                        window_end = match_time + window
                    else:
                        break

                if len(linked_channels) > 1
                    times = NULL*np.ones(num_channels, np.float32)
                    freqs = NULL*np.ones(num_channels, np.float32)
                    snrs = NULL*np.ones(num_channels, np.float32)
                    channel_ids = NULL*np.ones(num_channels, np.int32)
                    for i, channel in enumerate(linked_channels):
                        trigger = triggers[channel][rows[channel]]
                        times[i] = trigger.time_min
                        freqs[i] = trigger.freq
                        snrs[i] = trigger.snr
                        channel_ids[i] = channel.id

                    coincs.append_dict(times=times,
                                       freqs=freqs,
                                       snrs=snrs,
                                       channel_ids=channel_ids,
                                       length=len(linked_channels))

                for channel in linked_channels:
                    rows[channel] += 1
                    if rows[channel] < ends[channel]:
                        times[channel] = triggers[rows[channel]].time_min
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
        tables[channel] = context.__enter__()
        contexts.append(context)
    return triggers, contexts

def _close_all_triggers(contexts):
    for context in contexts:
        context.__exit__(None, None, None)
