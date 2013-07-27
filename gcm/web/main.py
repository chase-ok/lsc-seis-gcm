#!/usr/bin/env python

import bottle
from bottle import route, run, request, static_file, view
from web.utils import succeed_or_fail

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/lsc-seis-gcm/static/deploy'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/html/")

#from web import excesspower
#from web import channels
#from web import triggers

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

run(server="cgi", debug=True)
