
from gcm.data import make_data_path, make_dtype, hdf5
from gcm import utils
import numpy as np
import bisect
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

def open_triggers(channel, **kwargs):
    return hdf5.open_table(make_trigger_h5_path(channel), trigger_table,
                           **kwargs)


def append_triggers(channel, triggers, snr_threshold=5):
    assert triggers.dtype == trigger_dtype
    
    with open_triggers(channel, mode='w') as table:
        if snr_threshold > 0:
            triggers = triggers[triggers['snr'] >= snr_threshold]
        if len(triggers) > 0:
            table.append_array(triggers)


def time_to_trigger_index(table, time, low=0, high=None):
    if low < 0: raise ValueError('low must be non-negative')
    if high is None: high = len(table)
    while low < high:
        mid = (low + high)//2
        if table[mid].time_min < time: low = mid + 1
        else: high = mid
    return low
    

density_freq_bins = np.logspace(-1, 2, 8)
density_time_chunk = 100 # secs
density_dtype = [('time', np.uint32), 
                 ('density', (np.float32, (density_freq_bins.size,)))]

density_table = hdf5.GenericTable("densities",
                                  dtype=density_dtype,
                                  chunk_size=2**10,
                                  initial_size=2**14)

def open_densities(channel, **kwargs):
    return hdf5.open_table(make_trigger_h5_path(channel), density_table,
                           **kwargs)

def compute_densities(channel):
    with open_densities(channel, mode='w', reset=True) as densities:
        with open_triggers(channel, mode='r') as triggers:
            index = 0
            num_triggers = len(triggers)
            bins = density_freq_bins
            num_bins = len(bins)
            
            start = triggers[0].time_min
            end = triggers[-1].time_min
            assert start < end
            
            sums = np.zeros_like(bins).astype(np.float32)
            for chunk in range(start, end, density_time_chunk):            
                cutoff = chunk + density_time_chunk
                
                sums.fill(0)
                while index < num_triggers:
                    trigger = triggers[index]
                    if trigger.time_min > cutoff: break
                    
                    bin = min(num_bins-1, bisect.bisect(bins, trigger.freq))
                    duration = trigger.time_max - trigger.time_min
                    bandwidth = trigger.freq_max - trigger.freq_min
                    sums[bin] += trigger.snr*duration*bandwidth
                    index += 1
                
                densities.append_row((chunk, sums/density_time_chunk))
                print chunk, sums

clusters_table = hdf5.GenericTable("clusters",
                                    dtype=trigger_dtype,
                                    chunk_size=2**10,
                                    initial_size=2**14)
def open_clusters(channel, **kwargs):
    return hdf5.open_table(make_trigger_h5_path(channel), clusters_table,
                           **kwargs)

def cluster_triggers(channel):
    with open_triggers(channel, mode='r') as triggers:
        clusters = []
        current_clusters = []
        current_row = 0
        
        for row, trigger in enumerate(triggers.iterdict()):
            if row % 10000: print row, len(triggers), len(current_clusters)
            
            time = trigger.time_min
            # iterate backwards so that we can remove elements in-place
            for index, cluster in reversed(enumerate(current_clusters)):
                if cluster.time_max < time:
                    clusters.append(cluster)
                    current_clusters.pop(index)
            
            for index, cluster in reversed(enumerate(current_clusters)):
                if _triggers_touch(trigger, cluster):
                    trigger = _merge_trigger_into(trigger, cluster)
                    current_clusters.pop(index)
            current_clusters.append(trigger)
        
        clusters.extend(current_clusters)
    
    print "sorting"
    clusters.sort(key=lambda trigger: trigger.time_min)
    
    print "appending"
    with open_clusters(channel, mode='w') as table:
        for cluster in clusters:
            table.append_dict(cluster)

def _triggers_touch(trigger1, trigger2):
    time_min1, time_min2 = trigger1['time_min'], trigger2['time_min']
    time_max1, time_max2 = trigger1['time_max'], trigger2['time_max']
    if time_min2 <= time_min1 <= time_max2 or\
            time_min1 <= time_min2 <= time_max1:
        freq_min1, freq_min2 = trigger1['freq_min'], trigger2['freq_min']
        freq_max1, freq_max2 = trigger1['freq_max'], trigger2['freq_max']
        
        return freq_min2 <= freq_min1 <= freq_max2 or\
               freq_min1 <= freq_min2 <= freq_max1
    else:
        return False

def _merge_trigger_into(trigger, cluster):
    cluster['time_min'] = min(trigger['time_min'], cluster['time_min'])
    cluster['time_max'] = max(trigger['time_max'], cluster['time_max'])
    cluster['freq_min'] = min(trigger['freq_min'], cluster['freq_min'])
    cluster['freq_max'] = max(trigger['freq_max'], cluster['freq_max'])
    cluster['time'] = (cluster['time_min'] + cluster['time_max'])/2
    cluster['freq'] = (cluster['freq_min'] + cluster['freq_max'])/2
    cluster['snr'] = max(trigger['snr'], cluster['snr'])
    cluster['amplitude'] = max(trigger['amplitude'], cluster['amplitude'])
    cluster['q'] = max(trigger['q'], cluster['q'])
    return cluster
    
    