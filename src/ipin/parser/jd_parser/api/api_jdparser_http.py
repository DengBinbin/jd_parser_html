#!/usr/bin/env python
# coding=utf-8

import requests
import json

def jdparser(jdurl="http://jobs.zhaopin.com/317802487250086.htm"):
    URL = "http://0.0.0.0:8088/jdstring"
    response = requests.post(URL,data={ "input_url":jdurl} )
    result = json.loads(response.content)
    for k,v in result.iteritems():
        print k,v
    return result



jdparser()

