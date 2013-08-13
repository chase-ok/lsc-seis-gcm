
from gcm.data import make_data_path, make_dtype, hdf5
from gcm.data import coinc as co, channels as chn
from gcm import utils
import numpy as np
import bisect
from os.path import join
from random import randint

RAW_DIR = "raw/"
def make_raw_h5_path(group):
    return make_data_path(join(RAW_DIR, "{0.name}.h5".format(group)))

IFO_TO_FRAMETYPE = {'H1': 'H1_R', 'L1': 'R'}
CHANNEL_DATASET = "channel{0}"
SAMPLING_RATE = 64 # Hz
SAMPLE_DURATION = 20 # s
SAMPLE_BUFFER = 4 # s
NUM_SAMPLES = SAMPLING_RATE*SAMPLE_DURATION

raw_dtype = make_dtype(raw=(np.float64, (NUM_SAMPLES,)), 
                       bandpassed=(np.float64, (NUM_SAMPLES,))) 

def get_raw_table(channel):
    return hdf5.GenericTable(CHANNEL_DATASET.format(channel.id),
                             dtype=raw_dtype,
                             chunk_size=1,
                             initial_size=1024)

def open_raw(group, channel, **kwargs):
    return hdf5.open_table(make_raw_h5_path(group),
                           get_raw_table(channel), **kwargs)

#@utils.memoized
def get_cache(frametype):
    from pylal import frutils
    return frutils.AutoqueryingFrameCache(frametype=frametype,
                                          scratchdir="/usr1/chase.kernan")

def get_raw_coinc(group, coinc):
    raw, bandpassed = [], []
    
    for channel in group.channels: 
        with open_raw(group, channel) as table:
            raw.append(table[coinc.id].raw)
            bandpassed.append(table[coinc.id].bandpassed)
    
    return raw, bandpassed 

def fetch_raw_data(channel, start, end):
    from pylal import seriesutils
    from lal import LIGOTimeGPS

    cache = get_cache(IFO_TO_FRAMETYPE[channel.ifo])
    try:
        data = cache.fetch("{0.ifo}:{0.subsystem}_{0.name}".format(channel),
                           start, end)
        dt = data.metadata.dt
    except ValueError:
        print "WARNING: raw data missing for {0}-{1} on {2}"\
              .format(start, end, channel)
        data = np.zeros(NUM_SAMPLES, dtype=np.float64)
        dt = 1.0/SAMPLING_RATE

    return seriesutils.fromarray(data, 
                                 epoch=LIGOTimeGPS(start),
                                 deltaT=dt)

def process_group(group):
    with co.open_coincs(group, mode='r') as table:
        with open_raw(group, group.channels[0], mode='w') as raw:
            to_sync = len(raw)
        print to_sync, "already sync'd!"

        for i, coinc in enumerate(table[to_sync:]):
            print i, "of", len(table)
            process_coinc(group, coinc)

def process_coinc(group, coinc):
    from pylal import seriesutils

    start = coinc.time_min - SAMPLE_BUFFER
    end = start + SAMPLE_DURATION
    
    freq_bands = coinc.freq_bands[:coinc.length, :]
    coinc_freq_min = np.min(freq_bands[:, 0])
    coinc_freq_max = np.max(freq_bands[:, 1])

    for channel in group.channels:
        raw_data = fetch_raw_data(channel, start, end)
        seriesutils.resample(raw_data, SAMPLING_RATE)
        
        if channel.id in coinc.channel_ids:
            index = np.nonzero(coinc.channel_ids == channel.id)[0][0]
            freq_min, freq_max = freq_bands[index]
        else:
            freq_min, freq_max = coinc_freq_min, coinc_freq_max
        bandpassed = seriesutils.bandpass(raw_data, 
                                          np.float64(freq_min),
                                          np.float64(freq_max),
                                          inplace=False)
        
        _write_coinc(group, channel, raw_data, bandpassed)
        
def _coerce_to_sample_array(series):
    empty = np.empty(NUM_SAMPLES, dtype=np.float64)
    array = series.data.data
    length = min(NUM_SAMPLES, array.size)
    empty[:length] = array[:length]
    return empty

def _write_coinc(group, channel, raw_data, bandpassed):
    with open_raw(group, channel, mode='w') as table:
        table.append_dict(raw=_coerce_to_sample_array(raw_data), 
                          bandpassed=_coerce_to_sample_array(bandpassed))

if __name__ == '__main__':
    import sys
    from gcm.data import channels
    
    group_id = int(sys.argv[1])
    process_group(channels.get_group(group_id))
