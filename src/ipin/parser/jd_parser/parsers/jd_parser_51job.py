#!/usr/bin/env python
# coding=utf-8
import sys,re,codecs,jieba
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from bs4 import BeautifulSoup
import urllib2
from urllib2 import urlopen
from utils.util import *
from utils.path import *
from collections import OrderedDict
from base import JdParserTop
import time
import codecs
import chardet
from socket import error as SocketError
import socket
from  requests.exceptions import ConnectionError
import errno

import requests
reload(sys)
sys.setdefaultencoding('utf-8')


def replace_space(line):
    regex = re.compile(u' +')
    line = re.sub(regex, u' ', line)
    return line

class JdParser51Job(JdParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """
    def __init__(self):
        JdParserTop.__init__(self)
    # @profile
    def preprocess(self,htmlContent=None,fname=None,url=None):
        '''

        Args:
            htmlContent: html文本
            fname: 文件名
            url: url链接

        Returns:

        '''

        self.refresh()
        self.result["jdFrom"] = "51job"

        if url!=None:
            #print "url"
            #urlopen有时候会出现104错误，原因未知，用requests来代替即可
            # html = urlopen(url).read()
            # html=unicode(html,'gb18030',errors='ignore')
            res = requests.get(url)
            res.encoding = 'gb18030'
            html = res.text

        elif htmlContent:
            #print "html"

            html = htmlContent
        elif fname:
            #print "file"
            html = codecs.open(fname,"rb",'gb18030').read()

        if len(html)<60:
            raise Exception("input arguments error")

        #换行符问题
        self.html= re.sub("<br.*?/?>|<BR.*?/?>|<br>|<li>","\n",html)
        #print self.html
        self.soup = BeautifulSoup(self.html,"lxml")
        self.find_new_comp =  self.soup.find("div","tHeader tHjob") # 判断是否为新版本
        if not self.find_new_comp:
            self.jdsoup = self.soup.find("div","tCompany_introduction")
            if not self.jdsoup:
                print "input arguments error"
                pass
            self.compsoup = self.soup.find("div","tBorderTop_box job_page_company")
            self.lineDl = self.jdsoup.find("div","tCompany_basic_job").find_all("dl","lineDl")# 为了方便取出表格基本信息
            self.jdstr = self.jdsoup.find("div","tCompany_text").get_text().strip()

        else:
            self.compsoup = self.find_new_comp.find("div","cn")
            self.jdsoup = self.soup.find("div","tCompany_main")
            self.basicsoup = self.jdsoup.find("div","jtag inbox")
            self.lineDl = self.basicsoup.find("div","t1").find_all("span","sp4")
            self.lineDl2 = self.basicsoup.find("div","t1").find_all("span","sp2")  # 语言要求，专业要求
            self.jdstr = self.basicsoup.find_next("div","bmsg job_msg inbox").get_text().strip()
        self.jdstr = self.CLEAN_TEXT.sub(" ",self.jdstr)
        self.linelist = [line.strip() for line in self.SPLIT_LINE.split(self.jdstr) if len(line.strip()) > 3]

    # @profile
    def regular_incname(self):
        incname=""
        if not self.find_new_comp and self.compsoup:
            incname = self.compsoup.find('h2').get_text()
        else:
            incname =  self.compsoup.find("p","cname").get_text()
        self.result['jdInc']['incName'] = incname.strip()

    # @profile
    def regular_inc_tag(self):

        if not self.compsoup:
            return
        if self.find_new_comp:
            if self.compsoup.find("p","msg ltype"):
                tags = self.compsoup.find("p","msg ltype").get_text(strip=True).split(u"|")
                if len(tags)==3:
                    self.result["jdInc"]["incType"] = tags[0].strip()
                    self.result["jdInc"]["incScale"] = tags[1].strip()
                    self.result["jdInc"]["incIndustry"] = tags[-1].strip()
                else:
                    for tag in tags:
                        if re.search(u"公司|国企|外资|合资|外企",tag):
                            self.result["jdInc"]["incType"] = tag.strip()
                        elif re.search(u"\d人",tag):
                            self.result["jdInc"]["incScale"] = tag.strip()
                        #if tags and  not re.search(u"人|公司|国企",tags[-1]):
                        if tags and  not re.search(u"\d人|公司|国企",tags[-1]):
                            self.result["jdInc"]["incIndustry"] = tags[-1].strip()


            find_inc_intro = self.compsoup.find_next("div","tmsg inbox")
            if find_inc_intro:
                #dengbinbin
                intro = find_inc_intro.get_text('\n').strip()
                #print intro
                self.result['jdInc']['incIntro'] = intro
                intro = find_inc_intro.get_text('\n').strip().split('\n')

                #新公司信息


                regex_contactInfo = re.compile(u'联络方式|联络电话|固定电话|固话|电话|联系电话|微信|QQ|联系方式|传真|Tel')
                regex_contactName = re.compile(u'联络|联系人$|联络人')
                regex_number = re.compile(u'(?<=[^-Q/——_ 0123456789])([-/_ ——0123456789]{7,})')
                regex_QQ = re.compile(u'QQ\d{6,}|QQ|qq')
                regex_punction = re.compile(u'[\],.;:，、。（）《》【】！#……()<>；“”'']')
                for line in intro:
                    if line:
                        line = re.sub(u':', u'：', line)
                        line = re.sub(u'：', u' ： ', line)

                        contactInfo = u''
                        contactName = u''

                        if re.search(u'联络方式|微信 ：|联络电话|联系电话 ：|电话 ：|联系方式 ：|传真 ：|Tel ：', line) \
                                or re.search(u'联系人 ：|联络 ：|人员 ：|联络人', line):

                            line = replace_space(line)
                            line = line.strip().split(u' ')
                            index = [index for (index, i) in enumerate(line) if i == u'：']
                            for i in range(len(index)):
                                # 只要不是最后一个冒号
                                if i != len(index) - 1:
                                    if re.search(regex_contactInfo, line[index[i] - 1]) or re.search(regex_QQ,
                                                                                                     line[index[i] - 1]):
                                        for j in range(index[i] - 1, index[i + 1] - 1):
                                            if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                                if len(re.findall(regex_punction, line[j])) > 0:
                                                    last_punction = re.findall(regex_punction, line[j])[-1]
                                                    line[j] = line[j].split(last_punction)[-1]

                                                    contactInfo += line[j] + u' '
                                            elif re.search(regex_QQ, line[j]):
                                                contactInfo += line[j] + u' '
                                            else:
                                                contactInfo += line[j] + u' '

                                    elif re.search(regex_contactName, line[index[i] - 1]):
                                        for j in range(index[i] + 1, index[i + 1] - 1):
                                            if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                                if len(re.findall(regex_punction, line[j])) > 0:
                                                    last_punction = re.findall(regex_punction, line[j])[-1]
                                                    line[j] = line[j].split(last_punction)[-1]

                                                    contactName += line[j] + u' '
                                            else:
                                                contactName += line[j] + u' '
                                # 是最后一个冒号
                                else:
                                    if re.search(regex_contactInfo, line[index[i] - 1]) or re.search(regex_QQ,
                                                                                                     line[index[i] - 1]):
                                        for j in range(index[i] - 1, len(line)):
                                            if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                                if len(re.findall(regex_punction, line[j])) > 0:
                                                    last_punction = re.findall(regex_punction, line[j])[-1]
                                                    line[j] = line[j].split(last_punction)[-1]
                                                    contactInfo += line[j] + u' '
                                            elif re.search(regex_QQ, line[j]):
                                                contactInfo += line[j] + u' '
                                            else:
                                                contactInfo += line[j] + u' '
                                    elif re.search(regex_contactName, line[index[i] - 1]):
                                        for j in range(index[i] + 1, len(line)):
                                            if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                                if len(re.findall(regex_punction, line[j])) > 0:
                                                    last_punction = re.findall(regex_punction, line[j])[-1]
                                                    line[j] = line[j].split(last_punction)[-1]

                                                    contactName += line[j] + u' '
                                            else:
                                                contactName += line[j] + u' '

                            if re.search(regex_number, contactName) or re.search(u'\d{11}', contactName):
                                # print "contactName have tel"
                                tel = ""
                                find_tel = re.findall(regex_number, contactName)

                                if find_tel == []:
                                    find_tel = re.findall(u'\d{11}', contactName)
                                for index in range(len(find_tel)):
                                    tel = find_tel[index] + u' '
                                    contactName = re.sub(find_tel[index], u'', contactName)
                                    contactInfo += tel + u' '
                            if re.search(regex_QQ, contactName):
                                # print "contactName have QQ"
                                QQ = ""
                                find_QQ = re.findall(regex_QQ, contactName)
                                for index in range(len(find_QQ)):
                                    QQ += find_QQ[index] + u' '
                                    contactName = re.sub(find_QQ[index], u'', contactName)
                                contactInfo += QQ + u' '
                            contactInfo = replace_space(contactInfo).strip()
                            contactName = re.sub(regex_punction, u'', contactName)
                            contactInfo = re.sub(u' ： ', u'：', contactInfo)
                            contactName = re.sub(u' ： ', u'：', contactName)
                            self.result['jdInc']['incContactInfo'] += contactInfo+u' '
                            self.result['jdInc']['incContactName'] += contactName +u' '
                            contactInfo = u''
                            contactName = u''
                            # print "ContactInfo:", self.result['jdInc']['incContactInfo']
                            # print "ContactName:", self.result['jdInc']["incContactName"]







                find_inc_url = self.compsoup.find("p","cname").find("a")
                if find_inc_url:
                    self.inc_url=self.compsoup.find("p","cname").find("a").get("href")


            find_inc_location = self.compsoup.find("span","lname")
            if find_inc_location:
                self.result["jdJob"]["jobWorkCity"] = find_inc_location.get_text().strip()


        #下面是没找到inc_intro时候的解决方法
        else:

            inc_tags = self.compsoup.find_all("dl","lineDl")
            for tag in inc_tags:
                key = tag.find('dt').get_text()
                if re.search(u"行业",key):
                    self.result["jdInc"]["incIndustry"] = tag.find("dd").get_text().strip()
                elif re.search(u"性质",key):
                    self.result["jdInc"]["incType"]=tag.find("dd").get_text().strip()
                elif re.search(u"规模",key):
                    self.result["jdInc"]["incScale"] = tag.find("dd").get_text().strip()
                elif re.search(u"地址",key):

                    self.result["jdJob"]["jobWorkCity"] = tag.find("p",{"class":"job_company_text"}).get_text().strip()

                elif re.search(u"公司网站",key):
                    self.result["jdInc"]["incUrl"] = tag.find("dd").get_text().strip()
            if re.search(u"公司介绍",self.html) and self.soup.find("div","tCompany_text_gsjs"):
                self.result["jdInc"]["incIntro"] = self.soup.find("div","tCompany_text_gsjs").get_text('\n').strip().strip()

                incUrl = self.INC_URL.search(self.result["jdInc"]["incIntro"])
                if not self.result["jdInc"]["incUrl"] and incUrl:
                    self.result["jdInc"]["incUrl"] = re.search("[\w\d\./_:\-]+",incUrl.group()).group()
        #51job公司主页解析
        if self.inc_url:


            try:
                #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
                #html = opener.open(self.inc_url).read().decode('gb18030')
                res = requests.get(self.inc_url)
                res.encoding = 'gb18030'
                html = res.text

            except SocketError as e:
                # if e.errno != errno.ECONNRESET:
                #    raise
                print e
            except ConnectionError as err:
                print err
            else:
                soup = BeautifulSoup(html, "lxml")
                rows = soup.find("div", {"class": "tCompany_full"}).find_all("span", {"class": "label"})
                find_inc_aliasName = soup.find("p", "tPosition_center_bottomText")
                if find_inc_aliasName:
                    incAliasName = soup.find("p", "tPosition_center_bottomText").get_text().strip().split('：')[1] if \
                        soup.find("p", "tPosition_center_bottomText").get_text().strip() else ""
                else:
                    incAliasName = ""
                self.result['jdInc']['incAliasName'] = incAliasName
                for row in rows:
                    if re.search(u"公司地址", row.get_text()):
                        #add incZipcode
                        info = row.parent.get_text()
                        if re.search(u"邮编：(\d{6})", info):
                            self.result["jdInc"]["incZipCode"] = re.search(u"邮编：(\d{6})",info).group(1)
                        self.result['jdInc']["incLocation"] = re.sub(u"\s+|\(邮编：\d{6}\)", u'', row.parent.get_text())[
                                                              5:]

                    elif re.search(u"公司官网", row.get_text()):

                        self.result['jdInc']['incUrl'] = re.sub(u"\s+", u'', row.parent.get_text())[5:]

    # @profile
    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """

        pubTime =""
        if not self.find_new_comp:
            pubTime = self.jdsoup.find("div","tCompany_basic_job").dd.get_text().strip()
        self.result["pubTime"] = pubTime

    # @profile
    def regular_jobname(self):
        jobname = u""
        if self.find_new_comp:
            jobname = self.compsoup.find("h1").get_text().strip()
            find_job_type = re.search(u"实习|兼职|全职",jobname)
            if find_job_type:
                self.result["jdJob"]["jobType"] = find_job_type.group()
        else:
            jobname = self.jdsoup.find("li","tCompany_job_name").find('h1').get_text()

        self.result["jdJob"]["jobPosition"] = re.sub("\s+","",jobname.strip())

    # @profile
    def regular_job_tag(self):

        intro=self.job_desc_process(self.jdstr)
        self.result['jdJob']['jobDesc'] = intro
        # intro = intro.split('\n')
        # intro = [x for x in intro if x != '' and x != u''and x!=u' ']
        #
        # for item in intro[:-1]:
        #     self.result["jdJob"]["jobDesc"] += item + '\t'
        # self.result["jdJob"]["jobDesc"] += intro[-1]

        if self.find_new_comp:
            intro = self.job_desc_process(self.jdstr).split('\n')
            # 新职位信息
            regex_contactInfo = re.compile(u'联络方式|联络电话|固定电话|固话|电话|联系电话|微信|QQ|联系方式|传真|Tel')
            regex_contactName = re.compile(u'联络|联系人$|联络人')
            regex_number = re.compile(u'(?<=[^-Q/——_ 0123456789])([-/_ ——0123456789]{7,})')
            regex_QQ = re.compile(u'QQ\d{6,}|QQ|qq')
            regex_punction = re.compile(u'[\],.;:，、。（）《》【】！#……()<>；“”'']')
            for line in intro:
                if line:
                    line = re.sub(u':', u'：', line)
                    line = re.sub(u'：', u' ： ', line)

                    contactInfo = u''
                    contactName = u''

                    if re.search(u'联络方式|微信 ：|联络电话|联系电话 ：|电话 ：|联系方式 ：|传真 ：|Tel ：', line) \
                            or re.search(u'联系人 ：|联络 ：|人员 ：|联络人', line):

                        line = replace_space(line)
                        line = line.strip().split(u' ')
                        index = [index for (index, i) in enumerate(line) if i == u'：']
                        for i in range(len(index)):
                            # 只要不是最后一个冒号
                            if i != len(index) - 1:
                                if re.search(regex_contactInfo, line[index[i] - 1])or re.search(regex_QQ, line[index[i] - 1]) :
                                    for j in range(index[i] - 1, index[i + 1] - 1):
                                        if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                            if len(re.findall(regex_punction, line[j]))>0:
                                                last_punction = re.findall(regex_punction, line[j])[-1]
                                                line[j] = line[j].split(last_punction)[-1]

                                                contactInfo += line[j] + u' '
                                        elif re.search(regex_QQ,line[j]):
                                            contactInfo+=line[j]+u' '
                                        else:
                                            contactInfo += line[j] + u' '

                                elif re.search(regex_contactName, line[index[i] - 1]):
                                    for j in range(index[i]+1, index[i + 1] - 1):
                                        if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                            if len(re.findall(regex_punction, line[j])) > 0:
                                                last_punction = re.findall(regex_punction, line[j])[-1]
                                                line[j] = line[j].split(last_punction)[-1]

                                                contactName += line[j] + u' '
                                        else:
                                            contactName += line[j] + u' '
                            # 是最后一个冒号
                            else:
                                if re.search(regex_contactInfo, line[index[i] - 1]) or re.search(regex_QQ, line[index[i] - 1]) :
                                    for j in range(index[i] - 1, len(line)):
                                        if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                            if len(re.findall(regex_punction, line[j])) > 0:
                                                last_punction = re.findall(regex_punction, line[j])[-1]
                                                line[j] = line[j].split(last_punction)[-1]
                                                contactInfo += line[j] + u' '
                                        elif re.search(regex_QQ, line[j]):
                                            contactInfo += line[j] + u' '
                                        else:
                                            contactInfo += line[j] + u' '
                                elif re.search(regex_contactName, line[index[i] - 1]):
                                    for j in range(index[i]+1 , len(line)):
                                        if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                            if len(re.findall(regex_punction, line[j])) > 0:
                                                last_punction = re.findall(regex_punction, line[j])[-1]
                                                line[j] = line[j].split(last_punction)[-1]

                                                contactName += line[j] + u' '
                                        else:
                                            contactName += line[j] + u' '

                        if re.search(regex_number, contactName)or re.search(u'\d{11}',contactName):
                            #print "contactName have tel"
                            tel = ""
                            find_tel = re.findall(regex_number, contactName)

                            if find_tel==[]:
                                find_tel = re.findall(u'\d{11}', contactName)
                            for index in range(len(find_tel)):
                                tel = find_tel[index] + u' '
                                contactName = re.sub(find_tel[index], u'', contactName)
                                contactInfo += tel + u' '
                        if re.search(regex_QQ, contactName):
                            #print "contactName have QQ"
                            QQ = ""
                            find_QQ = re.findall(regex_QQ, contactName)
                            for index in range(len(find_QQ)):
                                QQ += find_QQ[index] + u' '
                                contactName = re.sub(find_QQ[index], u'', contactName)
                            contactInfo += QQ + u' '
                        contactInfo = replace_space(contactInfo).strip()
                        contactName = re.sub(regex_punction, u'', contactName)
                        contactInfo = re.sub(u' ： ', u'：', contactInfo)
                        contactName = re.sub(u' ： ', u'：', contactName)
                        self.result['jdInc']['incContactInfo'] += contactInfo
                        self.result['jdInc']['incContactName'] += contactName
                        contactInfo = u''
                        contactName = u''
			
                        # print "ContactInfo:", self.result['jdInc']['incContactInfo']
                        # print "ContactName:", self.result['jdInc']["incContactName"]

	
            for line in self.lineDl:
                if re.search(u"经验",line.get_text()):
                    self.result["jdJob"]["jobWorkAge"] = line.get_text().strip()
                elif self.DEGREE.search(line.get_text()):
                    self.result["jdJob"]["jobDiploma"] = line.get_text().strip()
                elif re.search(u"招聘|人",line.get_text()):
                    self.result["jdJob"]["jobNum"] = line.get_text()
                elif re.search(u"发布",line.get_text()):
                    self.result["pubTime"] = line.get_text().strip()

            find_job_cate = self.basicsoup.find_next("div","bmsg job_msg inbox").find("span","label",text=re.compile(u"职能类别"))
            if find_job_cate:
                tags = [tag.get_text() for tag in find_job_cate.find_next_siblings("span")]
                self.result["jdJob"]["jobCate"] = ' | '.join(tags)

        else:

            for line in self.lineDl:
                for tag in line.find_all("dt"):
                    if re.search(u"招聘人数",tag.get_text()):
                        self.result["jdJob"]["jobNum"] = tag.findNext("dd").get_text().strip()

            for line in self.lineDl:
                if re.search(u"职能类别",line.dt.get_text()):
                    self.result["jdJob"]["jobCate"] =  " | ".join(line.dd.get_text().split())
                if re.search(u"职位标签",line.dt.get_text()):
                    if re.search(u"实习|兼职",line.dd.get_text()):
                        self.result["jdJob"]["jobType"] = u"实习"
                    elif re.search(u"全职",line.dd.get_text()):
                        self.result["jdJob"]["jobType"] = u"全职"
	#self.result['jdInc']['incContactInfo'] = self.result['jdInc']['incContactInfo'].strip()
	#self.result['jdInc']['incContactName'] = self.result['jdInc']['incContactName'].strip()

    # @profile
    def regular_sex(self):
        """
        不限
        男
        女
        """
        res = u"不限"
        for line in self.linelist:
                if re.search(u"性别不限|男女不限",line):
                    res = u"不限"
                elif re.search(u"男",line):
                    res = u"男"
                elif re.search(u"女",line):
                    res = u"女"
                break

        self.result['jdJob']["gender"] = str(res)

    # @profile
    def regular_age(self):
        """
        (minage,maxage)
        """
        agestr = u"不限"
        for line in self.linelist:
            if re.search(u"\d+后",line):continue
            if self.AGE.search(line):
                findage = re.search(u"\d{2}?\s?[\-－　到至\s]?\d{2}周?岁|(至少|不低于|不超过|不大于|大概|大约|不少于|大于)\d+周?岁|\d+周岁(以上|左右|以下)|年龄.{2,9}",line)
                if findage:
                    agestr = findage.group()
        self.result["jdJob"]["age"] = agestr

    # @profile
    def regular_major(self):
        res = []
        if self.find_new_comp:
            for line in self.lineDl2:
                if line.find("em","i6"):
                    res = line.get_text().strip().split()

        self.result['jdJob']["jobMajorList"] = res

    # @profile
    def regular_major_detail(self):
        res = []
        if self.find_new_comp:
            for line in self.lineDl2:
                if line.find("em","i6"):
                    res = line.get_text().strip().split()
        if not res:
            for line in self.linelist:
                for word in jieba.cut(line):
                    word = word.strip().lower()
                    if word in self.majordic:
                        res.append(word)

        self.result["jdJob"]["jobMajorList"] = list(set(res))

    # @profile
    def regular_degree(self):
        res = ""
        if not self.find_new_comp:
            line = self.lineDl[1]
            for tag in line.find_all("dt"):
                if re.search(u"学历要求",tag.get_text()):
                    res = tag.findNext("dd").get_text()
                    self.result['jdJob']['jobDiploma'] = res
                    break

    # @profile
    def regular_language(self):


        #根据网页icon获取语言信息
        if self.find_new_comp:
            for line in self.lineDl2:
                if line.em.get("class")[0]==u"i5":
                    self.result['others']["language"] = line.get_text()
                    return
        if self.find_new_comp:
            for line in self.lineDl2:
                if re.search(u"好|语言",line.get_text()):
                    res = line.get_text().strip()
                    self.result['others']["language"] = res
                    break

    # @profile
    def regular_exp(self):
        expstr =""
        if not self.find_new_comp:
            for line in self.lineDl:
                if re.search(u"工作年限",line.dt.get_text()):
                    expstr = line.dd.get_text().strip()
                    self.result['jdJob']["jobWorkAge"] = expstr
                    break

    # @profile
    def regular_skill(self):
        res = {}
        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.lower()
                if word in self.skilldic:
                    res.setdefault(word,1)
                    res[word] += 1

        sorted_res = sorted(res.items(),key = lambda d:d[1],reverse=True)

        res =[w[0] for w in sorted_res[:5] ]
        self.result["jdJob"]["skillList"] = res

    # @profile
    def regular_workplace(self):
        res = ""
        resultList = []
        if self.find_new_comp:
            find_workplace = self.jdsoup.find("span","label",text=re.compile(u"上班地址："))

            if find_workplace:
                res = find_workplace.find_previous("p","fp").get_text().strip()
                res = res[res.find(u"：")+1:]   # 去掉上班地址这几个字

        else: # 旧版本

            for line in self.lineDl:
                for tag in line.find_all("dt"):
                    if re.search(u"工作地点",tag.get_text()):
                        res = tag.findNext("dd").get_text()
                        break

        self.result['jdJob']['jobWorkLoc'] = res

        for word in jieba.cut(self.result['jdInc']['incLocation']):
            word = word.strip().lower()
            if word in self.citydic:
                resultList.append(word)
        #resultList[0]是所有提取出来的行政区划中最高级别的，如果这个级别至少是市级的
        if resultList and resultList[0] in self.province_city:
            if (len(resultList) >= 2):
                length = len(resultList)
                res = ""
                res = resultList[0]
                for each in resultList[1:]:
                    res +='-'+each

                if(resultList[0][:-1]==resultList[1]):
                    resultList[1] ='-'+resultList[1]
                    self.result['jdInc']['incCity'] = re.sub(resultList[1],'',res)
                else:
                    self.result['jdInc']['incCity'] = res
            elif (len(resultList)==1):
                self.result['jdInc']['incCity'] = resultList[0]
            else:
                self.result['jdInc']['incCity'] = ""
        #当resultList[0]所提取出来的信息不是省市级的时候，需要采用其他方法来考虑提取城市信息
        #1、按照单词字符的匹配率大于百分之80来判断
        # else:
        #     number = re.compile(u'\w{1,}')
        #     infoincLocation = re.findall(number,self.result['jdInc']['incLocation'])
        #     infojobWorkLoc = re.findall(number,self.result['jdJob']['jobWorkLoc'])
        #     correct = 0
        #     total = 0
        #     for word in infoincLocation:
        #         if word in infojobWorkLoc:
        #             correct+=1
        #         total+=1
        #     rate = 1.0*correct/total
        #     if(rate>=0.80):
        #         self.result['jdInc']['incCity'] = self.result['jdJob']['jobWorkCity']
        #     else:
        #         self.result['jdInc']['incCity'] = ""
        #2、按照jieba分词之后的结果进行匹配
        else:
            infoincLocation = jieba.cut(self.result['jdInc']['incLocation'])
            infojobWorkLoc = jieba.cut(self.result['jdJob']['jobWorkLoc'])
            incLocationList = []
            jobLocationList = []
            for word in infojobWorkLoc:
                incLocationList.append(word)
            for word in infoincLocation:
                jobLocationList.append(word)
            correct = 0
            total = 0
            for word in incLocationList:
                if word in jobLocationList:
                    correct+=1
                total+=1
            if total != 0:
                ratio = 1.0 * correct / total
            else:
                ratio = 0
            if(ratio>=0.60):
                self.result['jdInc']['incCity'] = self.result['jdJob']['jobWorkCity']
            else:
                self.result['jdInc']['incCity'] = ""
            for word in jobLocationList:
                if word in incLocationList:
                    correct += 1
                total += 1
            if total!=0:
                ratio = 1.0 * correct / total
            else:
                ratio = 0.0
            if (ratio >= 0.60):
                self.result['jdInc']['incCity'] = self.result['jdJob']['jobWorkCity']
            else:
                self.result['jdInc']['incCity'] = ""

    # @profile
    def regular_pay(self):
        """
        薪酬工资
        """
        paystr = ""
        if self.find_new_comp: #新版本
            find_pay = self.compsoup.find("p","cname").find_previous("strong")
            if find_pay:
                paystr = find_pay.get_text().strip()

        else:
            for line in self.lineDl:
                for tag in line.find_all("dt"):
                    if re.search(u"薪资范围",tag.get_text()):
                        paystr = tag.findNext("dd").get_text()
                        break
        self.result['jdJob']["jobSalary"] = paystr

    # @profile
    def regular_cert(self):
        """
        证书要求
        """
        res = []
        for line in self.linelist:
            findcert = self.CERT.search(line)
            if findcert and not re.search(u"保证",findcert.group()):
                res.append(findcert.group())
            else:
                findcert = re.search(u"有(.+资格证)",line)
                if findcert and not re.search(u"保证",findcert.group()):
                    res.append(findcert.group(1))
        res = re.sub(u"[通过或以上至少]","","|".join(res))
        self.result_job['certList'] = res.split("|")

    # @profile
    def regular_demand(self):
        """
        岗位要求
        """

        jdstr = self.jdstr
        res,linelist = [],[]
        pos = list(self.START_DEMAND.finditer(jdstr))
        if pos:
            linelist = [line.strip() for line in self.SPLIT_LINE.split(jdstr[pos[-1].span()[1]:]) if line.strip()>3]

        linelist = filter(lambda x:len(x)>2,linelist)

        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DEMAND.search(line):
                continue
            if self.START_DUTY.search(line):
                break
            if re.match(u"\d[\.、\s　]|[\(（【][a-z\d][\.、\s　]|[\u25cf\uff0d\u2022]",line) or self.DEMAND.search(line) or self.clf.predict(line)=="demand":
                res.append(self.CLEAN_LINE.sub("",line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=="demand":
                res.append(self.CLEAN_LINE.sub("",line))
            else:
                break
        if not res:
            for line in self.linelist:
                if self.clf.predict(line) == "demand":
                    res.append(self.CLEAN_LINE.sub("",line))

        res = [str(i+1)+". "+line for i,line in enumerate(res)]
        self.result["workDemand"] = '\n'.join(res)

    # @profile
    def regular_duty(self):
        """
        岗位职责
        """
        jdstr = self.jdstr
        res,linelist = [],[]
        pos = list(self.START_DUTY.finditer(jdstr))
        if pos:
            linelist = [line.strip() for line in self.SPLIT_LINE.split(jdstr[pos[-1].span()[1]:]) if line.strip()>3]

        linelist = filter(lambda x:len(x)>2,linelist)
        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DUTY.search(line):
                continue
            if self.START_DEMAND.search(line):
                break

            if re.match(u"\d[\.、\s　]|[\(（【][a-z\d][\.、\s　]|[\u25cf\uff0d]",line) or self.DUTY.search(line) or self.clf.predict(line)=="duty":
                res.append(self.CLEAN_LINE.sub("",line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=="duty":
                res.append(self.CLEAN_LINE.sub("",line))
            else:
                break
        if not res:
            for line in self.linelist:
                if self.clf.predict(line) == "duty":
                    res.append(self.CLEAN_LINE.sub("",line))
        res = [str(i+1)+". "+line for i,line in enumerate(res)]
        self.result["workDuty"] = '\n'.join(res)

    # @profile
    def regular_benefit(self):
        """
        福利制度
        """

        res = []

        if self.find_new_comp:
            find_benefit = self.basicsoup.find("div","t2")
            if not find_benefit:
                find_benefit = self.basicsoup.find("p","t2")
            if find_benefit:
                for tag in find_benefit.find_all("span"):
                    res.append(tag.get_text().strip())
        else:
            for line in self.lineDl:
                if re.search(u"薪酬福利",line.find("dt").get_text()):
                    res.append(line.find("dd").get_text().strip())

        self.result['jdJob']["jobWelfare"] = '\n'.join(set(list(res)))

    # @profile
    def regular_other(self):
        """
        关键词，具体上班地址等信息
        """

        if self.find_new_comp:
            find_key_words = self.basicsoup.find_next("div","bmsg job_msg inbox").find("span","label",text=re.compile(u"关键字"))
            if find_key_words:
                tags = [tag.get_text() for tag in find_key_words.find_next_siblings("span") ]
                tags = [item for item in tags if item!=u'']
                self.result['others']["keyWords"] = ' | '.join(tags)

                #如果没有jobType，从keywords中判断
                if not self.result['jdJob']['jobType']:
                    find_job_type = re.search(u"实习|兼职|全职", self.result['others']["keyWords"])
                    if find_job_type:
                        self.result["jdJob"]["jobType"] = find_job_type.group()

        #邮编
        if re.search(u"邮编：(\d{6})",self.result["jdInc"]["incLocation"]):
            #print self.result["jdInc"]["incLocation"]
            self.result["jdInc"]["incZipCode"]=re.search(u"邮编：(\d{6})",self.result["jdInc"]["incLocation"]).group(1)
            self.result['jdInc']['incLocation']=re.sub(u"\(邮编：\d{6}\)",'',self.result['jdInc']['incLocation'])
            # find_workp_detail = self.basicsoup.find_next("span","label",text=re.compile(u"上班地址"))
            # if find_workp_detail:
            #     res["workPlaceDetail"] = re.sub("\s","",find_workp_detail.find_parent("p").get_text())[5:]
        #公司邮箱
        if self.MAIL.search(self.result["jdInc"]["incIntro"]):
            self.result['jdJob']["email"]=self.MAIL.search(self.result["jdInc"]["incIntro"]).group()
        elif self.MAIL.search(self.result["jdJob"]["jobDesc"]):
            self.result['jdJob']["email"] = self.MAIL.search(self.result["jdJob"]["jobDesc"]).group()

        #如果前面没有找到incUrl，那么在此处再去判断一下incIntro和jobDesc里面是否有公司网址
        if not self.result['jdInc']['incUrl']:
            intro = self.result['jdInc']['incIntro'].split('\n')
            for line in intro:
                # print '*'*50
                # if re.search(u'公司官网：网址：|网站：|主页：',line):
                #     self.result['jdInc']['incUrl'] = line[line.find(u'：') + 1:]
                #     return

                if re.search(u'公司官网：|网址：|网站：|主页：', line):
                    url = re.compile(
                        u'(http:.*?\.cn|http:.*?\.com|http:.*?\.org|www.*?\.com|www.*?\.cn|http:.*?\.html|http:.*?\.shtml)')
                    if re.search(url, line):
                        if len(re.findall(url, line)) >= 1:
                            for item in re.findall(url, line):
                                self.result['jdInc']['incUrl'] += item + u' '
                            break
                if not self.result['jdInc']['incUrl']:
                    self.result['jdInc']['incUrl'] = ""


                    intro = self.result['jdJob']['jobDesc'].split('\n')
                    for line in intro:
                        if re.search(u'公司官网：网址：|网站：|主页：', line):
                            url = re.compile(u'(http:.*?\.cn|http:.*?\.com|http:.*?\.org|www.*?\.com|www.*?\.cn|http:.*?\.html|http:.*?\.shtml)')
                            if re.search(url,line):
                                if len(re.findall(url,line))>=1:
                                    for item in re.findall(url,line):
                                        self.result['jdInc']['incUrl'] += item + u' '
                                    return
                    #self.result['jdInc']['incUrl'] = line[line.find(u'网址：|网站：|主页：') + 1:]
                    # for char in self.result['jdInc']['incUrl']:
                    #     print char
                # if not self.result['jdInc']['incUrl']:
                #     self.result['jdInc']['incUrl'] = ""
                # else:
                #     return

    # @profile
    #职位信息的格式处理  zhangzq 20160308
    def job_desc_process(self,src_str):
        src_str = re.sub(u'\n',u'`',src_str)
        src_str = re.sub(u'职能类别：.*|关键字:.*|举报`分享',u'',src_str)
        src_str = re.sub(u'\s+',u' ',src_str)
        return re.sub(u'`',u'\n',src_str)

    # @profile
    #公司地址与工作地址交换   zhangzq 20160309
    def location_exchange(self):
        self.result_inc["incworkdetail"],self.result_job["jobWorkLoc"] = self.result_job["jobWorkLoc"],self.result_inc["incworkdetail"]

    # @profile
    def parser_basic(self,htmlContent="",fname=None,url=None):
        """
        基本解析，简单抽取信息
        """
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_pay()
        self.regular_degree()
        self.regular_major()
        self.regular_exp()
        self.regular_language()
        self.regular_workplace()
        self.regular_benefit()
        self.regular_other()

        return self.result

    # @profile
    def parser_detail(self,htmlContent="",fname=None,url=None):
        """
        进一步简单语义解析
        """
        self.preprocess(htmlContent,fname,url)
        self.regular_exp()
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_pay()
        self.regular_degree()
        #self.regular_demand()
        self.regular_sex()
        self.regular_age()
        self.regular_major_detail()
        # self.regular_skill()
        # self.regular_cert()

        self.regular_exp()
        self.regular_language()
        self.regular_workplace()
        self.regular_benefit()
        self.regular_other()




        return self.result


    def ouput(self):
        for k,v in self.result.iteritems():
            print k
            if isinstance(v,list):
                print '['+','.join(v)+']'
            else:
                print v
            print "-"*20



if __name__ == "__main__":
    import os,json
    test = JdParser51Job()

    path = jd_path+'jd_51job/'
    #path = 'test_jds/wrong_answer/'
    fnames = [ path+file for file in os.listdir(path) if file.endswith("html")]
    starttime = time.time()
    count = 0
    for fname in fnames:

        print "=="*20,fname
        #print chardet.detect('test_jds/test/51job.html')
        htmlContent = codecs.open(fname,'r','utf-8').read()
        #print "simple"
        #result1 = test.parser_basic(htmlContent,fname=None,url=None)
        #print json.dumps(result1,ensure_ascii=False,indent=4)
        #print 'detail'
        result2 = test.parser_detail(htmlContent,fname=None,url=None)
        #print "incZipCode:",result2['jdJob']['jobType']
        #print "ContactName:",result2['jdInc']["incContactName"]
        #if len(result2['jdInc']['incUrl'])>60:
        # print json.dumps(result2,ensure_ascii=False,indent=4)
        #生成有标签或者无标签的数据，用作CNN的数据集
        generate_text_withlabel(result2, jdfrom="51job",file_path = path,count = count)
        #generate_text_withoutlabel(result2, jdfrom="51job", file_path=path, count=count)
        count+=1
        print "the total jd parsed are:%d" % (count)
    endtime = time.time()
    print "total time is: %f" % (endtime - starttime)
    print "average time is %f" %((endtime - starttime)/count)
    # result2 = test.parser_detail(fname=None,url="http://jobs.51job.com/shenzhen-ftq/74324473.html?s=0")
    # #print json.dumps(result2,ensure_ascii=False,indent=4)
