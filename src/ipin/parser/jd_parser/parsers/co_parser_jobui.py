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
from base import JdParserTop,CoParserTop
import time
import codecs


reload(sys)
sys.setdefaultencoding('utf-8')


def replace_space(line):
    regex = re.compile(u' +')
    line = re.sub(regex, u' ', line)
    return line


class CoParserJobUI(CoParserTop):
    """
    对51job Jd 结合html 进行解析,分新旧两种情况判断并解析
    """

    def __init__(self):
        CoParserTop.__init__(self)
        self.jobui_dir = co_path + 'img_jobui/'

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



        # 换行符问题
        self.html = re.sub("<br.*?/?>|<BR.*?/?>|<br>|<li>", "\n", html)
        self.soup = BeautifulSoup(self.html, "lxml",from_encoding="utf-8")

        self.headsoup = self.soup.find("div","middat")
        self.basicsoup = self.soup.find("div","intro")
        self.locsoup = self.soup.find("div","s-wrapper")
        self.incstr = self.basicsoup.find("div","cfix fs16").find("p","mb10 cmp-txtshow")

        self.logosoup = self.headsoup.find("div", "company-logo")
        self.productsoup =self.soup.find("div","jk-matter pdCase")

        try:
            incName = self.headsoup.find("h1").get_text()
        except:
            # print ("the company is not exists")
            raise ("the company is not exists")

        # if not os.path.exists(self.jobui_dir):
        #     os.makedirs(self.jobui_dir)

    #incName、incAliasName
    def regular_incname(self):

        incName = ""
        incName = self.headsoup.find("h1").get_text()

        self.result['coInc']['incName'] = incName.strip()

    # incType、incScale、incIndustry、incAliasName、incIntro、incIntroShort
    def regular_inc_tag(self):

        inc_tags = self.basicsoup.find("dl","j-edit hasVist dlli mb10").find_all("dt") if self.basicsoup else []

        for tag in inc_tags:
            key = tag.get_text()
            if re.search(u"信息", key):
                self.result["coInc"]["incType"] = tag.find_next_sibling("dd").get_text().strip().split(u'/')[0]
                self.result["coInc"]["incScale"] = tag.find_next_sibling("dd").get_text().strip().split(u'/')[1] \
                    if len(tag.find_next_sibling("dd").get_text().strip().split(u'/'))==2 else u""
            elif re.search(u"行业", key):
                 self.result["coInc"]["incIndustry"] = tag.find_next_sibling("dd").get_text().strip()
            elif re.search(u"简称", key):
                 self.result["coInc"]["incAliasName"] = tag.find_next_sibling("dd").get_text().strip()


        if self.incstr:
            intro = self.incstr.get_text()
            intro = [line.strip()  for line in intro.split(u'\n') if line!=u''and line!=u'\r']

            intro = '\n'.join(intro)
            self.result['coInc']['incIntro'] = intro
        if self.headsoup:
            introShort = u''
            introShort = self.headsoup.find("p","fs16 gray9 sbox company-short-intro").get_text().replace(u'\"',u'') \
                if self.headsoup.find("p","fs16 gray9 sbox company-short-intro") else u''
            self.result['coInc']['incIntroShort'] = introShort


    #incCity、incLocation、incContactEmail、incContactPhone、incZipCode、incUrl、incContactQQ
    def regular_incplace(self):
        incplace = ""
        incZipCode = ""
        resultList = []

        contact_tags = self.locsoup.find_all("dt") if self.locsoup else []
        cnt = 0
        for tag in contact_tags:
            key = tag.get_text()
            if re.search(u"地址", key):
                incLocation = tag.find_next_sibling("dd").get_text().strip()
                incLocation = re.sub(u'\(',u'（',incLocation)
                self.result["coInc"]["incLocation"] = incLocation.split(u'（')[0]
                if self.ZIP.findall(incLocation):
                    self.result['coInc']['incZipCode'] += " ".join(self.ZIP.findall(incLocation))
            elif re.search(u"网站", key):
                 self.result["coInc"]["incUrl"] = tag.find_next_sibling("dd").get_text().strip()
            elif re.search(u"联系我们", key):
                if cnt==0:
                     contact_info = tag.find_next_sibling("dd").get_text().strip()
                     if self.MAIL.findall(contact_info):
                         self.result['coInc']['incContactEmail'] += " ".join(self.MAIL.findall(contact_info))
                     if self.PHONE.findall(contact_info):
                         self.result['coInc']['incContactPhone'] += " ".join(self.PHONE.findall(contact_info))
                cnt+=1
            elif re.search(u"QQ", key):
                self.result['coInc']['incContactQQ'] += " ".join(self.QQ.findall(tag.find_next_sibling("dd").get_text().strip()))
                break

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

    #
    # def regular_contactInfo(self):
    #     intro = [line.strip() for line in self.result["coInc"]["incIntro"].split('\n') if line.strip()]
    #
    #     if self.MAIL.findall(self.result["coInc"]["incIntro"]):
    #         self.result['coInc']["incContactEmail"] += " ".join(self.MAIL.findall(self.result["coInc"]["incIntro"]))
    #     if not self.result['coInc']['incUrl']:
    #         incUrl = self.INC_URL.search(self.result["coInc"]["incIntro"])
    #         if not self.result["coInc"]["incUrl"] and incUrl:
    #               self.result["coInc"]["incUrl"] = re.search("[\w\d\./_:\-]+", incUrl.group()).group()
    #
    #     regex_contactPhone = re.compile(u'联络方式|联络电话|固定电话|固话|电话|联系电话|微信|QQ|联系方式|传真|Tel')
    #     regex_contactName = re.compile(u'联络|联系人$|联络人')
    #     regex_number = re.compile(u'(?<=[^-Q/——_ 0123456789])([-/_ ——0123456789]{7,})')
    #     regex_QQ = re.compile(u'QQ\d{6,}|QQ|qq')
    #     regex_punction = re.compile(u'[\],.;:，、。（）《》【】！#……()<>；“”'']')
    #     #公司联系信息
    #     for line in intro:
    #
    #         line = re.sub(u':', u'：', line)
    #         line = re.sub(u'：', u' ： ', line)
    #         contactPhone = u''
    #         contactName = u''
    #
    #         line = replace_space(line.replace(u'\xa0',u' '))
    #
    #         if re.search(u'联络方式|微信 ：|联络电话|联系电话 ：|电话 ：|电 话 ：|联系方式 ：|传真 ：|Tel ：', line) \
    #                 or re.search(u'联系人 ：|联络 ：|人员 ：|联络人', line):
    #             line = line.strip().replace(u'电 话',u'电话').split(u' ')
    #             index = [index for (index, i) in enumerate(line) if i == u'：']
    #
    #             for i in range(len(index)):
    #                 # 只要不是最后一个冒号
    #                 if i != len(index) - 1:
    #                     if re.search(regex_contactPhone, line[index[i] - 1]):
    #                         for j in range(index[i] - 1, index[i + 1] - 1):
    #                             if len(line[j]) > 40 and not re.search(regex_number, line[j]):
    #                                 if len(re.findall(regex_punction, line[j])) > 0:
    #                                     last_punction = re.findall(regex_punction, line[j])[-1]
    #                                     line[j] = line[j].split(last_punction)[-1]
    #
    #                                     contactPhone += line[j] + u' '
    #
    #                             else:
    #                                 contactPhone += line[j] + u' '
    #
    #                     elif re.search(regex_contactName, line[index[i] - 1]):
    #                         for j in range(index[i] + 1, index[i + 1] - 1):
    #                             if len(line[j]) > 40 and not re.search(regex_number, line[j]):
    #                                 if len(re.findall(regex_punction, line[j])) > 0:
    #                                     last_punction = re.findall(regex_punction, line[j])[-1]
    #                                     line[j] = line[j].split(last_punction)[-1]
    #
    #                                     contactName += line[j] + u' '
    #                             else:
    #                                 contactName += line[j] + u' '
    #
    #
    #                 # 是最后一个冒号
    #                 else:
    #                     #冒号前面一个词找到了联系电话之类的字眼
    #                     if re.search(regex_contactPhone, line[index[i] - 1]):
    #                         contactPhone += line[index[i]+1] + u' '
    #
    #                     elif re.search(regex_contactName, line[index[i] - 1]):
    #                         for j in range(index[i] + 1, len(line)):
    #                             if len(line[j]) > 40 and not re.search(regex_number, line[j]):
    #                                 if len(re.findall(regex_punction, line[j])) > 0:
    #                                     last_punction = re.findall(regex_punction, line[j])[-1]
    #                                     line[j] = line[j].split(last_punction)[-1]
    #
    #                                     contactName += line[j] + u' '
    #                             else:
    #                                 contactName += line[j] + u' '
    #
    #             if re.search(regex_number, contactName) or re.search(u'\d{11}', contactName):
    #                 # print "contactName have tel"
    #                 tel = ""
    #                 find_tel = re.findall(regex_number, contactName)
    #
    #                 if find_tel == []:
    #                     find_tel = re.findall(u'\d{11}', contactName)
    #                 for index in range(len(find_tel)):
    #                     tel = find_tel[index] + u' '
    #                     contactName = re.sub(find_tel[index], u'', contactName)
    #                     contactPhone += tel + u' '
    #             if re.search(regex_QQ, contactName):
    #                 # print "contactName have QQ"
    #                 QQ = ""
    #                 find_QQ = re.findall(regex_QQ, contactName)
    #                 for index in range(len(find_QQ)):
    #                     QQ += find_QQ[index] + u' '
    #                     contactName = re.sub(find_QQ[index], u'', contactName)
    #                 contactPhone += QQ + u' '
    #             contactPhone = replace_space(contactPhone).strip()
    #             contactName = re.sub(regex_punction, u'', contactName)
    #             contactPhone = re.sub(u' ： ', u'：', contactPhone)
    #             contactName = re.sub(u' ： ', u'：', contactName)
    #             self.result['coInc']['incContactPhone'] += contactPhone + u' '
    #             self.result['coInc']['incContactName'] += contactName + u' '
    #             contactPhone = u''
    #             contactName = u''
    #             # print "ContactPhone:", self.result['jdInc']['incContactPhone']
    #             # print "ContactName:", self.result['jdInc']["incContactName"]

    def regular_inclogo(self):
        #公司logo
        if self.logosoup:
            logo_dir = self.jobui_dir + 'incLogo_jobui/'
            # if not os.path.exists(logo_dir):
            #     os.makedirs(logo_dir)
            if self.logosoup.find("img"):
                logo_Url =  self.logosoup.find("img").attrs["src"]
                logo_file = logo_dir + self.result['coInc']['incName'] + '.jpg'
                #下载并保存字段为本地路径
#                 # if not os.path.exists(logo_file):
                # urllib.urlretrieve(logo_Url, filename=logo_file)
                # self.result["coInc"]["incLogo"] = logo_file
                #不下载，保存字段为url地址
                self.result["coInc"]["incLogo"] = logo_Url

        # #对给定的每一个页面找到其中的公司图片
        def find_photos(url, pic_urls, pic_names,Cnt):
            photo_html = urlopen(url).read()
            photo_html = unicode(photo_html, 'utf-8', errors='ignore')
            photo_html = re.sub("<br.*?/?>|<BR.*?/?>|<br>", "\n", photo_html)
            self.photosoup = BeautifulSoup(photo_html, "lxml", from_encoding="utf-8")
            if self.photosoup:
                # 找到图片
                find_pic = self.photosoup.find("ul", "piclist cfix")
                if find_pic:
                    pics = self.photosoup.find("ul", "piclist cfix").find_all("li")
                    for pic in pics:

                        pic_urls.append(pic.find("span").attrs["src"])
                        photo_File = photo_dir + self.result["coInc"]["incName"] + "_" + str(Cnt) + '.jpg'
                        # pic_names.append(photo_dir+pic.find("span", "piclist-namec").get_text().strip())
                        pic_names.append(photo_File)
                        Cnt+=1

        #公司环境图片
        photo_url = self.url+'photos/'
        photo_html = urlopen(photo_url).read()
        photo_html = unicode(photo_html, 'utf-8', errors='ignore')
        photo_html = re.sub("<br.*?/?>|<BR.*?/?>|<br>", "\n", photo_html)
        self.photosoup  = BeautifulSoup(photo_html, "lxml", from_encoding="utf-8")
        photo_Urls = []
        photo_Files = []
        if self.photosoup:
            #找到图片
            find_pic = self.photosoup.find("ul","piclist cfix")
            if find_pic:
                pages = self.photosoup.find("div","picarea sbox").find("p","pager cfix box")
                #找到有哪些页码
                if pages:
                    page_nums = [int(i.get_text()) for i in pages.find_all("a")[:-1] ]
                    #首先加入第一页的图片
                    pics = self.photosoup.find("ul","piclist cfix").find_all("li")
                    Cnt = 0
                    for pic in pics:
                        photo_Url =  pic.find("span").attrs["src"]
                        photo_Urls.append(photo_Url)
                        # photo_Name = pic.find("span","piclist-namec").get_text().strip()

                        photo_dir = self.jobui_dir +'incPhoto_jobui/'+self.result["coInc"]["incName"] + '/'
                        # if not os.path.exists(photo_dir):
                        #     os.makedirs(photo_dir)
                        photo_File = photo_dir + self.result["coInc"]["incName"]+"_"+str(Cnt)+'.jpg'
                        photo_Files.append(photo_File)
                        Cnt+=1

                    for page in page_nums:
                         find_photos(photo_url+'p'+str(page)+'/',photo_Urls,photo_Files,Cnt)

            if len(photo_Files) != 0:
                # photo_dicts = dict()
                for idx in range(len(photo_Urls)):
                    photo_File = photo_Files[idx]+ str(Cnt) + '.jpg'
                    Cnt+=1
#                     # if not os.path.exists(photo_File):
                    # urllib.urlretrieve(photo_Urls[idx],filename=photo_File)
                #保存字段为本地路径
                # self.result["coInc"]["incPhoto"] = [name for name in photo_Files]
                #保存字段为url
                self.result["coInc"]["incPhoto"] = [name for name in photo_Urls]

    def regular_incProduct(self):
        if self.productsoup:
            prod_dir = self.jobui_dir +'incProduct_jobui/'+self.result["coInc"]["incName"] + '/'
            # if not os.path.exists(prod_dir):
            #     os.makedirs(prod_dir)
            prod_list = []
            all_prod = self.productsoup.find_all("div", "pdBox box")
            for prod in all_prod:

                prod_Photo = prod.find("div","pdPhoto").find("img").attrs['src']
                prod_Name = prod.find("div", "pdIntro").find("a").get_text()
                prod_Desc = prod.find("div", "pdIntro").find("p").attrs['title'].strip()
                prod_Url = prod.find("div", "pdIntro").find("a").attrs["href"]
                #下载到本地,并保存字段为本地路径
                # prod_File = prod_dir + str(prod_Name) + '.jpg'
#                 # if not os.path.exists(prod_File):
                # urllib.urlretrieve(prod_Photo, filename=prod_File)

                prod = {}
                prod["prod_Desc"] = prod_Desc
                prod["prod_Url"] = prod_Url
                #Photo字段为本地路径
                # prod["prod_Photo"] = prod_File
                prod["prod_Photo"] = prod_Photo
                prod["prod_Name"] = prod_Name

                prod_list.append(prod)
            self.result["coInc"]["prdInfo"] = prod_list



                #将产品信息放入到一个字典中，key就是产品名，value是每个产品的描述、链接以及本地存放路径
                # prod_Info[prod_Name] = {}
                # prod_Info[prod_Name]["prod_Desc"] = prod_Desc
                # prod_Info[prod_Name]["prod_Url"] = prod_Url
                # prod_Info[prod_Name]["prod_Photo"] = prod_Photo
                #
                # self.result["coInc"]["prdName"]+=str(cnt)+'.'+prod_Name+'\n'
                # self.result["coInc"]["prdUrl"]+=str(cnt)+'.'+prod_Url+'\n'
                # self.result["coInc"]["prdDesc"]+=str(cnt)+'.'+prod_Desc+'\n'
                # self.result["coInc"]["prdPhoto"] += str(cnt) + '.' + prod_File + '\n'


    def regular_incWelfare(self):
        if self.headsoup.find("div","company-tab-box sbox"):
            welfare_url = self.url+"salary"
            welfare_html = urlopen(welfare_url).read()
            welfare_html = unicode(welfare_html, 'utf-8', errors='ignore')
            welfare_html = re.sub("<br.*?/?>|<BR.*?/?>|<br>", "\n", welfare_html)
            self.welfaresoup = BeautifulSoup(welfare_html, "lxml", from_encoding="utf-8")
            welfare = self.welfaresoup.find("div","jk-matter").find_all("span")
            for item in welfare:

                self.result["coInc"]["incLabel"]+=item.find("a").get_text()+u'|'

    def regular_others(self):
        for item in self.soup.find("ul","icon-list j-footIco").find_all("li"):
            #data-show等于1说明有内容
            if item.attrs["data-show"].strip()==u'1':
                if item.find("a"):
                    item_data = item.find("a")
                    data_type = item_data.attrs["data-type"]
                elif item.find("span"):
                    item_data = item.find("span")
                    data_type = item_data.attrs["data-type"]
                if data_type ==u'WX':
                    self.result["coInc"]["incWechatName"] = item_data.attrs["title"]
                    self.result["coInc"]["incWechatUrl"] = item_data.attrs["data-web"]
                elif data_type ==u'WB':
                    self.result["coInc"]["incWeiboName"] = item_data.attrs["title"]
                    self.result["coInc"]["incWeiboUrl"] = item_data.attrs["data-web"]
        #找二维码
        if self.soup.find("ul", "icon-list j-footIco").find("input").attrs["value"]:
            wechat_dir = self.jobui_dir +'wechatCode_jobui/'
            # if not os.path.exists(wechat_dir):
            #     os.makedirs(wechat_dir)
            incWechatCode_Url = self.soup.find("ul", "icon-list j-footIco").find("input").attrs["value"]
            incWechatCode_File = wechat_dir+self.result["coInc"]["incName"]+'.jpg'
            #下载二维码到本地并将相应字段设置为本地路径
#             # if not os.path.exists(incWechatCode_File):
            # urllib.urlretrieve(incWechatCode_Url,filename=incWechatCode_File)
            self.result["coInc"]["incWechatCode"] = self.soup.find("ul", "icon-list j-footIco").find("input").attrs["value"]

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
        self.regular_others()
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

    test = CoParserJobUI()

    path = co_path+"jobui/"
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
    # result = []
    # result.append(test.parser_co(fname=None,url="http://www.jobui.com/company/1385891/"))
    # result.append(test.parser_co(fname=None, url="http://www.jobui.com/company/281097/"))
    # result.append(test.parser_co(fname=None, url="http://www.jobui.com/company/11565066/"))
    # result.append(test.parser_co(fname=None, url="http://www.jobui.com/company/12582565/"))
    # result.append(test.parser_co(fname=None, url="http://www.jobui.com/company/8553696/"))
    result = test.parser_co(fname=None, url="http://www.jobui.com/company/8104741/")
    print json.dumps(result,ensure_ascii=False,indent=4)
    result = json.dumps(result)

    # for item in result:
    #     data = pd.DataFrame(item)
    #     # print data
    #     data.to_csv(u"职友集.csv", encoding="utf8",mode="a",tupleize_cols=True)
