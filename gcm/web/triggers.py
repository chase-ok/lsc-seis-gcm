
import bottle
from gcm.data import channels as chn, triggers as tr
from gcm.web.utils import *
import numpy as np

@bottle.get('/triggers/channel/<channel_id:int>')
@bottle.view('triggers.html')
def get_channel(channel_id):
    try:
        channel = chn.get_channel(channel_id)
    except:
        bottle.abort(404, "No triggers for {0}".format(channel_id))
        
    with tr.open_triggers(channel, mode='r') as table:
        time_min = table[0].time_min
        time_max = table[-1].time_max
        num = len(table)
    
    return {'root': WEB_ROOT,
            'channel': channel._asdict(),
            'time_min': time_min,
            'time_max': time_max,
            'num_triggers': num}

@bottle.get('/triggers/channel/<channel_id:int>/<start_time:int>-<end_time:int>')
@succeed_or_fail
def get_triggers_in_range(channel_id, start_time, end_time):
    if start_time >= end_time: 
        raise ValueError('Start time must come before end time!')
    
    limit = int(bottle.request.query.limit or 100)
    clustered = get_bool_query("clustered", default=True)
    channel = chn.get_channel(channel_id)
    
    context = tr.open_clusters if clustered else tr.open_triggers
    with context(channel, mode='r') as table:
        low_index = tr.time_to_trigger_index(table, start_time)
        max_high = min(len(table), low_index + limit)
        high_index = tr.time_to_trigger_index(table, end_time,
                                              low=low_index, high=max_high)
        triggers = [table.read_dict(i) for i in xrange(low_index, high_index)]

    return {'triggers': triggers}
    
@bottle.get('/triggers/channel/<channel_id:int>/densities')
@succeed_or_fail
def get_densities(channel_id):
    channel = chn.get_channel(channel_id)
    
    with tr.open_densities(channel, mode='r') as table:
        times = table.dataset[:len(table), "time"]
        densities = table.dataset[:len(table), "density"]

    return {'frequencies': tr.density_freq_bins.tolist(),
            'times': times.tolist(),
            'densities': densities.tolist()}
