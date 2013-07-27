
from gcm.data import make_data_path, make_dtype, hdf5
from gcm import utils
import numpy as np
from os.path import join

TRIGGER_DIR = "triggers/"

def make_trigger_h5_path(channel):
    name = "{0.ifo}-{0.subsystem}-{0.name}.h5".format(channel)
    return make_data_path(join(TRIGGER_DIR, name))


trigger_dtype = make_dtype(time=np.float32,
                           time_min=np.float64,
                           time_max=np.float64,
                           freq=np.float32,
                           freq_min=np.float64,
                           freq_max=np.float64,
                           snr=np.float32,
                           amplitude=np.float64,
                           q=np.float32)
                           
trigger_table = hdf5.GenericTable("triggers",
                                  dtype=trigger_dtype,
                                  chunk_size=2**10,
                                  initial_size=2**14)


def append_triggers(channel, triggers, snr_threshold=10, h5=None):
    assert triggers.dtype == trigger_dtype
    
    with hdf5.write_h5(make_trigger_h5_path(channel), existing=h5) as h5:
        table = trigger_table.attach(h5)
        filtered = triggers[triggers['snr'] >= snr_threshold]
        if len(filtered) > 0:
            table.append_array(filtered)


class OmicronDirectoryStructure(object):
    
    def __init__(self, get_trigger_files, parse_file):
        self._file_func = get_trigger_files
        self._parser_func = parse_file
    
    def sync(self, group):
        for channel in group.channels:
            self._sync_channel(group, channel)
    
    def _sync_channel(self, group, channel):
        with hdf5.write_h5(make_trigger_h5_path(channel)) as h5:
            table = trigger_table.attach(h5)
            latest = table[-1].time_min if len(table) > 0 else 0
            
            files = self._file_func(group, channel)
            for file in files:
                start_time = self._get_start_time(file)
                if start_time < latest: continue
                
                print "Syncing {0}".format(file)
                
                triggers = self._parser_func(file)
                if len(triggers) == 0: continue
                
                append_triggers(channel, triggers, h5=h5)
                latest = triggers[-1]["time_min"]
    
    def _get_start_time(self, file):
        # ..._TIME_DURATION.extension
        return int(file.split(".")[-2].split("_")[-2])
    

def _get_scott_trigger_files(group, channel):
    base = "/home/scott.dossa/omicron/xml_triggers"
    
    #ifo, chamber = group.name.split("-")
    all_channels = base #join(base, ifo, chamber)
    channel_dir = join(all_channels, 
                       "{0.ifo}:{0.subsystem}_{0.name}".format(channel))
    
    return [join(channel_dir, name) for name in utils.get_files(channel_dir)]

def _parse_scott_triggers(file):
    from gcm.io import ligolw_xml
    return ligolw_xml.read_triggers(file)
    
scott_triggers = OmicronDirectoryStructure(_get_scott_trigger_files,
                                           _parse_scott_triggers)

