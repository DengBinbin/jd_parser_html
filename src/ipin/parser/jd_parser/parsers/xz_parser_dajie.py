#!/usr/bin/env python
# coding=utf-8
from __future__ import  absolute_import
import sys, re, codecs, jieba
from compiler.ast import flatten
import os
import requests
from copy import deepcopy
from bs4 import BeautifulSoup
from urllib2 import urlopen
from collections import OrderedDict, Counter,defaultdict
import datetime
import time
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from base import XzParserTop
from utils.util import *
from utils.path import *
reload(sys)
sys.setdefaultencoding('utf-8')



class XzParserDajie(XzParserTop):
    """
    对大街校招渠道html进行jd解析
    """

    def __init__(self):
        XzParserTop.__init__(self)
        '''
        这三个参数都是用来保存简历分块的分界线
        self.first是有明显一、二、这种类型的标题所在的行号
        self.second是JD中的加粗行所在的行号
        self.second是类似【招聘岗位】这种格式行所在的行号
        '''
        self.first = []
        self.second = []
        self.third = []
        # 记录jd是何种类型的，regular为普通JD，一个页面一份JD并且比较规范
        # special是一页多职或者带有表格信息的JD，或者其他一些JD
        self.jdType = None
        # JD是否包含表格的参数
        self.has_table = False
        '''
        params:
        self.jobNameList:存职位名的列表
        self.jobNameLine:存职位名所在行的列表
        self.jobType:存职位类型的列表
        '''
        self.jobNameList = []
        self.jobNameLine = []
        self.jobType = []
        '''
        params:
        self.majorList:优先专业列表
        self.skillList：技能要求列表
        self.intro_range:公司描述起始和终止位置，例如[2,5]代表第二行开始公司描述第五行结束公司描述
        '''
        self.majorList = []
        self.skillList = []
        self.intro_range = []
        '''
        self.jdJob主要是存JD中职位信息，每个key是职位名，对应value为文中抽取到的相应职位名的信息
        '''
        self.jdJob = defaultdict(lambda: defaultdict(unicode))

    def preprocess(self, htmlContent, fname=None, url=None):
        """
        预处理，改换换行符等
        """
        self.refresh()
        # self.__init__()
        self.result["jdInc"]["jdFrom"] = u"dajie"

        html = ""
        if url != None:
            res = requests.get(url)
            res.encoding = 'utf-8'
            html = res.text

        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read()
        if len(html) < 60:
            raise Exception("input arguments error")
        # 建立lxml树
        self.html = re.sub("<br.*?/?>|<BR.?/?>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml")

        if not url:
            if self.soup.find("div","cor-logo"):
                self.jdType = "special"
            else:
                self.jdType = "regular"
        #判断输入jd是何种类别
        if not self.jdType:
            if url.find("project") != -1:
                self.jdType = "special"
            else:
                self.jdType = "regular"

        print "the input jd type is : {0}".format(self.jdType)

        if self.jdType=="regular":
            self.sidesoup = self.soup.find("div", "p-wrap-side")
            self.innersoup = self.soup.find("div", "p-wrap-main")
        elif self.jdType=="special":
            self.outersoup = self.soup.find("div", "cor-warp-outer")
            self.innersoup = self.soup.find("div", "shadow-box")
            self.jdstr = self.innersoup.find("div", "pro-detail")
            self.job_tag = self.soup.find('div', 'hd').find('h2', 'pro-title')
            # #判断正文中是否有表格存在
            if self.innersoup.find("table"):
                self.has_table = True
        else:
            raise Exception("only support /mingqi and /zhaopin")

    #一份JD可能会有多个职位，该函数判断目前是否找到jobName的key这一字段
    def check(self,jobName,key):
        if key not in self.jdJob[jobName].keys():
            return False
        else:
            return True

    def find_title(self, list):
        '''
       输入是一个list，其中每个元素是带有标签信息的一行文本，一般情况下是一个p标签
       按照三种规则进行抽取
       '''
        for idx in range(len(list)):
            if self.FIRST.search(list[idx].get_text().strip()):
                self.first.append(idx)
            if list[idx].find("strong"):
                self.second.append(idx)
            if self.THIRD.search(list[idx].get_text()) and len(list[idx].get_text().strip()) < 20:
                self.third.append(idx)


    def judge_jobType(self):
        '''
        self.job_tag包含表格头部的一些信息，这些信息在全文搜索没找到结果的时候起辅助判断作用
        该函数是用来判断输入JD为special情况下，招聘职位后面的那一句话是否包含实习的信息
        '''
        if self.job_tag:
            if self.job_tag.get_text().find(u'实习') != -1:
                self.jobType = u'实习'
            else:
                self.jobType = u'全职'
    '''
    regular开头的是regular类型的JD解析，首先将能用规则解析出来的字段进行解析
    然后抽取简历描述——jobDesc信息，对于该字段是一大段的描述信息，需要进行一些字段的抽取，调用
    self.extra_info函数对大段落的描述文本进行信息抽取
    '''
    # incName、incAliasName、incLogo
    def regular_incinfo(self):

        # sidesoup_info
        if self.sidesoup:
            self.inc_info_soup = self.sidesoup.find('div', 'i-corp-base-info')
            if not  self.inc_info_soup:
                raise Exception("can not parser this jd , please check the url")
            self.result['jdInc']['incName'] = self.inc_info_soup.find('p').get_text()
            for token in self.inc_info_soup.find('ul').find_all('li'):
                key = token.get_text().split(u'：')[0]
                value = token.get_text().split(u'：')[1]
                if key == u'规模':
                    self.result['jdInc']['incScale'] = value
                elif key == u'行业':
                    self.result['jdInc']['incIndustry'] = value
                elif key == u'性质':
                    self.result['jdInc']['incType'] = value
                elif key == u'官网':
                    if value!=u"————":
                        self.result['jdInc']['incUrl'] = value
            incLogo = "http:"+self.inc_info_soup.find('a').find('img').attrs['src']
            if incLogo and incLogo!='http://fs1.dajie.com/corplogo/100x100.png':
                self.result['jdInc']['incLogo'] = incLogo


    def regular_jobinfo(self):
        detail_title = self.innersoup.find('div', 'p-corp-detail-title')
        find_jobName = detail_title.find('h1')
        if find_jobName:
            self.jobName = find_jobName.get_text().split()[0]

        pub_time = detail_title.find('p').find('span')
        if pub_time:
            self.jdJob[self.jobName]['pub_time'] = pub_time.get_text().split(u'于')[1]

        detail_tag = self.innersoup.find('div', 'p-corp-detail-tag')
        for token in detail_tag.find_all('dl'):
            if token.find('dt'):
                key = token.find('dt').get_text()
                value = token.find('dd')
                if re.search(u'职位亮点', key):
                    self.jdJob[self.jobName]['jobWelfare'] = u'|'.join(value.get_text().strip().split())

        detail_info = self.innersoup.find('div', 'p-corp-detail-info')
        for token in detail_info.find_all('dl'):
            if token.find('dt'):
                key = token.find('dt').get_text()
                value = token.find('dd')
                if re.search(u'工作地点', key):
                    if u',' in value:
                        self.jdJob[self.jobName]['jobWorkCity'] = value.get_text().strip().split(u'，')[0]
                        self.jdJob[self.jobName]['jobWorkLoc'] = value.get_text().strip().split(u'，')[1]
                    else:
                        self.jdJob[self.jobName]['jobWorkCity'] = value.get_text().strip()
                elif re.search(u'招聘人数', key):
                    self.jdJob[self.jobName]['jobNum'] = value.get_text().strip()
                elif re.search(u'实习天数', key):
                    self.jdJob[self.jobName]['jobMinimumDays'] = value.get_text().strip()
                elif re.search(u'岗位职责', key):
                    jobDesc = value.find('p', 'multiline').get_text().strip()
        #用抽取出来的jobDesc来抽取信息
        self.flag = None
        for idx, line in enumerate(jobDesc.split('\n')):
            # print line+"Z"*50
            self.extra_info(line, idx, add_desc=True)

    '''
    special开头的为特殊的JD，整个流程的主要思想是：
    1、先匹配到所有能用html标签找到的字段
    2、找到公司描述信息
    3、去全文中找职位名
    4、如果是多封JD可能共用一段职位描述或者有各自的职位描述，去进行相应的抽取
    5、匹配联系人信息或者其他描述中未找到，但是在JD中其他一些地方，可能能作为JD的一些参考依据
    '''

    def special_incname(self):
        '''
        1、匹配到所有能用html标签找到的字段
        '''
        if self.outersoup:
            incName = self.outersoup.find('div', 'cor-logo clearfix').find('h1').get_text('\n').split()[0]
            self.result['jdInc']['incName'] = incName

            incLogo = self.outersoup.find('div', 'cor-logo-img')
            if incLogo:
                incLogo = incLogo.find('img').attrs['src']
                if incLogo == 'http://fs1.dajie.com/corplogo/100x100.png':
                    incLogo = ""
                self.result['jdInc']['incLogo'] = incLogo
        if self.innersoup:
            for token in self.innersoup.find('div', 'project-info').find('div', 'hd').find('p', 'pro-job-kind').find_all('span'):
                # print(token.get_text('\n').split())
                if len(token.get_text('\n').split()) >=2:
                    key = token.get_text('\n').split()[0]
                    value = token.get_text('\n').split()[1]
                else:
                    key = ""
                if re.search(u'企业性质', key):
                    self.result['jdInc']['incType'] = value.strip()
                elif re.search(u'行业', key):
                    self.result['jdInc']['incIndustry'] = value.strip()

    def special_incintro(self):
        '''
        2、找到公司描述信息
        公司描述信息也混在了职位描述信息，这里主要做法是首先找JD中的关键行，使用方法self.find_title能够得到self.first,self.second,
        self.third（这三个中可能有空）
        对于这三种划分方法，先尝试first再second最后third。以self.first为例，每次首先匹配这些切分行，如果匹配到了描述公司描述信息关键词(self.INTRO)就终止，
        否则判断self.first[0]是否大于0，如果满足就将第0行到self.first[0]（不包括self.first[0]）之间的内容判断为公司描述，如果不满足判断self.first[1]
        是否满足。
        最后还没找到就将第一个加粗行之前的内容设置为公司介绍
        最后每次找到公司描述都需要将起始行和终止行加入到self.intro_range中方便之后调用
        '''
        if self.innersoup:
            self.intro = self.innersoup.find("div", "pro-detail").find_all("p")
            # 首先找到切分点

            self.find_title(self.intro)

            # 调整输入格式
            # self.intro = [self.CLEAN_LINE.sub("",line.get_text().strip()) for line in self.intro]
            self.intro = [re.sub(u":", u"：", line.get_text().strip()) for line in self.intro]

            # CNN预测,效果不好
            # self.intro = [u"51job",u"二、交易系统开发工程师实习生",u"一、量化交易员实习生"]

            # self.model_data = make_idx_data_cv(self.intro, self.word_idx_map, self.config.max_len, k=400, filter_h=5, pin=False,
            #                     config=self.config)
            #
            # result = self.model.predict(self.model_data, batch_size=1, verbose=0)
            # result_sort = [np.argsort(i)[-1] if np.max(i)>0 else None for i in result]
            # for i in range(len(self.model_data)):
            #     print self.intro[i]
            #     # print self.model_data[i]
            #     # print result[i]
            #     print "predict:{0}".format(num2label(result_sort[i]))
            # print result_sort


            # 提取公司介绍，首先从大标题去提取，然后从加粗行提取
            modes = [self.first, self.second, self.third]
            for mode in modes:
                for num in mode:
                    if self.INTRO.search(self.intro[num]):
                        next_index = mode[mode.index(num) + 1]
                        for i in range(num + 1, next_index):
                            self.result["jdInc"]["incIntro"] += self.intro[i]
                        self.intro_range.append(num)
                        self.intro_range.append(next_index - 1)

                    if self.result["jdInc"]["incIntro"]:
                        break

                if (mode and mode[0] > 0):
                    for i in range(mode[0]):
                        self.result["jdInc"]["incIntro"] += self.intro[i]
                    self.intro_range.append(0)
                    self.intro_range.append(mode[0] - 1)
                    break
                # elif (mode and mode[1] > 0):
                #     for i in range(mode[0] + 1, mode[1]):
                #         self.result["jdInc"]["incIntro"] += self.intro[i]
                #     self.intro_range.append(mode[0] + 1)
                #     self.intro_range.append(mode[1] - 1)

            if not self.result["jdInc"]["incIntro"]:
                for idx, line in enumerate(self.innersoup.find_all("p")):
                    if len(line.attrs) != 0 or line.find("strong"):
                        break
                    else:
                        self.result["jdInc"]["incIntro"] += line.get_text().strip()
                self.intro_range.append(0)
                self.intro_range.append(idx - 1)

            print "intro start:{0}---end:{1}".format(self.intro_range[0], self.intro_range[1])


    #incName、incAliasName、incLogo

    def special_jobname(self):
        '''
        3、去全文中找职位名:
        应对不同类型的JD，将其划分为两大类：有表格和无表格
        有表格情况：
        首先，无表格情况，第一个步骤就是去找职位名，这里采用了三种方法去找职位名
        一、逐行找职位名：
        第一种方法是通过自己写的规则去判断这行是否存在职位名，这种方法可能会漏掉一些职位名，如果漏掉了，就需要更改或者增加新的
        规则，以使职位名抽取更加准确
        第二种方法是用词库的方法，可以使用词库完整匹配或者部分匹配，但是词库感觉不太好，匹配效果不好
        二、从关键行去查找是否包含指示性词语，self.JOBNAME_LINE，再做进一步判断
        三、从self.job_tag中保存的招聘JD的标题中去进行查找。
        '''
        print u"JD是否包含表格: {0}".format(self.has_table)
        # 有表格情况
        if not self.has_table:
            #首先要找职位名，确定这是一封一页多职JD还是一页一职JD
            #1、逐行去找职位名

            for num in range(self.intro_range[1], len(self.intro)):

                # 方法1：自定义规则匹配法
                names = self.PUNCTION.split(self.intro[num])
                str = u""
                for idx, eachName in enumerate(names):
                    if len(eachName) == 0:
                        continue
                    if self.JOBNAME.search(eachName) and len(self.CLEAN_LINE.sub("", self.intro[num])) < 50:
                        if self.judge_eng(eachName):
                            for i in range(idx + 1):
                                str += names[i] + u" "
                            eachName = str
                        self.jobNameList.append(eachName)
                        self.jobNameLine.append(num)
                        # self.jobNameList.append(self.CLEAN_LINE.sub("", self.intro[num]))
                        # self.jobNameLine.append(num)

                        # 方法2：对长度小于阈值的行，进行标点符号切割，然后去词库进行匹配
                        # if len(self.intro[num])<50:
                        #     names= self.PUNCTION.split(self.intro[num])
                        #     str = u""
                        #     for idx,eachName in enumerate(names):
                        #         if len(eachName)==0:
                        #             continue
                        #         #print eachName
                        #         if not eachName[-1].islower() and  2 < len(eachName) < 13 and eachName.lower()[0:4] in self.position_prefix:
                        #             # print "*"*100
                        #             if self.judge_eng(eachName):
                        #                 # print idx
                        #                 for i in range(idx+1):
                        #                     str +=names[i]+u" "
                        #                 eachName = str
                        #             self.jobNameList.append(eachName)
                        #             self.jobNameLine.append(num)

            print "first_num : {0}".format(self.first)
            print "second num : {0}".format(self.second)
            print "third num : {0}".format(self.third)
            print u"从每一行直接找名字，找到:{0}个职位名".format(len(self.jobNameList))

            # 2、没找到职位名,去找能够提示职位名的特殊行
            if len(self.jobNameList) == 0:
                titleList = [self.first, self.second, self.third]
                for i in range(len(titleList)):
                    num_split = titleList[i]
                    if len(num_split) == 0:
                        continue

                    for num in range(len(num_split)):
                        # 方法1：自定义规则匹配法
                        # 找到提示岗位信息的标题行
                        if len(self.intro[num_split[num]])<20 and self.JOBNAME_LINE.search(self.intro[num_split[num]]) :

                            print u"在第{0}个提示中找到提示".format(unicode(i + 1))
                            next_index = num_split[num + 1] if num != len(num_split) - 1 else len(self.intro) - 1
                            if len(self.intro[num_split[num]]) > 10:
                                self.jobNameList.append(self.CLEAN_LINE.sub(u"", self.intro[num_split[num]]))
                                self.jobNameLine.append(num_split[num])

                            for j in range(num_split[num] + 1, next_index):
                                # 如果找到提示语下面的是带有序号的，认为是职位名
                                if self.XUHAO.search(self.intro[j]) and len(self.intro[j]) < 15:
                                    self.jobNameList.append(self.CLEAN_LINE.sub(u"", self.intro[j]))
                                    self.jobNameLine.append(j)
                                elif (next_index - num_split[num]) < 2:
                                    self.jobNameList.append(self.CLEAN_LINE.sub(u"", self.intro[j]))
                                    self.jobNameLine.append(j)
                                else:
                                    pass

                                    # 方法2：
                                    # for eachName in self.PUNCTION.split(self.intro[num_split[num]]):
                                    #     if len(eachName) == 0:
                                    #         continue
                                    #     if not eachName[-1].islower() and 2 < len(eachName) < 18 and eachName[-4:] in self.position_postfix:
                                    #         self.jobNameList.append(eachName)
                                    #         self.jobNameLine.append(num)

                    if len(self.jobNameList) > 0:
                        break

                print u"从提示语中找到:{0}个职位名".format(len(self.jobNameList))

            # 3、还是没找到职位名，去招聘概况中提取
            if len(self.jobNameList) == 0:
                if self.job_tag:
                    if self.job_tag.find(u"2016招聘") != -1 or self.job_tag.find(u"2016校园招聘") != -1 or self.job_tag.find(u"2016暑期") != -1:
                        self.jobNameList.append(re.sub(u"2016(校园)?招聘|2016暑期实习生招聘", u"",self.job_tag.get_text()))
                        self.jobNameLine.append(100)
                print u"从标题中找到:{0}个职位名".format(len(self.jobNameList))

            # 这个判断条件如果最终没有找到职位名，就抛出异常
            if len(self.jobNameLine) == 0:
                raise ("can't find any jobPosition")

            # 对职位名进行清洗，主要处理一行出现多个职位名已经职位名中存在的一些无关信息
            jobNameCopy = deepcopy(self.jobNameList)
            jobNameLineCopy = deepcopy(self.jobNameLine)
            self.jobNameList = []
            self.jobNameLine = []
            self.judge_jobType()

            for jobName, line in zip(jobNameCopy, jobNameLineCopy):
                if jobName.find(u"实习") != -1 or self.jobType == u"实习":
                    jobType = u"实习"
                else:
                    jobType = u"全职"

                # 将职位用标点或者空格切开，然后匹配
                for eachName in self.PUNCTION.split(jobName):
                    # print eachName
                    if len(eachName) != 0 and eachName[-1].islower():
                        continue
                    if 2 < len(eachName) < 13 and eachName[0:4] in self.position_postfix:
                        eachName = re.sub(u"招聘", u"", eachName.strip())
                        self.jobNameList.append(eachName)
                        self.jobNameLine.append(line)
                        self.jdJob[eachName.strip()]["jobType"] = jobType

                if len(self.jobNameList) == 0:
                    self.jobNameList = jobNameCopy
                    self.jobNameLine = jobNameLineCopy

            print "after clean jobName"

            for i, j in zip(self.jobNameList, self.jobNameLine):
                print "line{0}:{1}".format(j, i)

            print u"第一个职位名开始的行".format(self.jobNameLine[0])
            print u"职位描述开始的行".format(self.intro_range[0])
            # 如果第一个职位名出现在公司描述的前面，那么认为是没找到公司描述。
            if self.jobNameLine[0] < self.intro_range[1] or len(self.result["jdInc"]["incIntro"]) < 30:
                self.result["jdInc"]["incIntro"] = u""
            '''
            4、如果是多封JD可能共用一段职位描述或者有各自的职位描述，去进行相应的抽取
            查找职位名所对应的职位描述,这里分为单描述和多描述情况
            '''

            if len(self.jobNameList) >= 1:
                # 这里可能会有多个职位，如果每个职位都有自己的一段描述就是多描述JD，如果这些职位是共用的一段描述就是单描述
                # 首先确认单描述与多描述情况,主要依据是每个职位之间的行号差均大于3就认为是多描述，否则就是单描述。
                self.multi_desc = True
                if len(self.jobNameList) == 1:
                    self.multi_desc = False
                for i in range(1, len(self.jobNameLine)):
                    if (self.jobNameLine[i] - self.jobNameLine[i - 1]) <= 3:
                        self.multi_desc = False
                print u"JD是否为多描述:{0}".format(self.multi_desc)

                # 多描述的情况
                if self.multi_desc:
                    print self.jobNameLine
                    # num_split是用来划分整份简历的描述信息的那些行号
                    for i in [self.first, self.second, self.third]:
                        if len(i) != 0:
                            num_split = i
                    '''
                    因为多描述JD只能找到最后一个职位名出现的行号，但是它的描述结尾位置不好确定，可能出现最后还有部分
                    信息是所有职位均公用的，这里采用其他职位的平均行数信息，找到与最后一个职位名开头至少大于平均长度的关建行
                    作为最后一个职位的结束位置。
                    '''
                    aver_len = (self.jobNameLine[-1] - self.jobNameLine[0]) / (len(self.jobNameLine) - 1)
                    desc_end = len(self.intro) - 1
                    for num in num_split:
                        if num > self.jobNameLine[-1] and num - self.jobNameLine[-1] > aver_len:
                            desc_end = num
                            break

                    print u"描述信息终止位置:{0}".format(desc_end)

                    # 对于多描述情况，针对每一个职位都进行一次自己的描述信息查找
                    for idx, start_line in enumerate(self.jobNameLine):
                        self.flag = None
                        end_line = self.jobNameLine[idx + 1] if idx != len(self.jobNameLine) - 1 else desc_end
                        print "jobPostion:{0} Desc start line:{1},end line:{2}".format(idx, start_line, end_line)
                        for num in range(start_line, end_line):
                            line = self.intro[num]
                            # print line + "S" * 100
                            self.extra_info(line, idx, add_desc=True, clean_major=True)
                    # 除了独有部分，对于公有信息再进行一遍查找，公有信息包括第一个职位前面的部分和最后一个职位后面的部分
                    for idx, start_line in enumerate(self.jobNameLine):

                        self.flag = None
                        for num in range(self.intro_range[0], self.jobNameLine[0]):
                            line = self.intro[num]
                            # print line + "G" * 100
                            self.extra_info(line, idx, add_desc=False)

                        self.flag = None
                        for num in range(desc_end, len(self.intro)):
                            line = self.intro[num]
                            # print line + "G" * 100
                            self.extra_info(line, idx, add_desc=False)



                # 单描述情况
                else:
                    # 单描述情况只需要
                    for idx in range(len(self.jobNameList)):
                        self.flag = None
                        start_line = self.intro_range[-1] + 1 if len(self.intro_range) else 0
                        # self.extra_info(self.intro[start_line], idx,add_desc=False)
                        print "jobDesc start in line {0}".format(start_line)
                        for num in range(start_line, len(self.intro)):
                            line = self.intro[num]
                            # print line + "." * 100
                            self.extra_info(line, idx, add_desc=True)
            else:
                print u"没找到职位"
                pass

                # 表格分两种，一种是规整的m*n类型表格，另外一种是不规则的
        else:
            # 当表格不规整的时候，对表格进行补全，对跨了多行的项的值补充完整
            print "first_num : {0}".format(self.first)
            print "second num : {0}".format(self.second)
            print "third num : {0}".format(self.third)
            titleList = []
            tagList = []
            textList = []
            titleLine = 0
            keywords = []
            jobNameIdx = None
            '''
            titleList:用来保存表格的开头行所包含的属性值，岗位名称、招聘人数等等
            tagList是m行n列的一个二维列表（可能有缺失，因为有的单元格跨了多行），列表每一个元素都是一行的所有带td标签的单元格
            textList保存的和tagList类似，只是内容为纯文本不带html标签
            keywords是一个二维列表，size为m*2，列表的第一列是在表格开头找到的关键词，第二列是该关键所在表格中所在的列号
            '''
            # 有的表格具有thead标签
            if self.jdstr.find("table").find("thead"):
                head = self.jdstr.find("table").find("thead").find("tr").find_all("th")
                if len(head) == 0:
                    head = self.jdstr.find("table").find("thead").find("tr").find_all("td")

                if head[0].find("p"):
                    head = [item for item in head if item.find("p")]
                for item in head:
                    titleList.append(item.get_text().strip())

                rows = self.jdstr.find("table").find("tbody").find_all("tr")
                for row in rows:
                    col = row.find_all("td")
                    if col[0].find("p"):
                        col = [item for item in col if item.find("p")]

                    tagList.append(col)
                    textList.append([item.get_text().strip() for item in col])

            else:
                rows = self.jdstr.find("table").find_all("tr")
                for row in rows:
                    col = row.find_all("td")
                    if col[0].find("p"):
                        col = [item for item in col if item.find("p")]

                    if len(col) > 1 and len(titleList) == 0:
                        for item in col:
                            titleList.append(item.get_text().strip())
                    elif len(titleList) > 0:
                        # if len(col)!=0:
                        tagList.append(col)
                        textList.append([item.get_text().strip() for item in col])
                    else:
                        titleLine += 1

            print u"表格共有:{0}列".format(len(textList))

            # 因为表格的开头可能会有差异，因此当无法匹配到表格开头的时候需要修改此处的规则
            for idx, key in enumerate(titleList):

                if re.search(u"职位|招聘岗位|实习生招聘|职位名称|招聘职位|实习岗位|岗位方向|定向岗位|岗位名称", key):
                    jobNameIdx = idx
                elif re.search(u"人数|数量", key):
                    keywords.append(["jobNum", idx])
                elif re.search(u"学历", key):
                    keywords.append(["jobDiploma", idx])
                elif re.search(u"职位类型", key):
                    keywords.append(["jobType", idx])
                elif re.search(u"工作地点|工作地址", key):
                    keywords.append(["jobWorkLoc", idx])
                elif re.search(u"专业", key):
                    keywords.append(["jobMajorlist", idx])
                elif re.search(u"岗位职责|任职要求|职位描述|薪资|薪资待遇|任职条件", key):
                    keywords.append(["jobDesc", idx])

            print u"表格开头包含项:{0}".format(keywords)
            print u"职位名在第:{0}列".format(jobNameIdx)
            length = [len(col) for col in tagList]
            # 判断表格是否有缺失
            stand = True
            for le in length:
                if le != length[0]:
                    stand = False
                    break
            print u"表格是否m*n列中间无缺失嵌套?:{0}".format(stand)
            # 如果表格规整的情况
            if stand:
                if jobNameIdx != None:
                    for row in textList:
                        # 有职位名相同情况
                        if row[jobNameIdx] not in self.jobNameList:
                            self.jobNameList.append(row[jobNameIdx])
                        else:
                            self.jobNameList.append(row[jobNameIdx] + u" ")
                        # 找职位类别
                        if self.jobNameList[-1].find(u"实习") != 1 and self.jdType == u"实习":
                            self.jdJob[row[jobNameIdx]]["jobType"] = u"实习"
                        else:
                            self.jdJob[row[jobNameIdx]]["jobType"] = u"全职"
                        # 去找每个职位的信息
                        for key in keywords:
                            if key[0] == "jobDesc":
                                self.jdJob[row[jobNameIdx]][key[0]] += titleList[key[1]] + u"\n"
                                self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]] + u'\n'
                            else:
                                self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]]
            # 表格中有缺失时，需要那些单元格中含有rowspan=n 属性的td标签，并对下面n-1行信息进行补全
            else:
                min_len = len(keywords) + 1
                max_len = max(length)

                print u"在表格中，每一行的列数分别是:{0}".format(length)
                # infoLine = [ key[1] for key in keywords]
                for row, cols in enumerate(tagList):
                    print u"第{0}行表格共有：{1}项内容".format(row, len(cols))
                    for col in range(len(cols)):
                        if tagList[row][col].attrs.has_key("rowspan"):
                            shareLine = int(tagList[row][col].attrs["rowspan"])
                            for i in range(1, shareLine):
                                if len(textList[row + i]) != 0:
                                    textList[row + i].insert(col, textList[row][col])
                textList = [item for item in textList if len(item) != 0]
                for row, cols in enumerate(textList):
                    # 有职位名相同情况
                    while textList[row][jobNameIdx] in self.jobNameList:
                        textList[row][jobNameIdx] += u" "

                    self.jobNameList.append(textList[row][jobNameIdx])

                    # 判断职位类别
                    if self.jobNameList[-1].find(u"实习") != 1 and self.jdType == u"实习":
                        self.jdJob[textList[row][jobNameIdx]]["jobType"] = u"实习"
                    else:
                        self.jdJob[textList[row][jobNameIdx]]["jobType"] = u"全职"
                    # 去找每一栏信息
                    for key in keywords:

                        if key[0] == "jobDesc":
                            self.jdJob[textList[row][jobNameIdx]][key[0]] += titleList[key[1]] + u"\n"
                            self.jdJob[textList[row][jobNameIdx]][key[0]] += textList[row][key[1]] + u'\n'
                        else:
                            self.jdJob[textList[row][jobNameIdx]][key[0]] += textList[row][key[1]]

                print u"找到职位: {0}个".format(len(self.jobNameList))

            # 到此为止表格信息提取完毕，还需要提取表格之外的信息
            # 首先找到表格之外的内容，这些内容是所有职位共用的信息，对其进行全局的搜索

            # 找到所有的<p>标签存入split_table中
            def has_class_but_no_id(tag):
                return len(tag.attrs) == 0 and tag.name == "p"

            split_table = self.jdstr.find_all(has_class_but_no_id)

            for idx in range(len(self.jobNameList)):
                self.flag = None
                for line in split_table:
                    line = line.get_text()
                    # print line + "T" * 100
                    self.extra_info(line, idx, add_desc=False)

            # 之前只是照着表格中将原文抽出，如果需要抽取关键词等还需要再对表格内容进行一次抽取
            for idx, jobName in enumerate(self.jobNameList):
                keys = self.jdJob[jobName].keys()
                if "jobDesc" in keys:
                    self.flag = None
                    value = self.jdJob[jobName]["jobDesc"]
                    for line in value.split():
                        # print line + "D" * 100
                        self.extra_info(line, idx, add_desc=False, clean_major=True)
                elif "jobSalary" in keys:
                    self.flag = None
                    value = self.jdJob[jobName]["jobSalary"]
                    for line in value.split():
                        # print line + "S" * 100
                        self.extra_info(line, idx, add_desc=False)

            print u"从表格中找到:{0}个职位".format(len(self.jdJob))

    def special_contact(self):
        '''
        5、全局查找联系人和联系方式信息
        '''
        for line in self.intro:
            if line:
                contactInfo = u''
                contactName = u''
                if self.PHONE.search(line):
                    self.result["jdInc"]["incContactInfo"] = self.PHONE.search(line).group()
                if re.search(u'联络方式|微信 ：|联络电话|联系电话 ：|电话 ：|联系方式 ：|传真 ：|Tel ：',
                             re.sub(u'：', u' ： ', re.sub(u':', u'：', line))) \
                        or re.search(u'联 系 人 ：|联系人 ：|联络 ：|人员 ：|联络人', re.sub(u'：', u' ： ', re.sub(u':', u'：', line))):
                    line = re.sub(u" ", u"", line)
                    line = re.sub(u'：', u' ： ', line)
                    line = self.replace_space(line)
                    line = line.strip().split(u' ')
                    index = [index for (index, i) in enumerate(line) if i == u'：']
                    for i in range(len(index)):
                        # 只要不是最后一个冒号
                        if i != len(index) - 1:
                            if re.search(self.CONTACTINFO, line[index[i] - 1]) or re.search(self.QQ,
                                                                                            line[index[i] - 1]):
                                for j in range(index[i] - 1, index[i + 1] - 1):
                                    if len(line[j]) > 40 and not re.search(self.NUMBER, line[j]):
                                        if len(re.findall(self.PUNCTION, line[j])) > 0:
                                            last_punction = re.findall(self.PUNCTION, line[j])[-1]
                                            line[j] = line[j].split(last_punction)[-1]
                                            contactInfo += line[j] + u' '
                                    # elif re.search(self.QQ, line[j]):
                                    #     contactInfo += line[j] + u' '
                                    else:
                                        contactInfo += line[j] + u' '

                            elif re.search(self.CONTACTNAME, line[index[i] - 1]):
                                for j in range(index[i] + 1, index[i + 1] - 1):
                                    if len(line[j]) > 40 and not re.search(self.NUMBER, line[j]):
                                        if len(re.findall(self.PUNCTION, line[j])) > 0:
                                            last_punction = re.findall(self.PUNCTION, line[j])[-1]
                                            line[j] = line[j].split(last_punction)[-1]

                                            contactName += line[j] + u' '
                                    else:
                                        contactName += line[j] + u' '
                        # 是最后一个冒号
                        else:
                            if re.search(self.CONTACTINFO, line[index[i] - 1]) or re.search(self.QQ,
                                                                                            line[index[i] - 1]):
                                for j in range(index[i] - 1, len(line)):
                                    if len(line[j]) > 40 and not re.search(self.NUMBER, line[j]):
                                        if len(re.findall(self.PUNCTION, line[j])) > 0:
                                            last_punction = re.findall(self.PUNCTION, line[j])[-1]
                                            line[j] = line[j].split(last_punction)[-1]
                                            contactInfo += line[j] + u' '
                                    # elif re.search(self.QQ, line[j]):
                                    #     contactInfo += line[j] + u' '
                                    else:
                                        contactInfo += line[j] + u' '
                            elif re.search(self.CONTACTNAME, line[index[i] - 1]):
                                for j in range(index[i] + 1, len(line)):
                                    if len(line[j]) > 40 and not re.search(self.NUMBER, line[j]):
                                        if len(re.findall(self.PUNCTION, line[j])) > 0:
                                            last_punction = re.findall(self.PUNCTION, line[j])[-1]
                                            line[j] = line[j].split(last_punction)[-1]

                                            contactName += line[j] + u' '
                                    else:
                                        contactName += line[j] + u' '

                    if re.search(self.NUMBER, contactName) or re.search(u'\d{11}', contactName):
                        # print "contactName have tel"
                        tel = ""
                        find_tel = re.findall(self.NUMBER, contactName)

                        if find_tel == []:
                            find_tel = re.findall(u'\d{11}', contactName)
                        for index in range(len(find_tel)):
                            tel = find_tel[index] + u' '
                            contactName = re.sub(find_tel[index], u'', contactName)
                            contactInfo += tel + u' '

                    contactInfo = self.replace_space(contactInfo).strip()
                    if self.PUNCTION.search(contactName):
                        contactName = re.split(self.PUNCTION, contactName)[0].strip()
                    contactName = re.sub(self.PUNCTION, u'', contactName)
                    contactInfo = re.sub(u' ： ', u'：', contactInfo)
                    contactName = re.sub(u' ： ', u'：', contactName)
                    if not self.result['jdInc']['incContactInfo']:
                        self.result['jdInc']['incContactInfo'] += contactInfo + u' '
                    if contactName:
                        self.result['jdInc']['incContactName'] += self.clean_line(contactName)
                    contactInfo = u''
                    contactName = u''
                    # print "ContactInfo:", self.result['jdInc']['incContactInfo']
                    # print "ContactName:", self.result['jdInc']["incContactName"]


                elif self.INC_URL.search(line):
                    print "url"
                    self.result["jdInc"]["incUrl"] = self.INC_URL.search(line).group(2)

                    # elif self.MAIL.search(line):
                    #     print "mail"
                    #     self.result["jdJob"]["email"] = self.MAIL.search(line).group(0)



    def parser_xz(self, htmlContent=None, fname=None, url=None):
        self.preprocess(htmlContent, fname, url)

        if self.jdType=="regular":
            self.regular_incinfo()
            self.regular_jobinfo()
        elif self.jdType=="special":
            self.special_incname()
            self.special_incintro()
            self.special_jobname()
            self.special_contact()
        self.result["jdJob"] = self.jdJob

        return self.result


if __name__ == "__main__":
    import os, json
    #url = sys.argv[1]

    test = XzParserDajie()
    # path = xz_path + 'yjs/'
    # fnames = [path + fname for fname in os.listdir(path) if fname.endswith("42810.html")]
    tag = time.time()

    # for fname in fnames:
    #     print '==' * 20, fname
    #     htmlContent = codecs.open(fname, 'rb', 'utf-8').read()
    #     result = test.parser(htmlContent=htmlContent, fname=None, url=None)
        # print json.dumps(result, ensure_ascii=False, indent=4)
    # result = test.parser_xz(url="http://www.yjbys.com/mingqi/jobshow47689.html")

    result = test.parser_xz(url = "http://campus.dajie.com/project/catch/74805")
    print json.dumps(result, ensure_ascii=False, indent=4)

    print "total time {0}".format(time.time()-tag)


