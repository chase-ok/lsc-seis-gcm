#Plots FFT of raw bandpassed frame data and a spectagram of data round a specific event.

from pylal import frutils, Fr, seriesutils
from gcm.data import channels, coinc, hdf5, make_data_path
import numpy as np
import os
from glue import lal

RAW_DIR = "gcm/data/raw/"


# Creates a frame cache file for times around the coincidence arguement
def import_raw_frames(coinc, group):
    file_name = str(coinc["id"])+".cache"
    start_time = coinc['times'][0]-2
    end_time = coinc['times'][0]+2
    observatory = group.name[0]
    if observatory =='H':
        frame_type='H1_R'
    elif observatory =='L':
        frame_type='R'
    else:
        print 'ERROR: frame type not determined'
    
    os.system('ligo_data_find -o '+observatory+' -t '+frame_type+' -s '+str(start_time)+' -e '+str(end_time)+' -l -u file > '+RAW_DIR+file_name)
    

#Creates a hdf5 file of raw bandpassed frame data for each chananel with one data set per channel.
def create_h5_data(coinc, group):
   
    #defining important variables
    file_name = str(coinc["id"])+".cache"
    start_time = coinc['times'][0]-2
    end_time = coinc['times'][0]+2
    freq = coinc['freqs'][0]
    channels = group.channels
    
    #temporary file, will create better file naming system soon
    name='/home/scott.dossa/dev-seis/lsc-seis-gcm/gcm/data/raw/temp.h5'

    #open h5 file
    with hdf5.write_h5(name) as h5:


        #for each channel, generate bandpassed data
        for channel in group.channels:
            channel_name=channels[0][1]+':'+channels[0][2]+'_'+channels[0][3]
            f=open(RAW_DIR+file_name)
            framedata = frutils.FrameCache(lal.Cache.fromfile(f),verbose=False).fetch(channel_name, start_time, end_time)
            f.close()
            data = np.array(framedata)
            deltaT=framedata.metadata.dt
            timeseries = seriesutils.fromarray(data, deltaT=framedata.metadata.dt)
            if freq>1:
                seriesutils.bandpass(timeseries,freq-1, freq+1)
            else:
                seriesutils.bandpass(timeseries, 0.0001, 2)
            band_passed_data=timeseries.data.data
            times = np.arange(start_time, end_time, deltaT)

            #send bandpassed data to a dataset in the h5 file.
            channel_group=h5.require_group(str(channel.id))
            group.require_dataset(name=self.name,
                                  shape=(self.initial_size,),
                                  dtype=self.dtype,
                                  chunks=(self.chunk_size,),
                                  maxshape=(None,),
                                  compression=self.compression,
                                  fletcher32=True,
                                  exact=False)
            #table = channel_group.require_dataset(name=str(coinc['id']),
                                  #                data=band_passed_data,
                                   #               maxshape=(None,None),
                                    #              shape=(1,2))
                                                 
group = channels.get_group(2)
coincs = coinc.get_coincidences_with_offsets(group, 0.5, None)
coinc=coincs[0]            
try:
    with open(RAW_DIR+str(coinc["id"])+".cache"): pass
except:
    import_raw_frames(coinc, group)
create_h5_data(coinc,group)


