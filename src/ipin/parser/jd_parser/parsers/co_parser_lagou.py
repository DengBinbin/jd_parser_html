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
import numpy as np
import chardet
from socket import error as SocketError
import errno
import pickle
import requests

sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))

from utils.path import *
from base import CoParserTop




reload(sys)
sys.setdefaultencoding('utf-8')


def replace_space(line):
    regex = re.compile(u' +')
    line = re.sub(regex, u' ', line)
    return line


class CoParserLagou(CoParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """

    def __init__(self):
        CoParserTop.__init__(self)
        self.lagou_dir = co_path + 'img_lagou/'

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
        self.url = url
        if url != None:
            # print "url"
            # urlopen有时候会出现104错误，原因未知，用requests来代替即可
            # html = urlopen(url).read()
            # html=unicode(html,'utf-8',errors='ignore')
            res = requests.get(url)
            res.encoding = 'utf-8'
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
        self.html = re.sub("<br.*?/?>|<BR.*?/?>|<br>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml",from_encoding="utf-8")
        self.headsoup = self.soup.find("div","company_info")
        self.basicsoup = self.soup.find("div",id = "container_right")
        self.locsoup = self.soup.find("div",id="location_container")
        self.incstr = self.soup.find("div",id="company_intro").find("span","company_content")
        self.developsoup = self.soup.find("div",id = "history_container")
        self.logosoup = self.soup.find("div", "top_info").find("img")
        self.photosoup = self.soup.find("div","company_image_gallery")
        self.productsoup =self.soup.find("div","item_content")
        self.leadersoup = self.basicsoup.find("div","company_mangers_item")

        # try:
        #     incName = ""
        #     incAliasName = ""
        #     title = self.soup.find("head").find("title").get_text()
        #     incName = title.split('-')[0][:-2]
        #     incAliasName = title.split('-')[1][:-2]
        #     self.result['coInc']['incName'] = incName
        #     self.result['coInc']['incAliasName'] = incAliasName
        # except:
        #     # print ("the company is not exists")
        #     raise ("the company is not exists")

        # if not os.path.exists(self.lagou_dir):
        #     os.makedirs(self.lagou_dir)

    # @profile
    #incName、incAliasName
    def regular_incname(self):

        incName = ""
        incAliasName = ""
        title =  self.soup.find("head").find("title").get_text()
        incName = title.split('-')[0][:-2]
        incAliasName = title.split('-')[1][:-2]
        self.result['coInc']['incName'] = incName
        self.result['coInc']['incAliasName'] = incAliasName

    # @profile
    # incType、incScale、incIndustry、incAliasName、incIntro
    def regular_inc_tag(self):
        inc_tags = self.basicsoup.find("div","item_content").find("ul").find_all("li") if self.basicsoup else []
        for tag in inc_tags:
            key = tag.find("i").attrs['class'][0]
            value = tag.find("span").get_text()
            if re.search(u"type", key):
                self.result["coInc"]["incIndustry"] = value
            elif re.search(u"process", key):
                 self.result["coInc"]["incStage"] = value
            elif re.search(u"number", key):
                self.result["coInc"]["incScale"] = value

        if self.incstr:
             intro = self.incstr.get_text()
             intro = [line.strip()  for line in intro.split(u'\n') if line!=u''and line!=u'\r']

             intro = '\n'.join(intro)

             shortintro = self.headsoup.find("div","company_word")
             if shortintro:
                 self.result["coInc"]["incIntroShort"] = shortintro.get_text().strip()
             self.result['coInc']['incIntro'] = intro

    # @profile
    def regular_incplace(self):
        incplace = ""
        resultList = []

        place_tags = self.locsoup.find("div","item_con_mlist").find("ul").find_all("li") if self.locsoup else []
        location_list=[]
        for tag in place_tags:
            incCity = tag.find("p","mlist_li_title").find("span").get_text().strip().replace('，','-')
            incLocation = tag.find("p","mlist_li_desc").get_text().strip()
            locInfo = {}
            locInfo["incCity"] = incCity
            locInfo["incLocation"] = incLocation
            location_list.append(locInfo)
        self.result["coInc"]["locationInfo"] =location_list

    # @profile
    def regular_inclogo(self):
        #公司logo
        if self.logosoup:
            logo_dir = self.lagou_dir + 'incLogo_lagou/'
            # if not os.path.exists(logo_dir):
            #     os.makedirs(logo_dir)
            logo_Url =  self.logosoup.attrs["src"]
            #下载文件到本地并将相应字段设置为本地路径
            # postfix = '.' + logo_Url.split('.')[-1]
            # logo_File = logo_dir + self.result['coInc']['incName'] + postfix
#             # if not os.path.exists(logo_File):
            #     urllib.urlretrieve(logo_Url, filename=logo_File)
            # self.result["coInc"]["incLogo"] = logo_File
            #不下载，设置相应字段为url
            self.result["coInc"]["incLogo"] = logo_Url

        #公司环境图片
        if self.photosoup.find("ul",id = "rotateImages"):
            find_pic = self.photosoup.find_all("li")
            photo_dir = self.lagou_dir + 'incPhoto_lagou/' + self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(photo_dir):
            #     os.makedirs(photo_dir)

            photo_Urls = []
            photo_Files = []
            Cnt = 1
            for pic in find_pic:
                if  pic.attrs:
                    photo_Url =  u'http://www.lagou.com/'+pic.attrs['data-item']
                    photo_Urls.append(photo_Url)
                    postfix = '.' + photo_Url.split('.')[-1]
                    photo_File = photo_dir + self.result["coInc"]["incName"]+'_'+str(Cnt)+ postfix
                    photo_Files.append(photo_File)
                    Cnt+=1
                    #下载到本地并将相应字段设置为本地路径
#                     # if not os.path.exists(photo_File):
                    #     urllib.urlretrieve(photo_Url, filename=photo_File)

            # self.result["coInc"]["incPhoto"] = [name for name in photo_Files]
            self.result["coInc"]["incPhoto"] = [name for name in photo_Urls]

    # @profile
    def regular_incWelfare(self):

        if self.soup.find("div","tags_container item_container"):
            welfare = self.soup.find("div","tags_container item_container").find("ul","item_con_ul clearfix")
            if welfare:
                for item in welfare.find_all("li","con_ul_li"):
                    self.result["coInc"]["incLabel"]+=item.get_text().strip()+u'|'

    # @profile
    def regular_incProduct(self):
        if self.productsoup:
            prod_dir = self.lagou_dir +'incProduct_lagou/'+self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(prod_dir):
            #     os.makedirs(prod_dir)

            prod_list = []
            all_prod = self.productsoup.find_all("div","product_content product_item clearfix")
            for prod in all_prod:
                prod_Info = prod.find("div", "product_details")
                prod_Photo = prod.find("img").attrs['src']
                postfix = '.' + prod_Photo.split('.')[-1]
                prod_Url = prod_Info.find("div", "product_url").find("a").attrs['href'] if prod_Info.find("div", "product_url").find("a").attrs else ""
                prod_Name = prod_Info.find("div","product_url").find("a").get_text().strip() if prod_Info.find("div", "product_url").find("a") else ""
                prod_Type = prod_Info.find("ul","clearfix").find("li").get_text().strip() if prod_Info.find("ul","clearfix").find("li") else ""
                prod_Desc = prod.find("div","product_profile").get_text().strip() if prod.find("div","product_profile") else ""
                #下载到本地并设置相应字段为本地路径
                # prod_File = prod_dir + str(prod_Name) + postfix
#                 # if not os.path.exists(prod_File):
                #     urllib.urlretrieve(prod_Photo, filename=prod_File)
                prod = {}
                prod["prod_Type"] = prod_Type
                prod["prod_Desc"] = prod_Desc
                prod["prod_Url"] = prod_Url
                # prod["prod_Photo"] = prod_File
                prod["prod_Photo"] = prod_Url
                prod["prod_Name"] = prod_Name

                prod_list.append(prod)
            self.result["coInc"]["prdInfo"] = prod_list
                # self.result["coInc"]["prdName"]+=str(Cnt)+'.'+prod_Name+'\n'
                # self.result["coInc"]["prdType"] += str(Cnt) + '.' + prod_Type + '\n'
                # self.result["coInc"]["prdUrl"]+=str(Cnt)+'.'+prod_Url+'\n'
                # self.result["coInc"]["prdDesc"]+=str(Cnt)+'.'+prod_Desc+'\n'
                # self.result["coInc"]["prdPhoto"] += str(Cnt) + '.' + prod_File + '\n'

    # @profile
    def regular_leaderInfo(self):
        if self.leadersoup:
            leader_dir = self.lagou_dir + 'incLeader_lagou/' + self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(leader_dir):
            #     os.makedirs(leader_dir)
            leaderInfo = self.leadersoup.find_all("li")
            leader_list = []
            for leader in leaderInfo:

                leader_Photo = leader.find("img").attrs['src'].replace("/","")
                postfix = '.'+leader_Photo.split('.')[-1]
                leader_Name = leader.find("p","item_manager_name").get_text().strip()if leader.find("p","item_manager_name") else ""
                leader_Pos = leader.find("p","item_manager_title").get_text().strip()if leader.find("p","item_manager_title") else ""
                leader_Desc = leader.find("div","item_manager_content").get_text().strip() if leader.find("div","item_manager_content") else ""
                #下载到本地
                if '/' in leader_Name:
                    leader_Name = leader_Name.replace('/','_')
                #下载到本地并将相应字段设置为本地路径
                # leader_File = leader_dir + str(leader_Name) + postfix
#                 # if not os.path.exists(leader_File) :
                #     urllib.urlretrieve(leader_Photo, filename=leader_File)
                leader = {}
                # leader["leader_Photo"] = leader_File
                leader["leader_Photo"] = leader_Photo
                leader["leader_Name"] = leader_Name
                leader["leader_Pos"] = leader_Pos
                leader["leader_Desc"] = leader_Desc
                leader_list.append(leader)
            self.result["coInc"]["leader"] = leader_list
                # self.result["coInc"]["leaderName"] += str(Cnt) + '.' + leader_Name + '\n'
                # self.result["coInc"]["leaderPos"] += str(Cnt) + '.' + leader_Pos + '\n'
                # self.result["coInc"]["leaderPhoto"] += str(Cnt) + '.' + leader_Photo + '\n'
                # self.result["coInc"]["leaderDesc"] += str(Cnt) + '.' + leader_Desc + '\n'

    # @profile
    def regular_incDevelop(self):
        #公司主页
        if self.headsoup:
            self.result["coInc"]["incUrl"] = self.headsoup.find("a").attrs['href']

        if self.developsoup:
            # 投资机构
            tag = self.developsoup.find("ul","history_ul").find_all("li")
            for key in tag:
                icon = key.find("div","li_type_icon li_type_icon2")
                if icon:
                    invest = key.find("div","desc_intro").get_text().strip().split("：")
                    if len(invest)==2:
                        key =invest[0]
                        value = invest[1]
                        if re.search(u"机构", key):
                            self.result["coInc"]["investIns"] +=value+u'  '
                    else:
                        pass
            # 发展经历
            develop = self.developsoup.find("ul","history_ul").find_all("li")
            develop_list = []
            for item in develop:
                milestoneDate = item.find("div","li_date").find("p","date_year").get_text().strip()+' '+\
                                item.find("div","li_date").find("p","date_day").get_text().strip()
                milestoneDate = milestoneDate if milestoneDate!=" " else ""
                milestoneType = item.find("div","li_type_icon").attrs['title']
                milestoneName = item.find("div","li_desc").find("span","desc_real_title").find("a").get_text().strip()
                find_Url = item.find("div","li_desc").find("span","desc_real_title").find("a")
                milestoneUrl = find_Url.attrs["href"] if find_Url.attrs else ""
                milestoneDesc = item.find("div","desc_intro").get_text().strip() if item.find("div","desc_intro").get_text().strip()!="" else ""

                develop = {}
                develop["milestoneDate"] = milestoneDate
                develop["milestoneType"] = milestoneType
                develop["milestoneName"] = milestoneName
                develop["milestoneUrl"] = milestoneUrl
                develop["milestoneDesc"] = milestoneDesc
                develop_list.append(develop)
            self.result["coInc"]["developInfo"] = develop_list

                # self.result["coInc"]["milestoneDate"] += str(Cnt) + '.' + milestoneDate + '\n'
                # self.result["coInc"]["milestoneType"] += str(Cnt) + '.' + milestoneType  + '\n'
                # self.result["coInc"]["milestoneName"] += str(Cnt) + '.' + milestoneName + '\n'
                # self.result["coInc"]["milestoneUrl"] += str(Cnt) + '.' + milestoneUrl + '\n'
                # self.result["coInc"]["milestoneDesc"] += str(Cnt) + '.' + milestoneDesc + '\n'


    def parser_co(self, htmlContent="", fname=None, url=None):
        """
        进一步简单语义解析
        """

        self.preprocess(htmlContent, fname, url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_incplace()
        self.regular_inclogo()
        self.regular_incWelfare()
        self.regular_incProduct()
        self.regular_leaderInfo()
        self.regular_incDevelop()

        return self.result

    def ouput(self):
        for k, v in self.result.iteritems():
            print k
            if isinstance(v, list):
                print '[' + ','.join(v) + ']'
            else:
                print v
            print "-" * 20


if __name__ == "__main__":
    import os, json

    test = CoParserLagou()

    path = co_path+"lagou/"
    # path = 'test_jds/wrong_answer/'
    fnames = [path + file for file in os.listdir(path) if file.endswith("lagou.html")]
    starttime = time.time()
    count = 0

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

    # result = test.parser_co(fname=None,url="http://www.lagou.com/gongsi/28092.html")
    # print json.dumps(result,ensure_ascii=False,indent=4)
