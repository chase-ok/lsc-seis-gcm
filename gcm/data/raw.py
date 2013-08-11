
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

SEGLEN = 256 # should match sampling rate?

def process_coinc(group, coinc, time_buffer=2):
    from pylal import seriesutils

    start = coinc.time_min - time_buffer
    end = coinc.time_max + time_buffer

    for i, channel_id in enumerate(coinc.channel_ids[:coinc.length]):
        channel = chn.get_channel(channel_id)
        raw_data = fetch_raw_data(channel, start, end)

        freq_min, freq_max = coinc.freq_bands[i]
        bandpassed = seriesutils.bandpass(raw_data, freq_min, freq_max, 
                                          inplace=False)

        stride = SEGLEN/4
        spectrum = seriesutils.compute_average_spectrum(raw_data, 
                                                        SEGLEN, 
                                                        stride)

        step = SEGLEN/4
        spectrogram = seriesutils.compute_average_spectrogram(raw_data,
                                                              step,
                                                              SEGLEN,
                                                              stride)

        _write_coinc(group, channel, coinc, raw_data, bandpassed, spectrum, 
                     spectrogram)

def _write_coinc(group, channel, coinc, raw_data, bandpassed, spectrum, 
                 spectrogram):
    return raw_data, spectrum, spectrogram

    with hdf5.write_h5(make_raw_h5_path(group)) as h5:
        h5_group = h5.require_group("channel{0.id}".format(channel))

        dtype = make_dtype(raw=(raw_data.dtype, (len(raw_data),)),
                           bandpassed=(bandpassed.dtype, (len(bandpassed),)),
                           spectrum=(spectrum.dtype, (len(spectrum),)),
                           spectrogram=(spectrogram[0].dtype, spectrogram[0].shape))


def add_raw_data(group, channel, coinc, start_time, frame_data):
    with hdf5.write_h5(make_raw_h5_path(group)) as h5:
        channel_group = h5.require_group(str(channel.id))
        table = channel_group.require_dataset(name=str(coinc.id),
                                              data=frame_data)
        table.attrs.start_time = start_time
        table.attrs.sample_rate = int(1.0/frame_data.metadata.dt)

        group.require_dataset(name=self.name,
                                            shape=(self.initial_size,),
                                            dtype=self.dtype,
                                            chunks=(self.chunk_size,),
                                            maxshape=(None,),
                                            compression=self.compression,
                                            fletcher32=True,
                                            exact=False)
