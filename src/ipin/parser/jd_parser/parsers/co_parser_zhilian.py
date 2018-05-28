#!/usr/bin/env python
# coding=utf-8

import sys, re, codecs, jieba
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from bs4 import BeautifulSoup
import urllib2
import urllib
from urllib2 import urlopen
from utils.util import *
from utils.path import *
from collections import OrderedDict
from base import JdParserTop,CoParserTop
import time
import codecs
import numpy as np
import chardet
from socket import error as SocketError
import errno
import pickle
import requests

reload(sys)
sys.setdefaultencoding('utf-8')


def replace_space(line):
    regex = re.compile(u' +')
    line = re.sub(regex, u' ', line)
    return line


class CoParserZhilian(CoParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """

    def __init__(self):
        CoParserTop.__init__(self)
        self.zhilian_dir = co_path + 'img_zhilian/'
    def preprocess(self, htmlContent=None, fname=None, url=None):
        '''

        Args:
            htmlContent: html文本
            fname: 文件名
            url: url链接

        Returns:

        '''

        self.refresh()
        if url != None:
            # print "url"
            # urlopen有时候会出现104错误，原因未知，用requests来代替即可
            html = urlopen(url).read()
            html=unicode(html,'utf-8',errors='ignore')
            # res = requests.get(url)
            # res.encoding = 'utf-8'
            # html = res.text

        elif htmlContent:
            # print "html"

            html = htmlContent
        elif fname:
            # print "file"
            html = codecs.open(fname, "rb", 'gb18030').read()

        if len(html) < 60:
            raise Exception("input arguments error")



        # 换行符问题
        self.html = re.sub("<br.*?/?>|<BR.*?/?>|<br>|<li>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml",from_encoding="utf-8")


        self.basicsoup = self.soup.find("div","main")
        self.compsoup = self.basicsoup.find("table","comTinyDes")
        self.incstr = self.basicsoup.find("div","company-content")
        self.logosoup = self.basicsoup.find("img", "companyLogo")

        try:
            incName = ""
            incName = self.basicsoup.find("h1").get_text()

            self.result['coInc']['incName'] = incName.strip()
        except:
            # print ("the company is not exists")
            raise ("the company is not exists")

        # if not os.path.exists(self.zhilian_dir):
        #     os.makedirs(self.zhilian_dir)

    #incName
    def regular_incname(self):

        incName = ""
        incName = self.basicsoup.find("h1").get_text()


        self.result['coInc']['incName'] = incName.strip()

    # incType、incScale、incIndustry、incLocation、incIntro
    def regular_inc_tag(self):

        inc_tags = self.compsoup.find_all("tr") if self.compsoup else []
        for tag in inc_tags:

            key = tag.find("span").get_text()
            if re.search(u"规模", key):
                self.result["coInc"]["incScale"] = [word.get_text() for word in tag.find_all("span")][1]
            elif re.search(u"性质", key):
                self.result["coInc"]["incType"] = [word.get_text() for word in tag.find_all("span")][1]
            elif re.search(u"行业", key):
                self.result["coInc"]["incIndustry"] = [word.get_text() for word in tag.find_all("span")][1]
            elif re.search(u"主页|网站", key):
                self.result["coInc"]["incUrl"] = [word.get_text() for word in tag.find_all("span")][1]
            elif re.search(u"地址", key):
                self.result["coInc"]["incLocation"] = [word.get_text() for word in tag.find_all("span")][1]

        if self.result['coInc']['incUrl']==u'http://null':
            self.result['coInc']['incUrl'] = u''

        if self.incstr:
            intro = self.incstr.find_all("p")
            if len(intro)==0:
                intro =  self.incstr.get_text().strip()
            else:
                intro =  [line.get_text() for line in intro if line.get_text().strip()]
                intro = '\n'.join(intro)
            self.result['coInc']['incIntro'] = intro


    #incCity
    def regular_incplace(self):
        incplace = ""
        incZipCode = ""
        resultList = []

        # find_incplace = self.jdstr.find("span", "label", text=re.compile(u"公司地址："))
        # if find_incplace:
        #     incplace = find_incplace.find_previous("p", "fp").get_text().strip()
        #     incZipCode = re.search(self.ZIP,incplace)
        #     incplace = incplace[incplace.find(u"：") + 1:incplace.find('(')].strip()  # 去掉公司地址这几个字和后面的右边
        #
        #
        #     self.result['coInc']['incLocation'] = incplace
        #     self.result['coInc']['incZipCode'] = incZipCode.group(0)


        for word in jieba.cut(self.result['coInc']['incLocation']):
            word = word.strip().lower()
            if word in self.city_area:
                resultList.append(word)

        # resultList[0]是所有提取出来的行政区划中最高级别的，如果这个级别至少是市级的
        if resultList and resultList[0] in self.city_area:
            if (len(resultList) >= 2):
                length = len(resultList)
                res = resultList[0]
                res += '-' + resultList[1]

                if (resultList[0][:-1] == resultList[1]):
                    resultList[1] = '-' + resultList[1]
                    self.result['coInc']['incCity'] = re.sub(resultList[1], '', res)
                else:
                    self.result['coInc']['incCity'] = res
            elif (len(resultList) == 1):
                self.result['coInc']['incCity'] = resultList[0]
            else:
                self.result['coInc']['incCity'] = ""


    #incContactEmail、incUrl、incContactPhone、incContactName
    def regular_contactInfo(self):
        intro = [line.strip() for line in self.result["coInc"]["incIntro"].split('\n') if line.strip()]

        if self.MAIL.findall(self.result["coInc"]["incIntro"]):
            self.result['coInc']["incContactEmail"] += " ".join(self.MAIL.findall(self.result["coInc"]["incIntro"]))
        if not self.result['coInc']['incUrl']:
            incUrl = self.INC_URL.search(self.result["coInc"]["incIntro"])
            if not self.result["coInc"]["incUrl"] and incUrl:
                  self.result["coInc"]["incUrl"] = re.search("[\w\d\./_:\-]+", incUrl.group()).group()

        regex_contactPhone = re.compile(u'联络方式|联络电话|固定电话|手机|固话|电话|联系电话|微信|QQ|联系方式|传真|Tel')
        regex_contactName = re.compile(u'联络|联系人$|联络人')
        regex_number = re.compile(u'(?<=[^-Q/——_ 0123456789])([-/_ ——0123456789]{7,})')
        regex_QQ = re.compile(u'QQ\d{6,}|QQ|qq')
        regex_punction = re.compile(u'[\],.;:，、。（）《》【】！#……()<>；“”'']')
        #公司联系信息
        for line in intro:

            line = re.sub(u':', u'：', line)
            line = re.sub(u'：', u' ： ', line)
            contactPhone = u''
            contactName = u''

            line = replace_space(line.replace(u'\xa0',u' '))
            if re.search(u'联络方式|微信 ：|手 机 ：|联络电话|联系电话 ：|电话 ：|电 话 ：|联系方式 ：|传真 ：|Tel ：', line) \
                    or re.search(u'联系人 ：|联络 ：|人员 ：|联络人', line):
                line = line.strip().replace(u'电 话',u'电话').replace(u'手 机',u'手机').split(u' ')
                index = [index for (index, i) in enumerate(line) if i == u'：']

                for i in range(len(index)):
                    # 只要不是最后一个冒号
                    if i != len(index) - 1:
                        if re.search(regex_contactPhone, line[index[i] - 1]):
                            for j in range(index[i] - 1, index[i + 1] - 1):
                                if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                    if len(re.findall(regex_punction, line[j])) > 0:
                                        last_punction = re.findall(regex_punction, line[j])[-1]
                                        line[j] = line[j].split(last_punction)[-1]

                                        contactPhone += line[j] + u' '

                                else:
                                    contactPhone += line[j] + u' '

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
                        #冒号前面一个词找到了联系电话之类的字眼
                        if re.search(regex_contactPhone, line[index[i] - 1]):
                            if index[i]+1>=len(line):
                                contactPhone = ""
                            else:
                                contactPhone += line[index[i]+1] + u' '

                        elif re.search(regex_contactName, line[index[i] - 1]):
                            for j in range(index[i] + 1, len(line)):
                                if len(line[j]) > 40 and not re.search(regex_number, line[j]):
                                    if len(re.findall(regex_punction, line[j])) > 0:
                                        last_punction = re.findall(regex_punction, line[j])[-1]
                                        line[j] = line[j].split(last_punction)[-1]

                                        contactName += line[j] + u' '
                                else:
                                    contactName += line[j] + u' '

                    # print contactName,contactPhone
                if re.search(regex_number, contactName) or re.search(u'\d{11}', contactName):
                    # print "contactName have tel"
                    tel = ""
                    find_tel = re.findall(regex_number, contactName)

                    if find_tel == []:
                        find_tel = re.findall(u'\d{11}', contactName)
                    for index in range(len(find_tel)):
                        tel = find_tel[index] + u' '
                        contactName = re.sub(find_tel[index], u'', contactName)
                        contactPhone += tel + u' '
                if re.search(regex_QQ, contactName):
                    # print "contactName have QQ"
                    QQ = ""
                    find_QQ = re.findall(regex_QQ, contactName)
                    for index in range(len(find_QQ)):
                        QQ += find_QQ[index] + u' '
                        contactName = re.sub(find_QQ[index], u'', contactName)
                    contactPhone += QQ + u' '
                contactPhone = replace_space(contactPhone).strip()
                contactName = re.sub(regex_punction, u'', contactName)
                contactPhone = re.sub(u' ： ', u'：', contactPhone)
                contactName = re.sub(u' ： ', u'：', contactName)
                self.result['coInc']['incContactPhone'] += contactPhone + u' '
                self.result['coInc']['incContactName'] += contactName + u' '
                contactPhone = u''
                contactName = u''
                # print "ContactPhone:", self.result['jdInc']['incContactPhone']
                # print "ContactName:", self.result['jdInc']["incContactName"]

    def regular_inclogo(self):
        if self.logosoup:
            logo_dir = self.zhilian_dir+'incLogo_zhilian/'
            # if not os.path.exists(logo_dir):
            #     os.makedirs(logo_dir)
            logo_Url = self.logosoup.attrs["src"]
            #下载到本地
            # logo_File = logo_dir + self.result['coInc']['incName'] + '.jpg'
#             # if not os.path.exists(logo_File):
            #     urllib.urlretrieve(logo_Url, filename=logo_File)
            # self.result["coInc"]["incLogo"] = logo_File
            #保存url
            self.result["coInc"]["incLogo"] = logo_Url

    def parser_co(self, htmlContent="", fname=None, url=None):
        """
        进一步简单语义解析
        """
        self.preprocess(htmlContent, fname, url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_incplace()
        self.regular_contactInfo()
        self.regular_inclogo()

        return self.result
if __name__ == "__main__":
    import os, json

    test = CoParserZhilian()

    path = co_path+"zhilian/"
    # path = 'test_jds/wrong_answer/'
    fnames = [path + file for file in os.listdir(path) if file.endswith("CC137816208.html")]
    starttime = time.time()
    count = 0
    # for fname in fnames:
    #       print "==" * 20, fname
    # #     #print chardet.detect(fname)
    #       htmlContent = codecs.open(fname, 'r','utf-8').read()
    # #     # print 'detail'
    #       result = test.parser_co(htmlContent, fname=None, url=None)
    # #     # print "incZipCode:",result2['jdInc']['incZipCode']
    # #     # print "ContactName:",result2['jdInc']["incContactName"]
    # #     # if len(result2['jdInc']['incUrl'])>60:
    # #     #print result
    #       print json.dumps(result,ensure_ascii=False,indent=4)
    # #     # 生成又标签或者无标签的数据，用作CNN的数据集
    # #     # generate_text_withlabel(result2, jdfrom="51job",file_path = path,count = count)
    # #     #generate_text_withoutlabel(result2, jdfrom="51job", file_path=path, count=count)
    # #     count += 1
    # #     print "the total jd parsed are:%d" % (count)
    # # endtime = time.time()

    # print "total time is: %f" % (endtime - starttime)

    #url
    result = test.parser_co(fname=None,url="http://company.zhaopin.com/CC673349025.htm")
    print json.dumps(result, ensure_ascii=False, indent=4)
    print "time:%f" %(time.time()-starttime)
