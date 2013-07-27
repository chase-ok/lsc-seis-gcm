
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
    channels = [c._asdict() for c in chn.get_channels()]
    add_limit(channels)
    return {'channels': channels}


@bottle.get('/groups')
@bottle.view('groups.html')
def index():
    return {'root': WEB_ROOT}

@bottle.get('/groups/all')
@succeed_or_fail
def get_all_channels():
    groups = [dict(id=g.id, 
                   name=g.name, 
                   channels=[c._asdict() for c in g.channels])
              for g in chn.get_groups()]
    add_limit(groups)
    return {'groups': groups}
