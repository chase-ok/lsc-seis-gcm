
from gcm.data import make_data_path, make_dtype, hdf5
from gcm.data import coinc as co, channels as chn
from gcm import utils
import numpy as np
import bisect
from os.path import join

RAW_DIR = "raw/"
def make_raw_h5_path(group):
    return make_data_path(join(RAW_DIR, "{0.name}.h5".format(group)))

IFO_TO_FRAMETYPE = {'H1': 'H1_R', 'L1': 'L1_R'}
CHANNEL_DATASET = "channel{0}"
SAMPLING_RATE = 64 # Hz
SAMPLE_DURATION = 10 # s
SAMPLE_BUFFER = 2 # s
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

@utils.memoized
def get_cache(frametype):
    from pylal import frutils
    return frutils.AutoqueryingFrameCache(frametype=frametype,
                                          scratchdir="/usr1/chase.kernan")

def get_raw_coinc(group, coinc):
    raw, bandpassed = [], []
    
    for channel_id in coinc.channel_ids:
        with open_raw(group, chn.get_channel(channel_id)) as table:
            # TODO: use bisect to make this faster
            index = np.nonzero(table.attrs['index'] == coinc.id)[0][0]
            raw.append(table[index].raw)
            bandpassed.append(table[index].bandpassed)
    
    return raw, bandpassed 

def fetch_raw_data(channel, start, end):
    from pylal import seriesutils
    from lal import LIGOTimeGPS

    cache = get_cache(IFO_TO_FRAMETYPE[channel.ifo])
    data = cache.fetch("{0.ifo}:{0.subsystem}_{0.name}".format(channel),
                       start, end)
    return seriesutils.fromarray(data, 
                                 epoch=LIGOTimeGPS(start),
                                 deltaT=data.metadata.dt)

def process_group(group):
    with co.open_coincs(group, mode='r') as table:
        for i, coinc in enumerate(table):
            print i, "of", len(table)
	    process_coinc(group, coinc)

def process_coinc(group, coinc):
    from pylal import seriesutils

    start = coinc.time_min - SAMPLE_BUFFER
    end = start + SAMPLE_DURATION

    for i, channel_id in enumerate(coinc.channel_ids[:coinc.length]):
        channel = chn.get_channel(channel_id)
        raw_data = fetch_raw_data(channel, start, end)
        seriesutils.resample(raw_data, SAMPLING_RATE)
        print i, start, end, raw_data.data.length
        
        freq_min, freq_max = map(np.float64, coinc.freq_bands[i])
        bandpassed = seriesutils.bandpass(raw_data, freq_min, freq_max, 
                                          inplace=False)
        
        _write_coinc(group, channel, coinc, raw_data, bandpassed)

def _coerce_to_sample_array(series):
    empty = np.empty(NUM_SAMPLES, dtype=np.float64)
    array = series.data.data
    length = min(NUM_SAMPLES, array.size)
    empty[:length] = array[:length]
    return empty

def _write_coinc(group, channel, coinc, raw_data, bandpassed):
    with open_raw(group, channel, mode='w') as table:
        index = table.attrs.get('index', np.array([], np.uint32))
        
        table.append_dict(raw=_coerce_to_sample_array(raw_data), 
                          bandpassed=_coerce_to_sample_array(bandpassed))
        table.attrs['index'] = np.concatenate((index, [coinc.id]))

if __name__ == '__main__':
    import sys
    from gcm.data import channels
    
    group_id = int(sys.argv[1])
    process_group(channels.get_group(group_id))
