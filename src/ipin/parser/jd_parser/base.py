#!/usr/bin/env python
# coding=utf-8
import sys,os
import re,codecs,jieba
from tgrocery import Grocery
import numpy as np
from collections import OrderedDict,defaultdict
from copy import deepcopy
# from acora import AcoraBuilder
base_dir =  os.path.split(os.path.realpath(__file__))[0]
sys.path.append(base_dir)
sys.path.append(os.path.abspath(os.path.join(__file__,"utils/")))
from utils.util import *


reload(sys)
sys.setdefaultencoding("utf-8")
'''
正常51job、lagou等渠道JD解析基类
'''
class JdParserTop(object):
    def __init__(self):


        self.result=OrderedDict()
        self.result["jdFrom"]=""
        self.result["pubTime"]=""
        inc_keys=["incName","incScale","incType","incIndustry","incLocation","incUrl","incStage","incAliasName","investIns",
                    "incContactInfo","incCity","incZipCode","incContactName","incIntro"]
        job_keys = ["jobType","jobPosition","jobCate","jobSalary","jobWorkAge","jobDiploma","jobNum","jobWorkCity","jobWorkLoc",
                    "jobWelfare","age","jobEndTime","email","gender","jobMajorList","jobDesc"]
        others_keys=["keyWords","isFullTime","jdRemedy","posType","urgent","holidayWelfare","livingWelfare","salaryCombine",
                     "socialWelfare","trafficWelfare","jobDepartment","jobReport","jobReportDetail","jobSubSize","language","overSea"]
        jdInc = OrderedDict()
        for k in inc_keys:
            jdInc[k]=""
        self.result["jdInc"]=jdInc
        jdJob = OrderedDict()
        for k in job_keys:
            jdJob[k]=""
        self.result["jdJob"]=jdJob
        others = OrderedDict()
        for k in others_keys:
            others[k]=""
        self.result["others"]=others


        self.CLEAN_TEXT = re.compile(u"[^\u4e00-\u9fa5\w\d；:：;,。、%\.，/。！!@（）\r\n\(\)\-\+ －　`]")


        
        self.clf = Grocery(base_dir+"/jdclf")
        self.clf.load()


        self.SPLIT_LINE = re.compile(u"[\r\n；:：。！？;]|[　\s \xa0\u724b]{4,}")
        self.CLEAN_LINE = re.compile(u"^[\u2022（【\[\s\t\r\n\(\- 　]?[\da-z１２３４５７８９]{1,2}[\.,。、，：:）】\]\)\s]|^[！＠＃￥％……＆×（）\(\)｛｝：“｜、－\-，。：:\.]|^[一二三四五六七八九１２３４５６７８９\d]{0,2}[\.、\s:：　]|[，；。、\s　\.]$|^[\s　\u2022 \uff0d \u25cf]")
        self.CLEAN_JOBNAME = re.compile(u"急聘|诚聘|高薪|包[食住宿餐]|.险一金|待遇|^急?招|职位编号\s?[\s\d:：]")

        self.PAY = re.compile("(\d{3,}\-)?\d{3,}元")
        self.SEX = re.compile(u"性别|男|女")
        self.AGE = re.compile(u"\d+周?岁|年龄")
        self.JOB_TAG = re.compile(u"全职|实习")
        self.DEGREE = re.compile(u"小学|初中|高中|职技|本科|研究生|硕士|博士|教授|专科|大专|中专|无要求|不限|无限")
        self.MAIL = re.compile(u"\w+@[\w\.]+")

        self.START_DEMAND = re.compile(u"(任职资格|岗位要求|工作要求|任职条件|任职要求|职位要求)[：:\s】\n　]?")
        self.START_DUTY = re.compile(u"(工作内容|岗位职责|工作职责|职位描述|工作描述|职位介绍|职位职责|岗位描述)[:：\s 】\n　]")
        self.START_BENEFIT = re.compile(u"(福利待遇|待遇|福利)[:：\s\n】]")
        
        self.INC_URL = re.compile(u"(主页|网站|网址|官网).{0,3}[\w\d_/\.:\-]+")
        self.DEMAND = re.compile(u"精通|熟悉|熟练|有.+经验")
        self.DUTY = re.compile(u"负责|促成|为客户|安排的其.工作")
        self.BENEFIT = re.compile(u".险一金|福利|晋身|休假|带薪|补助|补贴")
        self.CERT = re.compile(u"(\S{2,8}证书|CET-\d|普通话|英语|口语|.语|日文|雅思|托福|托业)(至少)?(通过)?[\d一二三四五六七八九]级[及或]?(以上)?|(英语)?CET-\d级?(以上)?|\
                                 医学.{0,3}证|会计.{0,3}证|律师.{0,3}证|有.{1,8}证书")

        self.degreedic = set([line.strip() for line in codecs.open(base_dir+'/data/degrees.txt','rb','utf-8')])
        self.majordic = set([line.strip() for line in codecs.open(base_dir+'/data/majordic.txt','rb','utf-8')])
        self.skilldic = set([line.strip() for line in codecs.open(base_dir+'/data/skills.txt','rb','utf-8')])
        self.jobdic = set([line.strip() for line in codecs.open(base_dir+'/data/jobnames.txt','rb','utf-8')])
        self.citydic = set([line.strip() for line in codecs.open(base_dir + '/data/citydic.txt', 'rb', 'utf-8')])
        self.province_city = set([line.strip() for line in codecs.open(base_dir + '/data/province_city.txt', 'rb', 'utf-8')])


        self.SALARY = re.compile(u'万')

        jieba.load_userdict(base_dir+'/data/majordic.txt')
        jieba.load_userdict(base_dir+'/data/skills.txt')
        jieba.load_userdict(base_dir+'/data/firm.txt')
        jieba.load_userdict(base_dir+'/data/degrees.txt')
        jieba.load_userdict(base_dir+'/data/benefits.txt')
        jieba.load_userdict(base_dir + '/data/citydic.txt')
        jieba.load_userdict(base_dir + '/data/province_city.txt')


    def refresh(self):
        self.result=OrderedDict()
        self.result["jdFrom"]=""
        self.result["pubTime"]=""
        inc_keys=["incName","incScale","incType","incIndustry","incLocation","incUrl","incStage","incAliasName","investIns",
                    "incContactInfo","incCity","incZipCode","incContactName","incIntro"]
        job_keys = ["jobType","jobPosition","jobCate","jobSalary","jobWorkAge","jobDiploma","jobNum","jobWorkCity","jobWorkLoc",
                    "jobWelfare","age","jobEndTime","email","gender","jobMajorList","jobDesc"]
        others_keys=["keyWords","isFullTime","jdRemedy","posType","urgent","holidayWelfare","livingWelfare","salaryCombine",
                     "socialWelfare","trafficWelfare","jobDepartment","jobReport","jobReportDetail","jobSubSize","language","overSea"]
        jdInc = OrderedDict()
        for k in inc_keys:
            jdInc[k]=""
        self.result["jdInc"]=jdInc
        jdJob = OrderedDict()
        for k in job_keys:
            jdJob[k]=""
        self.result["jdJob"]=jdJob
        others = OrderedDict()
        for k in others_keys:
            others[k]=""
        self.result["others"]=others


    def clean_line(self,line):
        """
        清除一个句子首尾的标点符号
        """
        line = self.CLEAN_LINE.sub("",line).strip()
        line = re.sub("\s+|^/d+[；’、，／。\.]","",line)
        return line


    def clean_cnNum(self,line):
        """
        经验年限提取时，中文一二三等转为123
        """
        line = unicode(line)
        a = [u"一",u"二",u"三",u"四",u"五",u"六",u"七",u"八",u"九",u"十",u"两"]
        b = range(1,11)+[2]
        table = dict((ord(aa),bb) for aa,bb in zip(a,b))
        return line.translate(table)




    def line2vec(self,line):
        """
        句子转换为向量
        """
        vec = np.zeros(50)
        for word in jieba.cut(line):
            if word in self.w2v.vocab:
                vec += self.w2v[word]

        return vec
    
    
    def clean_jobname(self,jobname):
        """
        职位名清洗
        """
        print jobname
        if jobname.lower() in self.jobdic:
            return jobname
        else:
           res = [(lcs_len(jobname,job),job) for job in self.jobdic]
           res.sort()
           return res[-1][1]


    def desc_extract(self,soup):
        line_list= soup.find_all("p")
        return '\n'.join([line.get_text() for line in line_list])
    #去除img标签,1-7位空格,&nbsp;
    removeImg = re.compile('<img.*?>| {1,7}|&nbsp;')
    #删除超链接标签
    removeAddr = re.compile('<a.*?>|</a>')
    #把换行的标签换为\n
    replaceLine = re.compile('<tr>|<div>|</div>|</p>')
    #将表格制表<td>替换为\t
    replaceTD= re.compile('<td>')
    #将换行符或双换行符替换为\n
    replaceBR = re.compile('<br><br>|<br>')
    #将其余标签剔除
    removeExtraTag = re.compile('<.*?>')
    #将多行空行删除
    removeNoneLine = re.compile('\n+')
    def replace(self,x):
        x = re.sub(self.removeImg,"",x)
        x = re.sub(self.removeAddr,"",x)
        x = re.sub(self.replaceLine,"\n",x)
        x = re.sub(self.replaceTD,"\t",x)
        x = re.sub(self.replaceBR,"\n",x)
        x = re.sub(self.removeExtraTag,"",x)
        x = re.sub(self.removeNoneLine,"\n",x)
        #strip()将前后多余内容删除
        return x.strip()


'''
51job等渠道公司界面解析基类
'''
class CoParserTop(object):
    def __init__(self):

        self.result = OrderedDict()
        co_keys = ['incName', 'incAliasName', 'incScale', 'incType', 'incIndustry', 'incSubIndustry', 'incIntro',
                   'incIntroShort', 'incCity', 'incLocation', 'locationInfo', 'incZipCode', \
                   'incContactName', 'incContactEmail', 'incContactPhone', 'incContactQQ', 'incUrl', 'investIns',
                   'incStage', 'incLogo', 'incPhoto' \
            , 'incLabel', 'prdInfo', 'leaderInfo', 'developInfo', \
                   'incWeiboName', 'incWeiboUrl', 'incWechatName', 'incWechatUrl', 'incWechatCode']

        coInc = OrderedDict()
        for k in co_keys:
            coInc[k] = ""
        self.result["coInc"] = coInc

        self.CLEAN_TEXT = re.compile(u"[^\u4e00-\u9fa5\w\d；:：;,。、%\.，/。！!@（）\r\n\(\)\-\+ －　`]")

        self.clf = Grocery(base_dir + "/jdclf")
        self.clf.load()

        self.SPLIT_LINE = re.compile(u"[\r\n；:：。！？;]|[　\s \xa0\u724b]{4,}")
        self.CLEAN_LINE = re.compile(
            u"^[\u2022（【\[\s\t\r\n\(\- 　]?[\da-z１２３４５７８９]{1,2}[\.,。、，：:）】\]\)\s]|^[！＠＃￥％……＆×（）\(\)｛｝：“｜、－\-，。：:\.]|^[一二三四五六七八九１２３４５６７８９\d]{0,2}[\.、\s:：　]|[，；。、\s　\.]$|^[\s　\u2022 \uff0d \u25cf]")
        self.CLEAN_JOBNAME = re.compile(u"急聘|诚聘|高薪|包[食住宿餐]|.险一金|待遇|^急?招|职位编号\s?[\s\d:：]")

        self.PAY = re.compile("(\d{3,}\-)?\d{3,}元")
        self.SEX = re.compile(u"性别|男|女")
        self.AGE = re.compile(u"\d+周?岁|年龄")
        self.JOB_TAG = re.compile(u"全职|实习")
        self.DEGREE = re.compile(u"小学|初中|高中|职技|本科|研究生|硕士|博士|教授|专科|大专|中专|无要求|不限|无限")
        self.MAIL = re.compile(u"\w+@[\w\.]+")
        self.ZIP = re.compile(u"(\d{6})")
        self.QQ = re.compile(u"\d{6,10}")
        self.PHONE = re.compile(
            u"1\d{10}|0\d{11}|\d{3,4}-\d{3,4}-\d{3,4}|\d{3,4}-\d{7,8}-\d{7,8}-\d{7,8}|\d{3,4}-\d{7,8}-\d{7,8}|\d{3,4}-\d{7,8}|\d{3,4}－\d{7,8}")

        self.START_DEMAND = re.compile(u"(任职资格|岗位要求|工作要求|任职条件|任职要求|职位要求)[：:\s】\n　]?")
        self.START_DUTY = re.compile(u"(工作内容|岗位职责|工作职责|职位描述|工作描述|职位介绍|职位职责|岗位描述)[:：\s 】\n　]")
        self.START_BENEFIT = re.compile(u"(福利待遇|待遇|福利)[:：\s\n】]")

        self.INC_URL = re.compile(u"(主页|网站|网址|官网).{0,3}[\w\d_/\.:\-]+")

        self.DEMAND = re.compile(u"精通|熟悉|熟练|有.+经验")
        self.DUTY = re.compile(u"负责|促成|为客户|安排的其.工作")
        self.BENEFIT = re.compile(u".险一金|福利|晋身|休假|带薪|补助|补贴")
        self.CERT = re.compile(u"(\S{2,8}证书|CET-\d|普通话|英语|口语|.语|日文|雅思|托福|托业)(至少)?(通过)?[\d一二三四五六七八九]级[及或]?(以上)?|(英语)?CET-\d级?(以上)?|\
                                     医学.{0,3}证|会计.{0,3}证|律师.{0,3}证|有.{1,8}证书")

        self.degreedic = set([line.strip() for line in codecs.open(base_dir + '/data/degrees.txt', 'rb', 'utf-8')])
        self.majordic = set([line.strip() for line in codecs.open(base_dir + '/data/majordic.txt', 'rb', 'utf-8')])
        self.skilldic = set([line.strip() for line in codecs.open(base_dir + '/data/skills.txt', 'rb', 'utf-8')])
        self.jobdic = set([line.strip() for line in codecs.open(base_dir + '/data/jobnames.txt', 'rb', 'utf-8')])
        self.citydic = set([line.strip() for line in codecs.open(base_dir + '/data/citydic.txt', 'rb', 'utf-8')])
        self.province_city = set(
            [line.strip() for line in codecs.open(base_dir + '/data/province_city.txt', 'rb', 'utf-8')])
        self.city_area = set(
            [line.strip() for line in codecs.open(base_dir + '/data/city_area.txt', 'rb', 'utf-8')])
        self.SALARY = re.compile(u'万')




        jieba.load_userdict(base_dir + '/data/majordic.txt')
        jieba.load_userdict(base_dir + '/data/skills.txt')
        jieba.load_userdict(base_dir + '/data/firm.txt')
        jieba.load_userdict(base_dir + '/data/degrees.txt')
        jieba.load_userdict(base_dir + '/data/benefits.txt')
        jieba.load_userdict(base_dir + '/data/citydic.txt')
        jieba.load_userdict(base_dir + '/data/province_city.txt')


    def refresh(self):
        self.result = OrderedDict()
        co_keys = ['incName', 'incAliasName', 'incScale', 'incType', 'incIndustry', 'incSubIndustry', 'incIntro',
                   'incIntroShort', 'incCity', 'incLocation', 'locationInfo','incZipCode', \
                   'incContactName', 'incContactEmail', 'incContactPhone', 'incContactQQ', 'incUrl', 'investIns',
                   'incStage', 'incLogo', 'incPhoto' \
            , 'incLabel', 'prdInfo', 'leaderInfo','developInfo',\
                   'incWeiboName', 'incWeiboUrl', 'incWechatName', 'incWechatUrl', 'incWechatCode']

        coInc = OrderedDict()
        for k in co_keys:
            coInc[k] = ""
        self.result["coInc"] = coInc


# def load_model():
#     # CNN模型用，如果没用CNN需要注释
#     from config import *
#     from cnn_architecture.flatten5 import *
#     config = config()
#     # 载入已经打包好的数据
#
#     f = file(os.path.join(pkl_path,"51job_short.pkl"), 'r')
#     datasets = cPickle.load(f)
#     vocab_size = cPickle.load(f)
#     word_idx_map = cPickle.load(f)
#     # idx_word_map = cPickle.load(f)
#     print "load complete"
#     # 导入配置
#     config.vocab_size = vocab_size + 2
#     model = build_model(config)
#     model.load_weights(pkl_path + "best_weights.hdf5")
#     return model,word_idx_map,config


'''
校招解析基类
'''
class XzParserTop(object):
    def __init__(self):

        self.result = OrderedDict()
        inc_keys = ["jdFrom","incName", "incAliasName", "incLogo", "incScale", "incType", "incIndustry", "incIntro",
                    "incCity", "incLocation","incZipCode","incContactName", "incContactInfo", "incUrl"]
        # job_keys = ["pub_time", "jobEndTime", "jobPosition", "jobCate", "jobSalary", "jobWorkAge","jobDiploma", "jobDesc",
        #             "jobType","jobNum", "jobWorkCity","jobWorkLoc","jobWelfare", "jobMajorList", "age", "gender", "email",
        #             "jobCVformat", "jobMinimumDays","jobSkill","jobCertificate"]

        jdInc = OrderedDict()
        for k in inc_keys:
            jdInc[k] = ""
        self.result["jdInc"] = jdInc
        jdJob = OrderedDict()
        # for k in job_keys:
        #     jdJob[k] = ""
        self.result["jdJob"] = jdJob


        self.CLEAN_TEXT = re.compile(u"[^\u4e00-\u9fa5\w\d；:：;,。、%\.，/。！!@（）\r\n\(\)\-\+ －　`]")

        self.clf = Grocery(base_dir + "/jdclf")
        self.clf.load()

        self.SPLIT_LINE = re.compile(u"[\r\n；:：。！？;]|[　\s \xa0\u724b]{4,}")
        self.CLEAN_LINE = re.compile(
            u"^[\u2022（【\[\s\t\r\n\(\- 　]?[\da-z１２３４５７８９]{1,2}[\.,。、，：:）】\]\)\s]|^[！＠＃￥％……＆×（）\(\)｛｝：“｜、－\-，。：:\.]|^[一二三四五六七八九１２３４５６７８９\d]{0,2}[\.、\s:：　]|[，；。、\s　\.]$|^[\s　\u2022 \uff0d \u25cf]")
        self.CLEAN_JOBNAME = re.compile(u"急聘|诚聘|高薪|包[食住宿餐]|.险一金|待遇|^急?招|职位编号\s?[\s\d:：]")


        self.SEX = re.compile(u"性别|男|女")
        self.JOB_TAG = re.compile(u"全职|实习")

        self.START_DEMAND = re.compile(u"(任职资格|岗位要求|工作要求|任职条件|任职要求|职位要求)[：:\s】\n　]?")
        self.START_DUTY = re.compile(u"(工作内容|岗位职责|工作职责|职位描述|工作描述|职位介绍|职位职责|岗位描述)[:：\s 】\n　]")
        self.START_BENEFIT = re.compile(u"(福利待遇|待遇|福利)[:：\s\n】]")

        self.DEMAND = re.compile(u"精通|掌握|熟悉|熟练|有.+经验")
        self.DUTY = re.compile(u"负责|促成|为客户|安排的其.工作")
        self.BENEFIT = re.compile(u".险一金|福利|晋身|休假|带薪|补助|补贴")
        self.CERT = re.compile(u"(\S{2,8}证书|CET-\d|普通话|英语|口语|.语|日文|雅思|托福|托业)(至少)?(通过)?[\d一二三四五六七八九]级[及或]?(以上)?|(英语)?CET-\d级?(以上)?|\
                                 医学.{0,3}证|会计.{0,3}证|律师.{0,3}证|有.{1,8}证书")

        self.degreedic = set([line.strip() for line in codecs.open(base_dir + '/data/degrees.txt', 'rb', 'utf-8')])
        self.majordic = set([line.strip() for line in codecs.open(base_dir + '/data/majordic_new.txt', 'rb', 'utf-8')])
        self.skilldic = set([line.strip() for line in codecs.open(base_dir + '/data/skills.txt', 'rb', 'utf-8')])
        self.jobdic = set([line.strip() for line in codecs.open(base_dir + '/data/jobnames.txt', 'rb', 'utf-8')])
        self.position = set([line.strip() for line in codecs.open(base_dir + '/data/jobposition_new.txt', 'rb', 'utf-8')])
        self.position_prefix = set([line.strip() for line in codecs.open(base_dir + '/data/jobposition_prefix.txt', 'rb', 'utf-8')])
        self.position_postfix = set(
            [line.strip() for line in codecs.open(base_dir + '/data/jobposition_postfix.txt', 'rb', 'utf-8')])
        self.citydic = set([line.strip() for line in codecs.open(base_dir + '/data/citydic.txt', 'rb', 'utf-8')])
        self.province_city = set(
            [line.strip() for line in codecs.open(base_dir + '/data/province_city.txt', 'rb', 'utf-8')])
        self.city_area = set(
            [line.strip() for line in codecs.open(base_dir + '/data/city_area.txt', 'rb', 'utf-8')])

        jieba.load_userdict(base_dir + '/data/majordic_new.txt')
        jieba.load_userdict(base_dir + '/data/skills.txt')
        jieba.load_userdict(base_dir + '/data/jobposition.txt')
        jieba.load_userdict(base_dir + '/data/firm.txt')
        jieba.load_userdict(base_dir + '/data/degrees.txt')
        jieba.load_userdict(base_dir + '/data/benefits.txt')
        jieba.load_userdict(base_dir + '/data/citydic.txt')
        jieba.load_userdict(base_dir + '/data/province_city.txt')

        #new

        self.INTRO = re.compile(u"公司介绍|公司简介|企业简介|企业介绍|关于我们|单位简介|关于")
        self.JOBNAME_LINE = re.compile(u"岗位：|招聘岗位|实习生招聘|职位名称|招聘职位|实习岗位|岗位方向|定向岗位|岗位$|岗位名称")
        self.JOBNAME = re.compile(u".*?工程师|\S{2}专员$|\S{4,}岗$|工程师$|\S{4,}实习生招聘$|职位\d.*?分析|[^招聘]实习生$|研究员$\
            |经理|.*?实习生[((].*?[)）|培训生$]")
        self.CONTACTINFO = re.compile(u'联络方式|联络电话|固定电话|固话|电话|联系电话|QQ|联系方式|传真|Tel')
        self.CONTACTNAME = re.compile(u'联络|联系人$|联络人')
        self.NUMBER = re.compile(u'(?<=[^-Q/——_ 0123456789])([-/_ ——0123456789]{7,})')
        self.QQ = re.compile(u'QQ\d{6,}|QQ|qq')
        self.PUNCTION = re.compile(u'[~\],.;:： ，、。《》【】！#……<>；“”]')
        self.INC_URL = re.compile(u"(主页|网站|网址|官网)：(.{0,5}[\w\d_/\.:\-]+)")
        self.MAIL = re.compile(u"\w+@[\w\.]+|\w+\.\w+@[\w\.]+|\w.*?at.*?com")
        self.FORMART = re.compile(u'(邮件|简历)名称?以?(主题|格式|标题){0,}为?[~\],.;:：，、。（）《》【】！#……()-<>；“”](.*)|\
        ("|“){1,}(.*?姓名.*?)["”]|(“|"){1,}(.*?姓名.*?学校.*?)[”"]|("|“){1,}(\S{2,}-\S{2,}-\S{2,}.*?)[”"]|([ 姓名年级学校职位可入职时间-]{5,})')


        self.JOBLOC = re.compile(u"工作地址|上班地点|公司地址|工作地点|实习地点|总部地址|[^邮件](地址|地点)")
        self.MAJOR = re.compile(u"相关专业|等?专业|专业优先|以上学历|优先考虑|专业背景")
        self.AGE_LINE = re.compile(u"\d+周?岁|年龄|\d{2}岁")
        self.AGE = re.compile(u"\d{2}?\s?[\-　－~到至]?\s?\d{2}周?岁|(至少|不低于|不超过|不大于|大概|大约|不少于|大于)\d+周?岁|\d+周?岁(以上|以下|左右|上下)")
        self.WEEKTIME = re.compile(u"(每|一)周(最好)?(至少|最少|保证|起码)?(实习|工作)?[\d一二三四五六七八九十].*?(天|日)(以上)?|实习天数[\d一二三四五六七](天|日)|\
(每|一)周.*?(最好|可到岗)?(至少|最少|保证|起码)?(实习|工作)?[\d一二三四五六七八九十].*?(天|日)(以上)?")
        self.JOBLENGTH =re.compile(u"(实习期)?(至少|保证|起码)?(工作)?[\d一二三四五六七八九十]个.*?月(或)?(以上)|\
周期?.*?(\d个月[-―]{1,2}\d个月)|(实习期)?(至少|保证|起码)(工作)?[\d一二三四五六七八九十]个.*?月(以上)?|至少.{1,5}年(以上)?|(实习).{1,5}年以上")
        self.XUHAO = re.compile(u"[0123456789一二三四五六七八九]")
        self.JOBNUM_LINE = re.compile(u"招?(\d{1,}人)|招聘人数：|岗位人数|人数：")
        self.JOBNUM = re.compile(u"(\(| )?(\d{1,}[人名]?)|(\d{1,}[-_~]?\d{1,}[人名])")
        self.PHONE = re.compile(u'(?<!\d)\d{11,12}(?!\d)|\d{3,4} \d{7,8}|\d{3,4}-\d{7,8}|\d{3,4}—\d{7,8}|\d{3}-\d{3}-\d{4}|(?<!\d)\d{8}(?!\d) ')
        self.ENDTIME = re.compile(u"(\d.*?[号|日])之?.{0,5}前|截止时间(\d.*日)|截止日期(\d.*日)|(\d.*日)之前")
        self.DEGREE_LINE = re.compile(u"(最低)?学历要求|(以上)?学历")
        self.DEGREE = re.compile(u"(小学|初中|高中|职技|本科|研究生|硕士|博士|教授|专科|大专|中专|无要求|不限|Master)(?!优先)|(小学|初中|高中|职技|本科|研究生|硕士|博士|教授|专科|大专|中专|无要求|不限|无限|Master)$")


        self.SALARY = re.compile(u"\d{3,}元?\-?\d{3,}元|(本科|研究生|硕士)?\d{2,4}(元|RMB)/?(天|周|月|day|Day)|\dk[--]\dk")
        #找标题规则
        self.FIRST = re.compile(u"一、|二、|三、|四、|五、|六、|七、|八、|九、")
        self.THIRD = re.compile(u"[\[【]\S{3,6}[\[】]|^\S{4,5}：$")

        #CNN模型
        # self.model,self.word_idx_map,self.config = load_model()

        #创一个ac自动机用于关键词的匹配。
        # builder = AcoraBuilder(list(self.position))
        # self.ac = builder.build(builder)

    '''
        逐行去找信息
        self.flag是标志位，主要处理抽取信息跨行的情况：
        工作地址：
        广东省深圳市XX路

        self.extra_info有四个参数：
        第一个line是一行文本（不带标签信息）
        第二个idx是该行文本所在的行号
        第三个add_desc是是否将该行文本加入职位描述信息
        第四个clean_major为是否将之前得到的专业与技能信息进行清空
    '''
    def extra_info(self, line, idx=None, add_desc=True,clean_major = False):
        '''
        Args:
            line (): 输入一行文本
            idx (): 该行文本在段落中的行号
            add_desc (): 是否将该行信息加入职位描述中，默认True
            clean_major (): 是否清空之前的优先专业与技能需求

        Returns:

        '''
        if self.jdType == "regular":
            jobName = deepcopy(self.jobName)
        elif self.jdType == "special":
            jobName = deepcopy(self.jobNameList[idx])
        # 加入职位描述
        if add_desc:
            if self.jdJob[jobName].has_key("jobDesc"):
                self.jdJob[jobName]["jobDesc"] += line + u'\n'
            else:
                self.jdJob[jobName]["jobDesc"] =  line+u'\n'
        if clean_major:
            self.majorList = []
            self.skillList = []

        # 如果职位名发现人数情况
        if self.JOBNUM.search(jobName):
            jobNum = re.search(u"\d{1,}人", jobName).group(0)
            jobName = jobName.split(jobNum)[0]
            self.jdJob[jobName]["jobNum"] = jobNum

        if self.flag == "workloc":
            self.jdJob[jobName]["jobWorkLoc"] = line
            self.flag = None

        if self.JOBLOC.search(line):
            print 'workloc'
            if (len(line)<20  or len(line)>100) and not re.search(u"[^城]市|路",line):
                pass
            elif line.count(u"：") == 1:
                workloc = line.split("：")[1]
                if len(workloc)>60:
                    workloc = re.split(self.PUNCTION,workloc)[0]
                self.jdJob[jobName]["jobWorkLoc"] = workloc
                if not line.split("：")[1].strip():
                    self.flag = "workloc"
            elif line.count(u"：") > 1:
                for tag in filter(None, line.split(" ")):
                    if self.JOBLOC.search(tag):
                        if tag.count(u"：") == 1:
                            self.jdJob[jobName]["jobWorkLoc"] = tag.split(u"：")[1]
            #
            elif len(filter(None,self.PUNCTION.split(line)))>1:
                self.jdJob[jobName]["jobWorkLoc"] = filter(None,self.PUNCTION.split(line))[-1]

            else:
                self.flag = "workloc"


        # 专业、技能采用词库匹配，
        if self.DEMAND.search(line):
            word_split = jieba.cut(line, cut_all=True)
            # 做分词去词库匹配
            print "demand"
            for word in word_split:
                word = word.lower()
                if word in self.skilldic:
                    self.skillList.append(word)

        if self.MAJOR.search(line):
            word_split = jieba.cut(line)
            # 做分词去词库匹配
            print "major"
            for word in word_split:
                word = word.lower()
                # print word
                word = re.sub(u"相关|学校|专业",u"",word)
                if word in self.majordic:
                    self.majorList.append(word)

        if self.FORMART.search(line):
            print "format"
            if line.count(u"：") == 1 and len(line) < 30:
                self.jdJob[jobName]["jobCVformat"] = line.split(u"：")[1]
            else:
                groups = filter(None,self.FORMART.search(line).groups())
                format = groups[np.argmax(map(lambda x:len(x),groups))]
                self.jdJob[jobName]["jobCVformat"] = format
        if self.ENDTIME.search(line):
            print "endtime"
            self.jdJob[jobName]["jobEndTime"] = self.ENDTIME.search(line).group()
        if self.MAIL.search(line):
            print "email"
            if len(self.MAIL.search(line).group())>8:
                self.jdJob[jobName]["email"] = self.MAIL.search(line).group()
            else:
                if line.count(u"：")==1:
                    self.jdJob[jobName]["email"] = line.split(u"：")[1]
        if self.SALARY.search(line):
            print "salary"
            for item in re.split(u" |；|,|，",line):
                if self.SALARY.search(item):
                    if self.jdJob[jobName].has_key("jobSalary"):
                        self.jdJob[jobName]["jobSalary"] += u" "+self.SALARY.search(item).group()
                    else:
                        self.jdJob[jobName]["jobSalary"] = self.SALARY.search(item).group()

        if self.JOBNUM_LINE.search(line):
            print "jobnum"
            self.jdJob[jobName]["jobNum"] = self.JOBNUM.search(line).group()
        if self.WEEKTIME.search(line):
            print "weektime"
            self.jdJob[jobName]["jobMinimumDays"] = self.WEEKTIME.search(line).group()
        if self.JOBLENGTH.search(line):
            print "jobLength"
            self.jdJob[jobName]["jobLength"] = self.JOBLENGTH.search(line).group()
        if self.DEGREE.search(line):
            print "degree"
            line = re.sub(u"士研究生",u"士",line)
            print filter(lambda x:len(x)>1,self.DEGREE.findall(line))
            self.jdJob[jobName]["jobDiploma"] = list(set(filter(None,self.DEGREE.findall(line)[0])))
        if self.AGE_LINE.search(line):
            print "age"
            findage = self.AGE.search(line)
            if findage:
                self.jdJob[jobName]["age"] = findage.group()

        if len(self.majorList) > 0:
            self.jdJob[jobName]["jobMajorList"] = list(set(self.majorList))
        if len(self.skillList) > 0:
            self.jdJob[jobName]["jobSkill"] = list(set(self.skillList))

            # elif self.WEEKTIME.search(line):
            #     print "worktime"
            #     if line.count(u"：") == 2:
            #         worktime = self.CLEAN_TEXT.sub(u"", line.split(u"：")[1])
            #         self.jdJob[jobName]["jobMinimumDays"] = worktime
            #         if not worktime:
            #             self.flag = "worktime"
            #     else:
            #
            #         if self.flag == "worktime":
            #             self.jdJob[jobName]["jobMinimumDays"] += self.WORKTIME.search(line).group(0)
            #         else:
            #             if self.WEEKTIME.search(line).group(0).find(u"：")<2:
            #                 self.jdJob[jobName]["jobMinimumDays"] = self.WORKTIME.search(line).group(0)

    def refresh(self):
        self.result = OrderedDict()
        inc_keys = ["jdFrom", "incName", "incAliasName", "incLogo", "incScale", "incType", "incIndustry", "incIntro",
                    "incCity", "incLocation", "incZipCode", "incContactName", "incContactInfo", "incUrl"]
        # job_keys = ["pub_time", "jobEndTime", "jobPosition", "jobCate", "jobSalary", "jobWorkAge", "jobDiploma",
        #             "jobDesc",
        #             "jobType", "jobNum", "jobWorkCity", "jobWorkLoc", "jobWelfare", "jobMajorList", "age", "gender",
        #             "email",
        #             "jobCVformat", "jobMinimumDays", "jobSkill", "jobCertificate"]

        jdInc = OrderedDict()
        for k in inc_keys:
            jdInc[k] = ""
        self.result["jdInc"] = jdInc
        jdJob = OrderedDict()
        # for k in job_keys:
        #     jdJob[k] = ""
        self.result["jdJob"] = jdJob

        self.first = []
        self.second = []
        self.third = []
        # 记录jd是何种类型的，是否名企界面，是否包含表格
        self.jdType = None
        # 是否包含表格
        self.has_table = False
        # 职位名列表
        self.jobNameList = []
        self.jobNameLine = []
        self.jobType = []
        # 专业列表和技能列表
        self.majorList = []
        self.skillList = []
        self.intro_range = []
        # 用来存职位信息
        self.jdJob = defaultdict(lambda :defaultdict(unicode))


    def replace_space(self,line):
        '''
        输入：一行文本
        输出：将具有多个空格的文本替换为一个空格之后的文本
        '''
        regex = re.compile(u' +')
        line = re.sub(regex, u' ', line)
        return line

    
    def judge_eng(self,word):
        '''
        输入：一个单词
        功能：判断这个单词是否为英文
        '''
        if len(re.split(u"\w",word.lower()))>4:
            return True
        else:
            return False

    def clean_line(self, line):
        """
        清除一个句子首尾的标点符号
        """
        line = self.CLEAN_LINE.sub("", line).strip()
        line = re.sub("\s+|^/d+[；’、，／。\.]", "", line)
        return line

    def clean_cnNum(self, line):
        """
        经验年限提取时，中文一二三等转为123
        """
        line = unicode(line)
        a = [u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九", u"十", u"两"]
        b = range(1, 11) + [2]
        table = dict((ord(aa), bb) for aa, bb in zip(a, b))
        return line.translate(table)

    def line2vec(self, line):
        """
        句子转换为向量
        """
        vec = np.zeros(50)
        for word in jieba.cut(line):
            if word in self.w2v.vocab:
                vec += self.w2v[word]

        return vec

    def clean_jobname(self, jobname):
        """
        职位名清洗
        """
        print jobname
        if jobname.lower() in self.jobdic:
            return jobname
        else:
            res = [(lcs_len(jobname, job), job) for job in self.jobdic]
            res.sort()
            return res[-1][1]

    def desc_extract(self, soup):
        line_list = soup.find_all("p")
        return '\n'.join([line.get_text() for line in line_list])

    # 去除img标签,1-7位空格,&nbsp;
    removeImg = re.compile('<img.*?>| {1,7}|&nbsp;')
    # 删除超链接标签
    removeAddr = re.compile('<a.*?>|</a>')
    # 把换行的标签换为\n
    replaceLine = re.compile('<tr>|<div>|</div>|</p>')
    # 将表格制表<td>替换为\t
    replaceTD = re.compile('<td>')
    # 将换行符或双换行符替换为\n
    replaceBR = re.compile('<br><br>|<br>')
    # 将其余标签剔除
    removeExtraTag = re.compile('<.*?>')
    # 将多行空行删除
    removeNoneLine = re.compile('\n+')

    def replace(self, x):
        x = re.sub(self.removeImg, "", x)
        x = re.sub(self.removeAddr, "", x)
        x = re.sub(self.replaceLine, "\n", x)
        x = re.sub(self.replaceTD, "\t", x)
        x = re.sub(self.replaceBR, "\n", x)
        x = re.sub(self.removeExtraTag, "", x)
        x = re.sub(self.removeNoneLine, "\n", x)
        # strip()将前后多余内容删除
        return x.strip()