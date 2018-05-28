#coding=utf-8
'''
逐行测试时间性能
'''
#测试51job渠道JD解析时间开销
# from jd_parser_51job import *
# from path import *
# test = JdParser51Job()
# path = jd_path+'51job/'
# htmlContent = codecs.open(path+'39067759.html','r','utf-8').read()
# test.preprocess(htmlContent)
# test.regular_incname()
# test.regular_inc_tag()
# test.regular_pubtime()
# test.regular_jobname()
# test.regular_job_tag()
# test.regular_pay()
# test.regular_degree()
# test.regular_major()
# test.regular_exp()
# test.regular_language()
# test.regular_workplace()
# test.regular_benefit()
# test.regular_other()

#测试51job渠道CO解析时间开销
from co_parser_51job import *

test = CoParser51Job()
path = co_path+'co_51job/'
htmlContent = codecs.open(path+'100006.html','r','utf-8').read()
test.preprocess(htmlContent)
test.regular_incname()
test.regular_inc_tag()
test.regular_incplace()
test.regular_contactInfo()
test.regular_inclogo()