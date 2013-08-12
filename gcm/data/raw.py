
from gcm.data import make_data_path, make_dtype, hdf5
from gcm.data import coinc as co, channels as chn
from gcm import utils
import numpy as np
import bisect
from os.path import join

RAW_DIR = "raw/"
def make_raw_h5_path(group):
    return make_data_path(join(RAW_DIR, "{0.name}.h5".format(group)))

@utils.memoized
def get_cache(frametype):
    from pylal import frutils
    return frutils.AutoqueryingFrameCache(frametype=frametype,
                                          scratchdir="/usr1/chase.kernan")

IFO_TO_FRAMETYPE = {'H1': 'H1_R', 'L1': 'L1_R'}

def fetch_raw_data(channel, start, end):
    from pylal import seriesutils
    from lal import LIGOTimeGPS

    cache = get_cache(IFO_TO_FRAMETYPE[channel.ifo])
    data = cache.fetch("{0.ifo}:{0.subsystem}_{0.name}".format(channel),
                       start, end)
    return seriesutils.fromarray(data, 
                                 epoch=LIGOTimeGPS(start),
                                 deltaT=data.metadata.dt)

SEGLEN = np.int64(256) # should match sampling rate?

def process_group(group, time_buffer=2, max_duration=10):
    with co.open_coincs(group, mode='r') as table:
        for i, coinc in enumerate(table):
            print i, "of", len(table)
	    process_coinc(group, coinc, time_buffer, max_duration)

def process_coinc(group, coinc, time_buffer, max_duration):
    from pylal import seriesutils

    start = coinc.time_min - time_buffer
    end = min(start + max_duration, coinc.time_max + time_buffer)

    for i, channel_id in enumerate(coinc.channel_ids[:coinc.length]):
        channel = chn.get_channel(channel_id)
        raw_data = fetch_raw_data(channel, start, end)
        print i, start, end, raw_data.data.length
        
	freq_min, freq_max = map(np.float64, coinc.freq_bands[i])
        bandpassed = seriesutils.bandpass(raw_data, freq_min, freq_max, 
                                          inplace=False)
	
	_write_coinc(group, channel, coinc, raw_data, bandpassed)
        # stride = SEGLEN/4
        # spectrum = seriesutils.compute_average_spectrum(raw_data, 
        #                                                 SEGLEN, 
        #                                                 stride)

        # step = SEGLEN/4
        # spectrogram = seriesutils.compute_average_spectrogram(raw_data,
        #                                                       step,
        #                                                       SEGLEN,
        #                                                       stride)

        # _write_coinc(group, channel, coinc, raw_data, bandpassed, spectrum, 
        #              spectrogram)

def _write_coinc(group, channel, coinc, raw_data, bandpassed):
    with hdf5.write_h5(make_raw_h5_path(group)) as h5:
        h5_group = h5.require_group("channel{0.id}".format(channel))

        dtype = make_dtype(raw=(np.float64, (raw_data.data.length,)),
                           bandpassed=(np.float64, (bandpassed.data.length,)))
        data = np.empty(1, dtype=dtype)
        data[0]['raw'] = raw_data.data.data
        data[0]['bandpassed'] = bandpassed.data.data
        
	dataset = h5_group.create_dataset(name="coinc{0.id}".format(coinc),
                                          data=data, chunks=(1,), 
                                          compression='gzip', compression_opts=9,
                                          shuffle=True)
        dataset.attrs.start_time = raw_data.epoch
        dataset.attrs.dt = raw_data.deltaT

if __name__ == '__main__':
    import sys
    from gcm.data import channels
    
    group_id = int(sys.argv[1])
    process_group(channels.get_group(group_id))
