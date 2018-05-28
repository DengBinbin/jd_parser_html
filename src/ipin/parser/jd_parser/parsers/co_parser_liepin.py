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


class CoParserLiePin(CoParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """

    def __init__(self):
        CoParserTop.__init__(self)
        self.liepin_dir = co_path + 'img_liepin/'

    def preprocess(self, htmlContent=None, fname=None, url=None):
        '''

        Args:
            htmlContent: html文本
            fname: 文件名
            url: url链接

        Returns:

        '''
        self.refresh()
        self.url = url
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

        # if not os.path.exists(self.liepin_dir):
        #     os.makedirs(self.liepin_dir)

        # 换行符问题
        self.html = re.sub("<br.*?/?>|<BR.*?/?>|<br>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml",from_encoding="utf-8")

        self.headsoup = self.soup.find("div","name-and-welfare")
        self.baseinfo = self.soup.find("div","base-info clearfix").find_next_sibling("div","base-info clearfix")
        self.incstr = self.soup.find("div","company-introduction clearfix").find("p","profile")
        self.logosoup = self.soup.find("section", "clearfix").find("img")
        self.photosoup = self.baseinfo.find("ul","clearfix")
        self.productsoup =self.soup.find("div","product-introduction clearfix")

        try:
            incName = ""
            regex = re.compile(u'<h1>(.*?)<')
            incName = re.search(regex, str(self.headsoup.find("h1"))).group(1)
            self.result['coInc']['incName'] = incName.strip()
        except:
            # print ("the company is not exists")
            raise ("the company is not exists")

    #incName、incAliasName
    def regular_incname(self):

        # incName = ""
        # regex = re.compile(u'<h1>(.*?)<')
        # incName = re.search(regex,str(self.headsoup.find("h1"))).group(1)
        # self.result['coInc']['incName'] = incName.strip()

        incAliasName = ""
        incAliasName = self.headsoup.find("p").get_text().strip() if self.headsoup.find("p") else ""
        self.result["coInc"]["incAliasName"] = incAliasName

    # incScale、incIndustry、incLocation、incCity、incIntro、incIntroShort
    def regular_inc_tag(self):

        inc_tags =  self.baseinfo.find("ul").find_all("li") if self.baseinfo else []
        for tag in inc_tags:
            key = tag.find("span").get_text() if tag.find("span") else ""
            if re.search(u"规模", key):
                self.result["coInc"]["incScale"] = tag.get_text().split(u'：')[1] if len(tag.find("span").get_text().split(u'：'))==2 else tag.find("span").get_text()
            elif re.search(u"行业", key):

                self.result["coInc"]["incIndustry"] = ' '.join([ tag.get_text().strip() for tag in tag.find_all("a") if tag!=None])
            elif re.search(u"地址", key):
                 self.result["coInc"]["incLocation"] = tag.get_text().split(u'：')[1] if len(tag.find("span").get_text().split(u'：'))==2 else tag.find("span").get_text()
            elif re.search(u"融资", key):
                self.result["coInc"]["incStage"] = tag.get_text().split(u'：')[1] if len(tag.find("span").get_text().split(u'：'))==2 else tag.find("span").get_text()
            elif re.search(u"领域", key):
                self.result["coInc"]["incSubIndustry"] = tag.get_text().split(u'：')[1] if len(
                    tag.find("span").get_text().split(u'：')) == 2 else tag.find("span").get_text()

        if self.result["coInc"]["incLocation"]:
            resultList = []
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

        if self.incstr:

            intro = self.incstr.get_text().strip()
            self.result['coInc']['incIntro'] = intro

        # if self.headsoup:
        #     introShort = u''
        #     introShort = self.headsoup.find("p","fs16 gray9 sbox company-short-intro").get_text().replace(u'\"',u'') \
        #         if self.headsoup.find("p","fs16 gray9 sbox company-short-intro") else u''
        #     self.result['coInc']['incIntroShort'] = introShort


    def regular_inclogo(self):
        #公司logo
        if self.logosoup:
            logo_dir = self.liepin_dir + 'incLogo_liepin/'
            # if not os.path.exists(logo_dir):
            #     os.makedirs(logo_dir)
            logo_Url =  self.logosoup.attrs["src"]

            if logo_Url.startswith("http"):
                #下载本地
                # logo_File = logo_dir + self.result['coInc']['incName'] + '.jpg'
                # urllib.urlretrieve(logo_Url, filename=logo_File)
                # self.result["coInc"]["incLogo"] = logo_File
                #保存url
                self.result["coInc"]["incLogo"] = logo_Url
            else:
                pass

        if self.photosoup:
            find_pic = self.photosoup.find_all("li")
            photo_dir = self.liepin_dir + 'incPhoto_liepin/' + self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(photo_dir):
            #     os.makedirs(photo_dir)

            photo_Urls = []
            photo_Files = []
            Cnt = 1
            for pic in find_pic:
                # print pic
                if pic.find("a").attrs:
                    photo_Url = pic.find("a").attrs['href']
                    photo_Urls.append(photo_Url)
                    #保存本地
                    # postfix = '.' + photo_Url.split('.')[-1]
                    # photo_File = photo_dir + self.result["coInc"]["incName"] + '_' + str(Cnt) + postfix
                    # photo_Files.append(photo_File)
                    # Cnt += 1
#                     # if not os.path.exists(photo_File):
                    #     urllib.urlretrieve(photo_Url, filename=photo_File)
                    #保存url

            # self.result["coInc"]["incPhoto"] = [name for name in photo_Files]
            self.result["coInc"]["incPhoto"] = [name for name in photo_Urls]


    def regular_incProduct(self):
        if self.productsoup:
            prod_dir = self.liepin_dir +'incProduct_liepin/'+self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(prod_dir):
            #     os.makedirs(prod_dir)
            prod_list = []
            Cnt=1
            all_prod = self.productsoup.find_all("dl", "clearfix")
            for prod in all_prod:
                prod_Photo = prod.find("dt").find("img").attrs['src']
                prod_Desc = prod.find("dd").find("p").get_text().strip() if prod.find("dd").find("p") else ""
                # 下载到本地
                # postfix = '.' + prod_Photo.split('.')[-1]
                # prod_File = prod_dir + self.result["coInc"]["incName"]+"_"+str(Cnt) + postfix
#                 # if not os.path.exists(prod_File):
                #     urllib.urlretrieve(prod_Photo, filename=prod_File)
                #保存url
                prod = {}
                prod["prod_Desc"] = prod_Desc
                prod["prod_Photo"] = prod_Photo
                # prod["prod_Photo"] = prod_File
                prod_list.append(prod)
            self.result["coInc"]["prdInfo"] = prod_list


    def regular_incWelfare(self):
        if self.headsoup.find("div","relative").find("ul"):

            welfare = self.headsoup.find("div","relative").find("ul").find_all("li")
            for item in welfare:
                self.result["coInc"]["incLabel"] += item.get_text().strip() + u'|'


    def parser_co(self, htmlContent="", fname=None, url=None):
        """
        进一步简单语义解析
        """


        self.preprocess(htmlContent, fname, url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_inclogo()
        self.regular_incProduct()
        self.regular_incWelfare()
        return self.result



if __name__ == "__main__":
    import os, json

    test = CoParserLiePin()

    path = co_path+"liepin/"
    # path = 'test_jds/wrong_answer/'
    fnames = [path + file for file in os.listdir(path) if file.endswith("CC302346880.html")]
    starttime = time.time()
    count = 0
    '''
    for fname in fnames:
          print "==" * 20, fname
    #     #print chardet.detect(fname)
          htmlContent = codecs.open(fname, 'r','utf-8').read()
    #     # print 'detail'
          result = test.parser_co(htmlContent, fname=None, url=None)
    #     # print "incZipCode:",result2['jdInc']['incZipCode']
    #     # print "ContactName:",result2['jdInc']["incContactName"]
    #     # if len(result2['jdInc']['incUrl'])>60:
    #     #print result
          print json.dumps(result,ensure_ascii=False,indent=4)
    #     # 生成又标签或者无标签的数据，用作CNN的数据集
    #     # generate_text_withlabel(result2, jdfrom="51job",file_path = path,count = count)
    #     #generate_text_withoutlabel(result2, jdfrom="51job", file_path=path, count=count)
    #     count += 1
    #     print "the total jd parsed are:%d" % (count)
    # endtime = time.time()
    '''
    # print "total time is: %f" % (endtime - starttime)
    result = test.parser_co(fname=None,url="https://company.liepin.com/2191558")
    # starttime = timeit.timeit()
    # result2 = test.parser_detail(fname=None,url="http://jobs.51job.com/shenzhen-ftq/74324473.html?s=0")
    print json.dumps(result,ensure_ascii=False,indent=4)
    # enttime = timeit.timeit()
    # print "time:%f" %(enttime-starttime)
