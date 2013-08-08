#Plots FFT of raw bandpassed frame data and a spectagram of data round a specific event.

from pylal import frutils, Fr, seriesutils
from gcm.data import channels, coinc, hdf5
from gcm import utils
import numpy as np
import os
from glue import lal

group = channels.get_group(0)
coincs = coinc.get_coincidences_with_offsets(group, 0.5, None)
coinc=coincs[0]


RAW_DIR = "gcm/data/raw/"

def import_raw_frames(coinc, group):
    file_name = str(coinc["id"])+".cache"
    start_time = coinc['times'][0]-2
    end_time = coinc['times'][0]+2
    observatory = group.name[0]
    if observatory =='H':
        frame_type='H1_R'
    elif observatory =='L':
        frame_type=='R'
    else:
        print 'ERROR: frame type not determined'
    
    os.system('ligo_data_find -o '+observatory+' -t '+frame_type+' -s '+str(start_time)+' -e '+str(end_time)+' -l -u file > '+RAW_DIR+file_name)
    
def create_h5_data(coinc, group):
    file_name = str(coinc["id"])+".cache"
    start_time = coinc['times'][0]-2
    end_time = coinc['times'][0]+2
    freq = coinc['freqs'][0]
    channels = group.channels
    h5_name=channels[0][1]+'-'+channels[0][2].split('-')[1]+'_coinc_'+str(coinc['id'])+'.h5'
    #with hdf5.write_h5(RAW_DIR+h5_name) as h5:
    for channel in group.channels:
        channel_name=channels[0][1]+':'+channels[0][2]+'_'+channels[0][3]
        f=open(RAW_DIR+file_name)
        framedata = frutils.FrameCache(lal.Cache.fromfile(f),verbose=False).fetch(channel_name, start_time, end_time)
        f.close()
        data = np.array(framedata)
        deltaT=framedata.metadata.dt
        timeseries = seriesutils.fromarray(data, deltaT=framedata.metadata.dt)
        seriesutils.bandpass(timeseries,freq-4, freq+4)
            #band_passed_data=timeseries.data.data
    

   # with hdf5.write_h5(hdf5_name) as h5:
   #     channel_group = h5.require_group(str(channel.id))

#import_raw_frames(coinc, group)
create_h5_data(coinc,group)
