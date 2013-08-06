#Plots FFT of raw bandpassed frame data and a spectagram of data round a specific event.

from pylal import frutils, Fr, seriesutils
from gcm.data import make_data_path, make_dtype, hdf5
from gcm import utils
import numpy as np

RAW_DIR = "raw/"

def import_raw_frames(coinc, group):
    file_name = str(coinc.id)+".cache"
    start_time = coinc.times[0]-2
    end_time = coinc.time[0]+2
    observatory = group.name[0]
    if observatory =='H':
        frame_type='H1_R'
    if observatory =='L':
        frame_type=='R'
    else:
        print 'frame type not determined'
    
    os.system('ligo_data_find -o '+observatory+' -t '+frame_type+' -s '+start_time+' -e '+end_time+' -l -u file > '+RAW_DIR+file_name)
    
def create_h5_data(coinc, group):
    start_time = coinc.times[0]-2
    end_time = coinc.time[0]+2
    
    channel_name = group.channels[n]
    freq = coinc.freq[n]
    hd5f_name = str(coinc.id)+channel_name+".h5"
        
    framedata = frutils.FrameChache(lal.Cache.fromfile(RAW_DIR+file_name),verbose=False).fetch(channel_name, start_time, end_time)
    data = np.array(framedata)
    timeseries = seriesutils.fromarray(data)
    seriesutils.bandpass(timeseries,freq-4, freq+4)
    band_passed_data=timeseries.data.data
