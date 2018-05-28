#!/usr/bin/env python
# coding=utf-8
import requests
import re,os,sys,codecs
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))

from parsers.jd_parser_lagou import JdParserLagou
from parsers.jd_parser_zhilian import JdParserZhiLian
from parsers.jd_parser_51job import JdParser51Job
from parsers.jd_parser_liepin import JdParserLiePin
from parsers.jd_parser_jobui import JdParserJobUI
from parsers.jd_parser_58tc import JdParser58tc
from parsers.jd_parser_highpin import JdParserHighPin

from parsers.co_parser_51job import CoParser51Job
from parsers.co_parser_zhilian import  CoParserZhilian
from parsers.co_parser_jobui import CoParserJobUI
from parsers.co_parser_liepin import CoParserLiePin
from parsers.co_parser_lagou import CoParserLagou

from parsers.xz_parser_yjbys import XzParserYJBYS
from parsers.xz_parser_yingjiesheng import XzParserYingJieSheng
from parsers.xz_parser_dajie import XzParserDajie
from parsers.xz_parser_zhilian import XzParserZhilian

import simplejson as json
import time
import traceback

reload(sys)
sys.setdefaultencoding('utf-8')


class JdParser(object):
    """
    lagou,智联和51job的html解析接口

    """

    def __init__(self):
        """
        声明5个html－jd解析器和一个简单文本解析器、5个html-co解析器

        """
        #jd解析调用解析器
        self.jd_parser_lagou = JdParserLagou()
        self.jd_parser_51job = JdParser51Job()
        self.jd_parser_zhilian = JdParserZhiLian()
        self.jd_parser_liepin = JdParserLiePin()
        self.jd_parser_jobui = JdParserJobUI()
        self.jd_parser_58tc = JdParser58tc()
        self.jd_parser_highpin = JdParserHighPin()
        #co解析调用解析器
        self.co_parser_51job = CoParser51Job()
        self.co_parser_zhilian = CoParserZhilian()
        self.co_parser_jobui = CoParserJobUI()
        self.co_parser_liepin = CoParserLiePin()
        self.co_parser_lagou = CoParserLagou()
        #调用校招解析器
        self.xz_parser_yjs = XzParserYJBYS()
        self.xz_parser_yingjiesheng = XzParserYingJieSheng()
        self.xz_parser_dajie = XzParserDajie()
        self.xz_parser_zhilain = XzParserZhilian()

    def parser(self,htmlContent=None,fname=None,url=None,jdFrom=None,type = 'detail'):
        """
        :htmlContent 输入的html源码,
        :jd_from [lagou,51job,zhilian,liepin]中的一个
        :return 基本解析结果，仅仅做提取

        """
        if not jdFrom:
            raise ValueError("jdFrom invalid")
        if type=="co":
            p = None
            if re.search(u"lagou", jdFrom):
                p = self.co_parser_lagou
            elif re.search(u"zhilian", jdFrom):
                p = self.co_parser_zhilian
            elif re.search(u"51job", jdFrom):
                p = self.co_parser_51job
            elif re.search(u"liepin", jdFrom):
                p = self.co_parser_liepin
            elif re.search(u"jobui", jdFrom):
                p = self.co_parser_jobui
            elif re.search(u"58.com", jdFrom):
                p = self.jd_parser_58tc
            elif re.search(u"highpin", jdFrom):
                p = self.jd_parser_highpin
            else:
                raise NameError("jdFrom invalid")

            result = p.parser_co(htmlContent=htmlContent, url=url)

        elif type=="xiaozhao":
            p=None
            if re.search(u"yjbys", jdFrom):
                p = self.xz_parser_yjs
            elif re.search(u"yingjiesheng", jdFrom):
                p = self.xz_parser_yingjiesheng
            elif re.search(u"dajie", jdFrom):
                p = self.xz_parser_dajie
            elif re.search(u"zhilian", jdFrom):
                p = self.xz_parser_zhilain
            else:
                raise NameError("jdFrom invalid")
            result = p.parser_xz(htmlContent=htmlContent, url=url)

        else:
            p = None
            if re.search(u"lagou",jdFrom):
                p = self.jd_parser_lagou
            elif re.search(u"zhilian",jdFrom):
                p = self.jd_parser_zhilian
            elif re.search(u"51job",jdFrom):
                p = self.jd_parser_51job
            elif re.search(u"liepin",jdFrom):
                p = self.jd_parser_liepin
            elif re.search(u"jobui",jdFrom):
                p = self.jd_parser_jobui
            elif re.search(u"58.com",jdFrom):
                p = self.jd_parser_58tc
            elif re.search(u"highpin",jdFrom):
                p = self.jd_parser_highpin
            else:
                raise NameError("jdFrom invalid")

            if type=="jd_detail":

                result = p.parser_detail(htmlContent=htmlContent,url=url)  # 默认为详尽解析
            else:

                result = p.parser_basic(htmlContent=htmlContent,url=url)  # 更少字段但准确率较高的解析结果


        return result

def jd_parser_http(htmlContent=None,jdFrom="zhilian",url="http://192.168.1.169:8088/jdstring"):
    """
    http 调用接口
    """

    result = requests.post(url,data={"htmlContent":htmlContent,"jdFrom":jdFrom})

    return result.content




if __name__=="__main__":
    test = JdParser()
    #url = "http://www.lagou.com/jobs/1407711.html?source=home_hot&i=home_hot-0"
    #r = requests.get(url)
    jd_from = "58.com"
    with open("./test_jds/58tc/58tc.html") as f:
        html = f.read()
    if '51job' in jd_from:
        r.encoding = 'gbk'
    res = test.parser(html, jdFrom=jd_from)
    print res

