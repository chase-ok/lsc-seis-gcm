
from gcm.data.triggers import trigger_dtype
import numpy as np

_ATTR_MAP = dict(time='peak_time',
                 time_min='tstart', time_max='tend',
                 freq='frequency',
                 freq_min='fstart', freq_max='fend',
                 amplitude='amplitude',
                 snr='snr',
                 q='q')

def read_triggers(path):
    from glue.ligolw import array, param, ligolw, table, lsctables, utils
    class ContentHandler(ligolw.LIGOLWContentHandler): pass
    for module in [array, param, table, lsctables]:
        module.use_in(ContentHandler)

    xml_doc = utils.load_filename(path, contenthandler=ContentHandler)
    table = table.get_table(xml_doc, lsctables.SnglBurstTable.tableName)
    
    triggers = np.empty(len(table), trigger_dtype)
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