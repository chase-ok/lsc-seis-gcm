#!/usr/bin/env python

import bottle
from bottle import route, run, request, static_file, view

from gcm.data import hdf5
hdf5.use_locking = False

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/lsc-seis-gcm/static/deploy'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/html/")

#from gcm.web import channels

@route('/')
def index():
    return "hello world!"

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

run(server="cgi", debug=True)
