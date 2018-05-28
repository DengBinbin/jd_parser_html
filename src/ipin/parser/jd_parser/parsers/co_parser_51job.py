#!/usr/bin/env python
# coding=utf-8

import sys, re, codecs, jieba
import os
from bs4 import BeautifulSoup
import urllib2
import urllib
from urllib2 import urlopen
from collections import OrderedDict
import time
import codecs
from socket import error as SocketError
import errno
import requests


sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from base import JdParserTop,CoParserTop
from utils.util import *
from utils.path import *


reload(sys)
sys.setdefaultencoding('utf-8')


def replace_space(line):
    regex = re.compile(u' +')
    line = re.sub(regex, u' ', line)
    return line


class CoParser51Job(CoParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """

    def __init__(self):
        CoParserTop.__init__(self)
        self.job51_dir = co_path + 'img_51job/'

    # @profile
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
            # html = urlopen(url).read()
            # html=unicode(html,'gb18030',errors='ignore')
            res = requests.get(url)
            res.encoding = 'gb18030'
            html = res.text

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




        self.basicsoup = self.soup.find("div","tCompanyPage")
        self.compsoup = self.basicsoup.find("div","tHeader tHCop")
        self.jdstr = self.basicsoup.find("div","tCompany_full")
        self.photosoup = self.jdstr.find("div","tImgShow clearfix")

        # try:
        #     incName = self.compsoup.find("h1").get_text()
        # except:
        #     # print ("the company is not exists")
        #     raise ("the company is not exists")
        #
#         # if not os.path.exists(self.job51_dir):
#         #     os.makedirs(self.job51_dir)

    # @profile
    #incName、incAliasName
    def regular_incname(self):

        if self.compsoup:
            incname = ""
            incAliasName = ""
            incname = self.compsoup.find("h1").get_text()
            incAliasName = self.jdstr.find("p","tPosition_center_bottomText").get_text().strip().split("：")[1] if \
                            self.jdstr.find("p", "tPosition_center_bottomText").get_text().strip() else ""
            self.result['coInc']['incName'] = incname.strip()
            self.result['coInc']['incAliasName'] = incAliasName

    # @profile
    # incType、incScale、incIndustry
    def regular_inc_tag(self):

        if not self.compsoup:
            return
        if  self.compsoup.find("p",'ltype'):
            tags = self.compsoup.find("p",'ltype').get_text(strip=True).split(u"|")
            if len(tags) == 3:
                 self.result["coInc"]["incType"] = tags[0].strip()
                 self.result["coInc"]["incScale"] = tags[1].strip()
                 self.result["coInc"]["incIndustry"] = tags[-1].strip()
            else:
                 for tag in tags:
                     if re.search(u"公司|国企|外资|合资|外企", tag):
                         self.result["coInc"]["incType"] = tag.strip()
                     elif re.search(u"\d人", tag):
                         self.result["coInc"]["incScale"] = tag.strip()
                     # if tags and  not re.search(u"人|公司|国企",tags[-1]):
                     if tags and not re.search(u"\d人|公司|国企", tags[-1]):
                         self.result["coInc"]["incIndustry"] = tags[-1].strip()

            find_inc_intro = self.compsoup.find_next("div", "tmsg inbox").find("div","in")
            if find_inc_intro:

                intro = find_inc_intro.get_text('\n').strip()
                # print intro
                self.result['coInc']['incIntro'] = intro

    # @profile
    #incLocation、incZipCode、incCity
    def regular_incplace(self):
        incplace = ""
        incZipCode = ""
        resultList = []

        find_incplace = self.jdstr.find("span", "label", text=re.compile(u"公司地址："))
        if find_incplace:
            incplace = find_incplace.find_previous("p", "fp").get_text().strip()

            incZipCode = re.search(self.ZIP,incplace)
            incplace = incplace[incplace.find(u"：") + 1:incplace.find('(')].strip()  # 去掉公司地址这几个字和后面的右边

            self.result['coInc']['incLocation'] = incplace
            self.result['coInc']['incZipCode'] = incZipCode.group(0) if incZipCode else ""

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

    # @profile
    #incContactEmail、incUrl
    def regular_contactInfo(self):
        if self.MAIL.findall(self.result["coInc"]["incIntro"]):
            self.result['coInc']["incContactEmail"] += " ".join(self.MAIL.findall(self.result["coInc"]["incIntro"]))
        if self.jdstr.find("div","bmsg tmsg inbox"):
            self.result['coInc']['incUrl'] =  self.jdstr.find("div","bmsg tmsg inbox").find("a").get_text()

    # @profile
    def regular_inclogo(self):
        self.logoName = None
        self.photoName = None
        #公司logo
        if self.compsoup.find("img","cimg"):
            logo_dir = self.job51_dir+'incLogo_51job/'
            # if not os.path.exists(logo_dir):
                # os.makedirs(logo_dir)
            logo_Url = self.compsoup.find("img","cimg").attrs["src"]
            logo_File = logo_dir + self.result['coInc']['incName'] + '.jpg'
            #下载到本地
#             # if not os.path.exists(logo_File):
            #     urllib.urlretrieve(logo_Url, filename=logo_File)
            self.result["coInc"]["incLogo"] = logo_Url
        #招聘图片
        if self.photosoup:
            photo_Files = []
            cnt = 0
            for photo in  self.photosoup.find_all("img"):
                #对于每个公司的图片，分开文件夹来进行存储
                photo_dir = self.job51_dir+'incPhoto_51job/'+self.result['coInc']['incName']+'/'
                # if not os.path.exists(photo_dir):
                    # os.makedirs(photo_dir)
                #对于每张图，photo_Url是图片Url、photo_file是图片存在本地的地址
                photo_Url = photo.attrs["src"]
                photo_File = photo_dir + str(cnt) + '.jpg'
                photo_Files.append(photo_Url)
                # photo_Files.append(photo_File)
                #下载到本地
#                 # if not os.path.exists(photo_File):
                #     urllib.urlretrieve(photo_Url, filename=photo_File)

                cnt+=1

            self.result["coInc"]["incPhoto"] = photo_Files
            self.photoName = photo_Files




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

    test = CoParser51Job()

    path = co_path+"51job/"
    # path = 'test_jds/wrong_answer/'
    # fnames = [path + file for file in os.listdir(path) if file.endswith("100045.html")]
    starttime = time.time()
    count = 0
    # for fname in fnames:
    #     print "==" * 20, fname
    #     #print chardet.detect(fname)
    #     htmlContent = codecs.open(fname, 'r','utf-8').read()
    #     # print "simple"
    #     # result1 = test.parser_basic(htmlContent,fname=None,url=None)
    #     # print json.dumps(result1,ensure_ascii=False,indent=4)
    #     # print 'detail'
    #     result = test.parser_co(htmlContent, fname=None, url=None)
    #     # print "incZipCode:",result2['jdInc']['incZipCode']
    #     # print "ContactName:",result2['jdInc']["incContactName"]
    #     # if len(result2['jdInc']['incUrl'])>60:
    #     #print result
    #     print json.dumps(result,ensure_ascii=False,indent=4)
    #     # 生成又标签或者无标签的数据，用作CNN的数据集
    #     # generate_text_withlabel(result2, jdfrom="51job",file_path = path,count = count)
    #     #generate_text_withoutlabel(result2, jdfrom="51job", file_path=path, count=count)
    #     count += 1
    #     print "the total jd parsed are:%d" % (count)
    # endtime = time.time()
    # print "total time is: %f" % (endtime - starttime)
    result = test.parser_co(fname=None,url="http://jobs.51job.com/all/co148102.html")
    print json.dumps(result,ensure_ascii=False,indent=4)
    # enttime = timeit.timeit()
    # print "time:%f" %(enttime-starttime)
