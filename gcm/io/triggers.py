
from gcm.data import triggers as tr
from gcm import utils
import numpy as np
from os.path import join

_ROOT_ATTR_MAP = dict(time='time',
                      time_min='tstart', time_max='tend',
                      freq='frequency',
                      freq_min='fstart', freq_max='fend',
                      amplitude='amplitude',
                      snr='snr',
                      q='q')

def parse_root_triggers(path):
    # Let's not load this library unless we have to (it takes a long time)
    from rootpy.io import root_open
    
    with root_open(path) as f:
        tree = f.triggers
        tree.create_buffer()
        buffer = tree._buffer
        
        triggers = np.empty(len(tree), dtype=tr.trigger_dtype)        
        for i, _ in enumerate(tree):
            # need to iterate the tree, hence the _ enumerate result
            for attr, mapped in _ROOT_ATTR_MAP.iteritems():
                triggers[i][attr] = buffer[mapped].value
    
    return triggers


def parse_xml_triggers(path):
    from glue.ligolw import array, param, ligolw, table, lsctables
    from glue.ligolw import utils as lw_utils
    class ContentHandler(ligolw.LIGOLWContentHandler): pass
    for module in [array, param, table, lsctables]:
        module.use_in(ContentHandler)

    xml_doc = lw_utils.load_filename(path, contenthandler=ContentHandler)
    table = table.get_table(xml_doc, lsctables.SnglBurstTable.tableName)
    
    triggers = np.empty(len(table), tr.trigger_dtype)
    for i, row in enumerate(table):
        triggers[i]['time'] = row.peak_time + row.peak_time_ns*1e-9
        triggers[i]['time_min'] = row.start_time + row.start_time_ns*1e-9
        triggers[i]['time_max'] = row.stop_time + row.stop_time_ns*1e-9
        triggers[i]['freq'] = row.central_freq
        triggers[i]['freq_min'] = row.flow
        triggers[i]['freq_max'] = row.fhigh
        triggers[i]['amplitude'] = row.amplitude
        triggers[i]['snr'] = row.snr
        triggers[i]['q'] = 0.0 # not available in xml
    
    return triggers


class TriggerSource(object):
    
    def sync(self, group):
        for channel in group.channels:
            self.sync_channel(group, channel)
    
    def sync_channel(self, group, channel):
        raise NotImplemented


class Omicron(TriggerSource):
    
    def sync_channel(self, group, channel):
        with tr.open_triggers(channel, mode='w') as table:
            latest = table[-1].time_min if len(table) > 0 else 0
            
            for file in self._get_files(group, channel):
                start_time = self._get_start_time(file)
                if start_time < latest: continue
                
                print "Syncing {0}".format(file)
                
                triggers = self._parse_file(file)
                if len(triggers) == 0: continue
                
                tr.append_triggers(channel, triggers)
                latest = triggers[-1]["time_min"]
    
    def _get_files(self, group, channel):
        raise NotImplemented
        
    def _parse_file(self, file):
        raise NotImplemented
    
    def _get_start_time(self, file):
        # ..._TIME_DURATION.extension
        return int(file.split(".")[-2].split("_")[-2])

class _ScottXmlTriggers(Omicron):
    
    def _get_files(self, group, channel):
        base = "/home/scott.dossa/omicron/xml_triggers"
    
        #ifo, chamber = group.name.split("-")
        all_channels = base #join(base, ifo, chamber)
        channel_dir = join(all_channels, 
                           "{0.ifo}:{0.subsystem}_{0.name}".format(channel))
        
        return [join(channel_dir, name) 
                for name in utils.get_files(channel_dir)]
                
    def _parse_file(self, file):
        return parse_xml_triggers(file)


default_source = _ScottXmlTriggers()
