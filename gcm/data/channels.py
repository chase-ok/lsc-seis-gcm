
from gcm.data import make_data_path
from gcm import utils
from collections import namedtuple
import csv
import numpy as np
import os.path

Channel = namedtuple("Channel", "id ifo subsystem name")
Group = namedtuple("Group", "id name channels")

CHANNELS_FILE = "channels.csv"
GROUPS_FILE = "groups.csv"

# memoize so we effectively have a global variable
@utils.memoized
def get_channels():
    path = make_data_path(CHANNELS_FILE)
    if not os.path.exists(path): return []
    
    channels = []
    with open(path, 'rb') as f:
        reader = csv.DictReader(f)
        for line in reader:
            line['id'] = int(line['id'])
            channels.append(Channel(**line))
    return channels
    
def save_channels():
    with open(make_data_path(CHANNELS_FILE), 'wb') as f:
        writer = csv.DictWriter(f, Channel._fields)
        writer.writerow(dict((field, field) for field in Channel._fields))
        for channel in get_channels():
            writer.writerow(channel._asdict())

def add_channel(ifo, subsystem, name, autosave=True):
    channels = get_channels()
    for match in channels:
        if match.ifo == ifo and match.subsystem == subsystem \
                and match.name == name:
            return match
    
    channel = Channel(len(channels), ifo, subsystem, name)
    channels.append(channel)
    if autosave: save_channels()
    return channel
    
def get_channel(id):
    return get_channels()[id]
    
@utils.memoized
def get_groups():
    path = make_data_path(GROUPS_FILE)
    if not os.path.exists(path): return []
    
    all_channels = get_channels()
    groups = []
    with open(path, 'rb') as f:
        reader = csv.DictReader(f)
        for line in reader:
            channels = [all_channels[id] for id in eval(line['channels'])]
            groups.append(Group(int(line['id']), line['name'], channels))
    return groups
    
def save_groups():
    with open(make_data_path(GROUPS_FILE), 'wb') as f:
        writer = csv.DictWriter(f, Group._fields)
        writer.writerow(dict((field, field) for field in Group._fields))
        
        for group in get_groups():
            d = group._asdict()
            d['channels'] = str([channel.id for channel in group.channels])
            writer.writerow(d)

def add_group(name, channels, autosave=True):
    groups = get_groups()
    for match in groups:
        if match.name == name:
            if match.channels == channels:
                return match
            else:
                raise ValueError('Group channels do not match!')
    
    group = Group(len(groups), name, channels)
    groups.append(group)
    if autosave: save_groups()
    return group

def get_group(id):
    return get_groups()[id]
