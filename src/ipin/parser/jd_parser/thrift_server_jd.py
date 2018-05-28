#!/usr/bin/env python
# coding=utf-8

import sys

# 要先安装这两个库
import ipin.rpc.etl.jd.analyze.JdAnalyzeService as jdService
from ipin.rpc.etl.jd.jd_type.ttypes import *

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from ipin.rpc.common.ttypes import NamedError


from api_jd_parser import JdParser

reload(sys)
sys.setdefaultencoding('utf-8')

import codecs
import logging
logging.basicConfig()


class JDHandler(object):

    def __init__(self):
        # 初始化四个网站的解析器

        self.jd_parser = JdParser()


    def analyzeHtml(self,htmlContent=None,jdFrom=None):
        """
        jd_html: 输入的html源码,
        jd_from:[lagou,51job,zhilian,liepin]中的一个
        """
        result = dict()
        result_inc = dict()
        result_job = dict()

        if not jdFrom:
            raise ValueError("jdFrom invalid")

        try:
            result = self.jd_parser.parser(htmlContent,jdFrom=jdFrom,detail=True)   # detail=False 为基础解析，True为详尽解析
        except Exception as e:
            raise NamedError(e.message)


        result_inc = result["jdInc"]
        result_job = result["jdJob"]

        # jdId 和　jdUrl 需要处理时填充
        # result["jdId"] = "None"
        # result["jdUrl"] = "None"

        result["jdInc"] = JdIncRaw(**result_inc)
        result["jdJob"] = JdJobRaw(**result_job)

        result = JdRaw(**result)

        return result




if __name__=="__main__":

    handler = JDHandler()

#    fname = "./test_jds/liepin/liepin_10.html"
#    inputstr = codecs.open(fname,'rb','utf-8').read()
#    res = handler.analyzeHtml(inputstr,jdFrom=fname)
#    print res

    processor = jdService.Processor(handler)
    transport = TSocket.TServerSocket(port=9098)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor,transport,tfactory,pfactory)
    print 'Starting the thrift server at port 9098...'
    server.serve()
    print 'done'

