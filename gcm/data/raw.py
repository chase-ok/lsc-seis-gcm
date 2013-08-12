from gcm.data import make_data_path, make_dtype, hdf5
from gcm.data import coinc as co, channels as chn
from gcm import utils
import numpy as np
import bisect
from os.path import join

RAW_DIR = "raw/"

def make_raw_h5_path(group):
    name = "{0.name}.h5".format(group)
    return make_data_path(join(RAW_DIR, name))

def find_raw_data_for_coincs(group):
    coincs = co.coincs_to_list(group)

    with hdf5.write_h5(make_raw_h5_path(group)) as h5:
        for coinc in coincs:
            for channel_id in 

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

                           
trigger_table = hdf5.GenericTable("triggers",
                                  dtype=trigger_dtype,
                                  chunk_size=2**10,
                                  initial_size=2**14)
