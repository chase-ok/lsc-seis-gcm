
from collections import namedtuple
from gcm.data import hdf5
import numpy as np

Channel = namedtuple("Channel", "ifo subsystem name id")
ChannelGroup = namedtuple("ChannelGroup", "name channels id")

H5_FILE = "channels.h5"

channels_table = hdf5.GenericTable("channels",
                                   dtype=[("ifo", (str, 8)),
                                          ("subsystem", (str, 64)),
                                          ("name", (str, 96))],
                                   chunk_size=1)

MAX_GROUP_SIZE = 256
_CHANNEL_ID_FILL = -1

groups_table = hdf5.GenericTable("groups",
                                 dtype=[("name", (str, 128)),
                                        ("channel_ids", (np.int32, 
                                                         MAX_GROUP_SIZE))],
                                 chunk_size=1)


@hdf5.use_h5(H5_FILE, 'r')
def get_channels(h5=None):
    table = channels_table.attach(h5)
    return [Channel(id=row, **data) 
            for row, data in enumerate(table.iterdict())]
            
@hdf5.use_h5(H5_FILE, 'r')
def get_channel_by_name(ifo, subsystem, name, h5=None):
    table = channels_table.attach(h5)
    for row, match in enumerate(table.iterdict()):
        if match['ifo'] == ifo \
                and match['subsystem'] == subsystem \
                and match['name'] == name:
            return Channel(id=row, **match)
    
    raise ValueError('No such channel')

@hdf5.use_h5(H5_FILE, 'r')
def get_channel_by_id(id, h5=None):
    table = channels_table.attach(h5)
    return Channel(id=id, **table.read_dict(id))

@hdf5.use_h5(H5_FILE, 'w')
def add_channel(ifo, subsystem, name, h5=None):
    try:
        return get_channel_by_name(ifo, subsystem, name, h5=h5)
    except ValueError:
        table = channels_table.attach(h5)
        id = len(table)
        values = dict(ifo=ifo, subsystem=subsystem, name=name)
        table.append_dict(**values)
        return Channel(id=id, **values)


@hdf5.use_h5(H5_FILE, 'r')
def get_groups(h5=None):
    table = groups_table.attach(h5)
    return [_read_group(h5, id, values) 
            for id, values in enumerate(table.iterdict())]
    
@hdf5.use_h5(H5_FILE, 'r')
def get_group_by_name(name, h5=None):
    table = groups_table.attach(h5)
    for row, match in enumerate(table.iterdict()):
        if match['name'] == name:
            return _read_group(h5, row, match)
    
    raise ValueError('No such channel group')
    
@hdf5.use_h5(H5_FILE, 'r')
def get_group_by_id(id, h5=None):
    table = groups_table.attach(h5)
    return _read_group(h5, id, table.read_dict(id))
    
@hdf5.use_h5(H5_FILE, 'w')
def add_group(name, channels, h5=None):
    try:
        get_group_by_name(name, h5=h5)
        exists = True
    except ValueError: 
        exists = False
    if exists: raise ValueError('Group by the same name exists already')
    
    channel_ids = _CHANNEL_ID_FILL*np.ones(MAX_GROUP_SIZE, np.int32)
    for i, channel in enumerate(channels):
        channel_ids[i] = channel.id
    
    table = groups_table.attach(h5)
    id = len(table)
    table.append_dict(name=name, channel_ids=channel_ids)
    return ChannelGroup(name=name, channels=channels, id=id)
    
def _read_group(h5, id, values):
    channels = [get_channel_by_id(cid, h5=h5) for cid in values['channel_ids']
                if id is not _CHANNEL_ID_FILL]
    return ChannelGroup(id=id, name=values['name'], channels=channels)

