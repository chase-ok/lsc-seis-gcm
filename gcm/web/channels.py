
import bottle
from gcm.data import channels as chn
from gcm.web.utils import *
import numpy as np

@bottle.get('/channels')
@bottle.view('channels.html')
def index():
    return {'root': WEB_ROOT}

@bottle.get('/channels/all')
@succeed_or_fail
def get_all_channels():
    channels = [convert_numpy_dict(c.todict()) 
                for c in chn.get_channels()]
    add_limit(channels)
    return {'channels': channels}
