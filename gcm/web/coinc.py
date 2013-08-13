
import bottle
from gcm.data import channels as chn, coinc as co, raw
from gcm.web.utils import *
import numpy as np

@bottle.get('/coinc/group/<group_id:int>')
@bottle.view('coincs.html')
def get_group(group_id):
    return {'root': WEB_ROOT, 'group': _get_group(group_id)}

@bottle.get('/coinc/cross/group/<group_id:int>')
@bottle.view('coinc_cross.html')
def get_group(group_id):
    return {'root': WEB_ROOT, 'group': _get_group(group_id)}

@bottle.get('/coinc/group/<group_id:int>/all')
@succeed_or_fail
def get_all_coinc(group_id):
    group = chn.get_group(group_id)
    coincs = co.coincs_to_list(group)
    limit = int(bottle.request.query.limit or len(coincs))
    return {'coincs': coincs[:limit]}

@bottle.get('/coinc/group/<group_id:int>/time-series/<coinc_id:int>')
@bottle.view('coinc_time_series.html')
def get_time_series(group_id, coinc_id):
    return {'root': WEB_ROOT, 
            'group': _get_group(group_id), 
            'coinc': _get_coinc(chn.get_group(group_id), coinc_id),
            'sampling_rate': raw.SAMPLING_RATE,
            'sample_buffer': raw.SAMPLE_BUFFER,
            'sample_duration': raw.SAMPLE_DURATION}

@bottle.get('/coinc/group/<group_id:int>/time-series/<coinc_id:int>/all')
@succeed_or_fail
def get_time_series_data(group_id, coinc_id):
    group = chn.get_group(group_id)
    with co.open_coincs(group, mode='r') as coincs:
        coinc = coincs[coinc_id]
    raw_series, bandpassed = raw.get_raw_coinc(group, coinc) 
    return {'raw': [s.tolist() for s in raw_series], 
            'bandpassed': [s.tolist() for s in bandpassed]}

@bottle.view('coinc_windows.html')
def get_group(group_id):
    return {'root': WEB_ROOT, 'group': _get_group(group_id)}

def _get_group(group_id):
    try:
        group = chn.get_group(group_id)
    except:
        bottle.abort(404, "No coincidences for {0}".format(group))
    
    group_dict = group._asdict()
    group_dict['channels'] = [c._asdict() for c in group.channels]
    return group_dict

def _get_coinc(group, coinc_id):
    with co.open_coincs(group, mode='r') as coincs:
        return co.coinc_to_dict(coincs[coinc_id])
