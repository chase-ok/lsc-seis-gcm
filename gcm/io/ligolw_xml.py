
from gcm.data.triggers import trigger_dtype
import numpy as np

_ATTR_MAP = dict(time='time',
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
        for attr, mapped in _ATTR_MAP.iteritems():
            triggers[i][attr] = getattr(row, mapped)
    
    return triggers