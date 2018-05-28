#!/usr/bin/env python
# coding=utf-8

import sys

import ipin.rpc.etl.jd.analyze.JdAnalyzeService as jdService
from ipin.rpc.etl.jd.jd_type.ttypes import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
import codecs
import  urllib2


def getClient(addr='192.168.1.169',port=9098):
    print 'conneting server %s at port %d' %(addr,port)
    transport = TSocket.TSocket(addr,port)
    transport = TTransport.TBufferedTransport(transport)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = jdService.Client(protocol)
    return transport,client




if __name__=="__main__":
    import os,jsonpickle,json

    try:
        transport,client = getClient("127.0.0.1")
        transport.open()

        path = "./test_jds/plain_jd/"
        fnames = [ path + fname for fname in os.listdir(path) if fname.endswith("html") ][:20]
        # for fname in fnames:
        #     print '==='*20,fname
        #     # jd_html = codecs.open(fname,'rb','gb18030').read()
        #     jd_html = codecs.open(fname,'rb').read()
        #     jd_html = unicode(jd_html,u"gb18030",errors='ignore')
        #     result = client.analyzeHtml(jd_html,jdFrom=fname)
        #     # 获取结果测试，可删除
        #     result = jsonpickle.encode(result,unpicklable = False)
        #     print json.dumps(jsonpickle.decode(result),ensure_ascii = False, indent=4)

        #html = urllib2.urlopen("http://jobs.zhaopin.com/225886818250040.htm?ssidkey=y&ss=201&ff=03")
        # result2 = test.parser_detail(fname=None,url="http://jobs.zhaopin.com/225886818250040.htm?ssidkey=y&ss=201&ff=03")
        html = urllib2.urlopen("http://jobs.zhaopin.com/225886818250040.htm?ssidkey=y&ss=201&ff=03").read()
        html=unicode(html,'gb18030',errors='ignore')
        result = client.analyzeHtml(html,'zhilian')
        result = jsonpickle.encode(result,unpicklable = False)
        print json.dumps(jsonpickle.decode(result),ensure_ascii = False, indent=4)
        transport.close()

    except Thrift.TException,e:
        print 'error: %s',e

