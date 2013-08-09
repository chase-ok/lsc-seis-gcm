
from gcm.data import make_data_path, make_dtype, hdf5
from gcm import utils
import numpy as np
import bisect
from os.path import join

TRIGGER_DIR = "triggers/"

def make_trigger_h5_path(channel):
    name = "{0.ifo}-{0.subsystem}-{0.name}.h5".format(channel)
    return make_data_path(join(TRIGGER_DIR, name))

# TODO: change time to float64
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

cluster_dtype = trigger_dtype + make_dtype(trigger_count=np.uint32,
                                           weighted_time=np.float64,
                                           weighted_freq=np.float32,
                                           snr_sum=np.float64)

clusters_table = hdf5.GenericTable("clusters",
                                    dtype=cluster_dtype,
                                    chunk_size=2**10,
                                    initial_size=2**14)

def open_clusters(channel, **kwargs):
    return hdf5.open_table(make_trigger_h5_path(channel), clusters_table,
                           **kwargs)

def cluster_triggers(channel):
    # first round
    with open_triggers(channel, mode='r') as triggers:
        clusters = _do_clustering(triggers.iterdict())
    
    with open_clusters(channel, mode='w', reset=True) as table:
        for cluster in clusters:
            table.append_dict(**cluster)
            
def _do_clustering(source):
    clusters = []
    current_clusters = []
    
    for row, trigger in enumerate(source):
        if row % 10000 == 0: print row, len(current_clusters)
        
        time_cutoff = trigger['time_min']
        # iterate backwards so that we can remove elements in-place
        for i, cluster in reversed(list(enumerate(current_clusters))):
            if cluster['time_max'] < time_cutoff:
                clusters.append(cluster)
                current_clusters.pop(i)
        
        as_cluster = trigger # no need to copy
        found_match = False
        for i, match in reversed(list(enumerate(current_clusters))):
            if _triggers_touch(as_cluster, match):
                found_match = True
                as_cluster = _merge_trigger_into(as_cluster, match)
                current_clusters.pop(i)

        if not found_match:
            snr = trigger["snr"]
            as_cluster["trigger_count"] = 1
            as_cluster["weighted_time"] = snr*trigger["time"]
            as_cluster["weighted_freq"] = snr*trigger["freq"]
            as_cluster["snr_sum"] = snr

        current_clusters.append(as_cluster)
    clusters.extend(current_clusters)

    print "sorting"
    clusters.sort(key=lambda cluster: cluster['time_min'])

    for cluster in clusters:
        cluster["weighted_time"] /= cluster["snr_sum"]
        cluster["weighted_freq"] /= cluster["snr_sum"]

    return clusters

def _triggers_touch(trigger1, trigger2):
    time_range1 = trigger1['time_min'], trigger1['time_max']
    time_range2 = trigger2['time_min'], trigger2['time_max']
    if not _ranges_overlap(time_range1, time_range2): return False
    
    freq_range1 = trigger1['freq_min'], trigger1['freq_max']
    freq_range2 = trigger2['freq_min'], trigger2['freq_max']
    return _ranges_overlap(freq_range1, freq_range2)
        
def _ranges_overlap(range1, range2):
    return range1[0] <= range2[1] and range2[0] <= range1[1]

def _merge_trigger_into(trigger, cluster):
    trigger_snr = trigger["snr"]

    cluster['time_min'] = min(trigger['time_min'], cluster['time_min'])
    cluster['time_max'] = max(trigger['time_max'], cluster['time_max'])
    cluster['freq_min'] = min(trigger['freq_min'], cluster['freq_min'])
    cluster['freq_max'] = max(trigger['freq_max'], cluster['freq_max'])

    if trigger_snr > cluster['snr']:
        cluster['time'] = trigger['time']
        cluster['freq'] = trigger['freq']
        cluster['snr'] = trigger_snr
        cluster['amplitude'] = max(trigger['amplitude'], cluster['amplitude'])
        cluster['q'] = max(trigger['q'], cluster['q'])

    cluster["trigger_count"] += trigger.get("trigger_count", 1)
    cluster["weighted_time"] += trigger.get("weighted_time", 
                                            trigger_snr*trigger["time"])
    cluster["weighted_freq"] += trigger.get("weighted_freq", 
                                            trigger_snr*trigger["freq"])
    cluster["snr_sum"] += trigger.get("snr_sum", trigger_snr)

    return cluster
    
    