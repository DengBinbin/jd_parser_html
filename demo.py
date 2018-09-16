#!/usr/bin/env python
# coding=utf-8
'''
调用html解析器实例
'''
import sys
sys.path.append("./src/ipin/parser/jd_parser/")
from api.api_jd_parser import JdParser
from utils.path import *
import codecs
import json

test = JdParser()
htmlContent1 = codecs.open(jd_path+'lagou/lagou.html').read()
htmlContent2 = codecs.open(co_path+'lagou/lagou.html').read()
htmlContent3 = codecs.open(xz_path+'dajie/dajie.html').read()
result1 = test.parser(htmlContent=htmlContent1,jdFrom="lagou",type="jd_detail")
result2 = test.parser(htmlContent=htmlContent2,jdFrom="lagou",type="co")
result3 = test.parser(htmlContent=htmlContent3,jdFrom="dajie",type="xiaozhao")
print u"JD解析"+"*"*30
print json.dumps(result1,ensure_ascii=False,indent=4)
print u"CO解析"+"*"*30
print json.dumps(result2,ensure_ascii=False,indent=4)
print u"XZ解析"+"*"*30
print json.dumps(result3,ensure_ascii=False,indent=4)