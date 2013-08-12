#!/usr/bin/env python

import bottle
from bottle import route, run, request, static_file, view

@route('/')
def index():
    return "hello world!"

run(server="cgi", debug=True)
