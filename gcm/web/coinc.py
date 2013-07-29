
import bottle
from gcm.data import channels as chn, coinc
from gcm.web.utils import *
import numpy as np

@bottle.get('/coinc/group/<group_id:int>')
@bottle.view('coincs.html')
def get_group(group_id):
    try:
        group = chn.get_group(group_id)
    except:
        bottle.abort(404, "No coincidences for {0}".format(group))
    
    return {'root': WEB_ROOT}

@bottle.get('/coinc/group/<group_id:int>/all')
@succeed_or_fail
def get_all_coinc(group_id):
    group = chn.get_group(group_id)
    coincs = coinc.coinc_to_list(group)
    return {'coincs': map(convert_numpy_dict, coincs)}
