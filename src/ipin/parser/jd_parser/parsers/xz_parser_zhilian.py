#!/usr/bin/env python
# coding=utf-8
from __future__ import  absolute_import
import sys, re, codecs, jieba
from compiler.ast import flatten
import os
from copy import deepcopy
import time
from bs4 import BeautifulSoup
from urllib2 import urlopen
from collections import OrderedDict, Counter,defaultdict
import requests
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from base import XzParserTop
from utils.path import *
from utils.util import *
reload(sys)
sys.setdefaultencoding('utf-8')



class XzParserZhilian(XzParserTop):
    """
    对智联校招html进行jd解析
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
        self.result["jdInc"]["jdFrom"] = u"zhilian"

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
        #建立lxml树
        self.html = re.sub("<br.*?/?>|<BR.?/?>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml")
        #智联渠道只有一种情况，没有特殊情况
        self.jdType = 'regular'
        print "the input jd type is : {0}".format(self.jdType)

        if self.jdType == "regular":
            self.headsoup = self.soup.find("div", "cMain")
            self.jdstr = self.headsoup.find('div','cLeft').find('div', 'cJobDetail_tabSwitch mt30').find('div','cJobDetail_tabSwitch_content j_cJobDetail_tabSwitch_content')


    def judge_jobType(self):

        if self.job_tag:
            if self.job_tag.get_text().find(u'实习') != -1:
                self.jobType = u'实习'
            else:
                self.jobType = u'全职'

    # incName、incAliasName、incLogo
    def regular_incinfo(self):

        self.cLeft = self.headsoup.find('div', 'cLeft')
        self.cRight = self.headsoup.find('div', 'cRight')

        if self.cLeft:
            self.cJobDetailInforWrap = self.cLeft.find('div', 'cJobDetailInforWrap')
            for item in self.cJobDetailInforWrap.find_all('ul'):
                if item.find('li',id='jobCompany'):
                    self.result['jdInc']['incName'] = item.find('li', id='jobCompany').get_text().strip()
                    cIncDetail = item.find_all('li', 'cJobDetailTit')
                    for token in cIncDetail:
                        # print(token)
                        if re.search(u'公司行业：', token.get_text().strip()):
                            self.result['jdInc']['incIndustry'] = token.find_next('li').get_text().strip()
                        elif re.search(u'公司规模：', token.get_text().strip()):
                            self.result['jdInc']['incScale'] = token.find_next('li').get_text().strip()
                        elif re.search(u'公司类型：', token.get_text().strip()):
                            self.result['jdInc']['incType'] = token.find_next('li').get_text().strip()
                else:
                    cJobDetail = item.find_all('li', 'cJobDetailTit marb')
                    for token in cJobDetail:
                        # print(token)
                        if re.search(u'薪：', token.get_text().strip()):
                            self.yuexin = token.find_next('li').get_text().strip()
                            # print(self.yuexin)
                        elif re.search(u'历：', token.get_text().strip()):
                            self.xueli = token.find_next('li').get_text().strip()
                        elif re.search(u'工作地点', token.get_text().strip()):
                            self.gongzuodidian = token.find_next('li').get_text().strip()
                        elif re.search(u'职位类别', token.get_text().strip()):
                            self.zhiweileibie = token.find_next('li').get_text().strip()
                        elif re.search(u'招聘人数', token.get_text().strip()):
                            self.zhaopinrenshu = token.find_next('li').get_text().strip()
                        elif re.search(u'发布时间', token.get_text().strip()):
                            self.fabushijian = token.find_next('li').get_text().strip()



        if self.cRight:
            incLogo = self.cRight.find('div', 'cCompanyInfoConWrap').find('a').find('img').attrs['src']
            if incLogo and incLogo!='http://cimg.zhaopin.cn/img/logo/logo_l.jpg':
                self.result['jdInc']['incLogo'] = incLogo

            incLocation = self.cRight.find('div', 'cRightTab mt20')

            if re.search(u'公司地址', incLocation.find('h4').get_text()):
                for item in incLocation.find_all('p'):
                    if re.search(u'网址', item.get_text().strip()):
                        self.result['jdInc']['incUrl'] = item.find('a').get_text().strip()
                    else:
                        self.result['jdInc']['incLocation'] = item.get_text().strip()

            incTab = self.cRight.find('div', 'cLabelList')
            if incTab:
                self.result["jdInc"]["jobWelfare"] = u'|'.join([item.get_text().strip() for item in incTab.find_all('span')])


    def regular_jobinfo(self):

        find_jobName = self.headsoup.find('div', 'cLeft').find('div', 'cJobDetailInforWrap').find('h1',id='JobName')
        if find_jobName:
            self.jobName = find_jobName.get_text().strip()

        if self.fabushijian:
            self.jdJob[self.jobName]['pub_time'] = self.fabushijian
        if self.yuexin:
            self.jdJob[self.jobName]['jobSalary'] = self.yuexin
        if self.xueli:
            self.jdJob[self.jobName]['jobDiploma'] = self.xueli
        if self.gongzuodidian:
            self.jdJob[self.jobName]['jobWorkLoc'] = self.gongzuodidian
        if self.zhiweileibie:
            self.jdJob[self.jobName]['jobCate'] = self.zhiweileibie
        if self.zhaopinrenshu:
            self.jdJob[self.jobName]['jobNum'] = self.zhaopinrenshu


        if self.jdstr:
            pre_tags = self.jdstr.find_all("div","mt20")
            for item in pre_tags:
                key = item.find("h4").get_text().strip()
                values = item.find("p").find_all("span")
                if key.find(u"优先专业")!=-1:
                    for value in values:
                        self.majorList.append(value.get_text().strip())
                elif key.find(u"技能要求")!=-1:
                    for value in values:
                        self.skillList.append(value.get_text().strip())
            self.jdstr = self.jdstr.find("p","mt20").get_text().split("\n")
            self.intro = [item.strip() for item in self.jdstr if item.strip()]
            self.flag = None
            for idx, line in enumerate(self.intro):
                # print line+"Z"*50
                self.extra_info(line, idx, add_desc=True)

    def regular_contact(self):
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
            self.regular_contact()
        self.result["jdJob"] = self.jdJob

        return self.result


if __name__ == "__main__":
    import os, json

    test = XzParserZhilian()
    # path = xz_path + 'yjs/'
    # fnames = [path + fname for fname in os.listdir(path) if fname.endswith("42810.html")]
    tag = time.time()

    # for fname in fnames:
    #     print '==' * 20, fname
    #     htmlContent = codecs.open(fname, 'rb', 'utf-8').read()
    #     result = test.parser(htmlContent=htmlContent, fname=None, url=None)
        # print json.dumps(result, ensure_ascii=False, indent=4)
    # result = test.parser_xz(url="http://www.yjbys.com/mingqi/jobshow47689.html")

    result = test.parser_xz(url="http://xiaoyuan.zhaopin.com/job/102140")
    print json.dumps(result, ensure_ascii=False, indent=4)

    print "total time {0}".format(time.time()-tag)


