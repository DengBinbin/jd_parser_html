#!/usr/bin/env python
# coding=utf-8

import sys,re,codecs,jieba
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
reload(sys)
sys.setdefaultencoding('utf-8')
from bs4 import BeautifulSoup
from urllib2 import urlopen
from collections import OrderedDict
from base import JdParserTop
import datetime
from utils.util import *
from utils.path import *
import numpy as np
reload(sys)
sys.setdefaultencoding('utf-8')


class JdParserLagou(JdParserTop):
    """
    对lagou Jd 结合html 进行解析
    """
    def __init__(self):
        JdParserTop.__init__(self)


    def preprocess(self,htmlContent=None,fname=None,url=None):
        self.refresh()
        self.inc_url=""
        self.result["jdFrom"] = "lagou"


        html = ""

        if url!=None:
            html = urlopen(url).read()
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = codecs.open(fname,'rb','utf-8').read()

       
        self.html = html
        #self.html= re.sub(u"<br./?./?>|<BR.?/?>|<br>",u"。",html)
        soup = BeautifulSoup(self.html)


        self.jdsoup = soup.find("dl","job_detail")
        self.compsoup = soup.find("dl","job_company")

        self.jdstr = self.jdsoup.find("dd","job_bt").get_text('\n').strip()

        self.jdstr  =re.sub(u'\n+','\n',self.jdstr)

        # split_jdstr = self.jdstr.split('\n')
        # del_line = []
        # for index in range(len(split_jdstr)):
        #     if len(split_jdstr[index])<=3 and re.findall('\d',split_jdstr[index]):
        #         split_jdstr[index] +=split_jdstr[index+1]
        #         del_line .append(split_jdstr[index+1])
        # for i in del_line:
        #     split_jdstr.remove(i)
        # jdstr = u''
        # for line in split_jdstr:
        #     jdstr+=line+u'\n'
        # print jdstr
        # self.jdstr = jdstr

        #修复换行符问题
        split_jdstr = self.jdstr.split('\n')
        jd_str = u''
        num_tuple = []
        num_index = []
        regex = re.compile(u'(\d)')
        #找到错位的数字
        for index in range(len(split_jdstr)):
            #print split_jdstr[index]
            if re.search(regex, split_jdstr[index]):
                num_index.append(index)
                num_tuple.append((index,int(re.search(regex, split_jdstr[index]).group())))
        #找到错位数字中不是行号的那些数字，存在reverse_num中
        reverse_num = []
        for index in range(len(num_tuple)-1):
            if num_tuple[index][1]>=num_tuple[index+1][1]:
                reverse_num.append(num_tuple[index])
        #存在逆序的最大的序号认为是之前就存在的，但可能又反例存在
        if len(reverse_num)>1:
            del reverse_num[np.argmax(reverse_num[:][1])]

        reverse_num = [i[0] for i in reverse_num]
        for item in reverse_num:
            num_index.remove(item)


        for index in range(len(split_jdstr)):
            if index+1 not in num_index:
                if index+1<=len(split_jdstr)-1 and (re.search(u'：$',split_jdstr[index+1].strip()) or re.search(u'要求$',split_jdstr[index+1].strip())):
                    jd_str+=split_jdstr[index] + u'\n'
                else:
                    jd_str += split_jdstr[index]
            else:
                jd_str+=split_jdstr[index]+u'\n'
        #print jd_str
        self.jdstr = jd_str



        self.linelist = [ line.strip() for line in self.SPLIT_LINE.split(self.jdstr) if len(line)>2]


    def regular_inc_name(self):
        link = self.compsoup.find("dt").find("img",{"class":"b2"})
        res = ""
        if ('alt' in dict(link.attrs)):
            incname1 = link['alt']
            res = incname1
        else:
            res = self.compsoup.find("dt").find("h2","fl").get_text().split()[0]
        self.result['jdInc']['incAliasName']=re.sub(u"拉勾认证企业|拉勾未认证企业",u"",self.compsoup.find("h2").get_text()).strip()
        self.result['jdInc']["incName"] = res
        self.inc_url=self.compsoup.find("a").get("href")



    def regular_inc_tag(self):
        """
        行业，类型，规模、介绍、公司主页url、目前阶段、公司地址、投资机构
        """

        inc_tags = self.compsoup.find_all("ul")
        for ul_tag in inc_tags:
            li_tags = ul_tag.find_all("li")
            for tag in li_tags:
                if re.search(u"主页",tag.span.get_text()):
                    self.result['jdInc']["incUrl"]= tag.a.get("href")
                #此处可能会出现多个空格
                elif re.search(u"领域",tag.span.get_text()):
                    self.result['jdInc']["incIndustry"]=''.join(tag.text.strip().split()[1:])
                elif re.search(u"规模",tag.span.get_text()):
                    self.result['jdInc']["incScale"]=tag.text.split()[-1]
                elif re.search(u"目前阶段",tag.span.get_text()):
                    self.result['jdInc']["incStage"]=tag.text.split()[-1]
                elif re.search(u"投资",tag.span.get_text()):
                    self.result['jdInc']["investIns"]=tag.text.split()[-1]
                # key,val = tag.span.get_text(),tag.text.split()[-1]
                # if re.search(u"领域",key):
                #     self.result['jdInc']["incIndustry"]=val.strip()
                # elif re.search(u"规模",key):
                #     self.result['jdInc']["incScale"] = val.strip()
                # elif re.search(u"主页",key):
                #     self.result['jdInc']["incUrl"]= val.strip()
                # elif re.search(u"目前阶段",key):
                #     self.result['jdInc']["incStage"] =val.strip()
                #     # res["incIntro"]= val.strip()
                # elif re.search(u"投资",key):
                #     self.result['jdInc']["investIns"]= val.strip()

        inc_place = self.compsoup.find("div",{"id":"smallmap"}).findPrevious("div").get_text()
        self.result['jdJob']["jobWorkLoc"] = inc_place.strip()

        if self.inc_url:
            html = urlopen(self.inc_url).read()
            soup = BeautifulSoup(html,"lxml")
            incIntro = soup.find("span",{"class":"company_content"}).get_text("\n")
            self.result['jdInc']["incIntro"]=incIntro
            if soup.find("i",{"class":"address"}):
                self.result['jdInc']["incCity"]= soup.find("i",{"class":"address"}).parent.get_text().strip()






    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """
        pub_time = self.jdsoup.find("p","publish_time").get_text().split()[0]
        is_time = re.search(u'\d\d:\d\d',pub_time)
        if is_time:
            pub_time=datetime.datetime.now().strftime("%Y-%m-%d")
            self.result["pubTime"] = pub_time
            return
        is_day_ago = re.search(u'天前',pub_time)
        if is_day_ago:
            pub_day=datetime.datetime.now() - datetime.timedelta(days=int(pub_time[0]))
            pub_time=pub_day.strftime("%Y-%m-%d")
            self.result["pubTime"] = pub_time
            return

        self.result["pubTime"] = pub_time


    def regular_jobname(self):

        jobname = self.jdsoup.find("dt","clearfix join_tc_icon").find('h1')["title"]
        # jobname = self.jdsoup.find("dt","clearfix join_tc_icon").find('h1').get_text().split()[-1]
        # self.result_job['jobPosition'] = self.clean_jobname(jobname.strip())
        self.result["jdJob"]['jobPosition'] = jobname.strip()


    def regular_jobtag(self):
        """
        返回职位性质，职位类别，招聘人数
        """
        self.result["jdJob"]["jobType"] = self.jdsoup.find("dd","job_request").find_all("span")[-1].get_text()
        find_jobtype = re.search(u"实习|兼职",self.result["jdJob"]["jobPosition"])
        if find_jobtype:
            self.result["jdJob"]["jobType"] = find_jobtype.group()



    def regular_sex(self):
        """
        不限:0
        男:1
        女:2
        """
        res = u"不限"
        for line in self.linelist:
            if self.SEX.search(line):
                if re.search(u"性别不限|男女不限",line):
                    res = u"不限"
                elif re.search(u"男",line):
                    res = u"男"
                elif re.search(u"女",line):
                    res = u"女"
                break

        self.result["jdJob"]['gender'] = str(res)


    def regular_age(self):
        """
        (minage,maxage)
        """
        agestr = ""
        for line in self.linelist:
            if re.search(u"\d+后",line):continue
            if self.AGE.search(line):
                findage = re.search(u"(\d{2}[\-－到至])?\d{2}岁|(至少|不低于|不超过|不大于|大概|大约|不少于|大于)?\d+周?岁|\d+周岁(以上|左右|上下)",line)
                if findage:
                   agestr = findage.group()
                   break

        self.result["jdJob"]['age'] = agestr


    def regular_major(self):
        res = set()
        for line  in self.linelist:
            for word in jieba.cut(line):
                if len(word)>1 and word.lower() in self.majordic:
                    res.add(word.lower())

        self.result["jdJob"]["jobMajorList"] = list(res)



    def regular_degree(self):
        degree =  self.jdsoup.find("dd","job_request").find_all("span")[3].get_text().strip()
        self.result["jdJob"]['jobDiploma'] = degree



    def regular_exp(self):

        find_exp =  self.jdsoup.find("dd","job_request").find_all("span")[2]
        expstr = find_exp.get_text() if find_exp else "None"
        self.result["jdJob"]['jobWorkAge'] = expstr


    def regular_skill(self):
        res = {}
        for line in self.linelist:
            for word in jieba.cut(line):
                if len(word)>1 and word.lower() in self.skilldic:
                    res[word.lower()] = res.get(word.lower(),0) + 1

        sorted_res = sorted(res.items(), key = lambda d:d[1], reverse=True)

        res = [ word for (word,cnt) in sorted_res[:5] ]
        self.result["jdJob"]["skillList"] = res



    def regular_workplace(self):
        workplace =  self.jdsoup.find("dd","job_request").find_all("span")[1].get_text().strip()
        self.result["jdJob"]['jobWorkCity'] = workplace



    def regular_pay(self):
        paystr =  self.jdsoup.find("dd","job_request").find_all("span")[0].get_text().strip()
        if paystr:
            self.result["jdJob"]['jobSalary'] = paystr



    def regular_cert(self):
        res = []
        for line in self.linelist:
            findcert = self.CERT.search(line)
            if findcert and len(findcert.group())<6 and not re.search(u"保证",findcert.group()):
                res.append(findcert.group())
            else:
                findcert = re.search(u"有(.+资格证)",line)
                if findcert:
                    res.append(findcert.group(1))

        res = re.sub(u"[或及以上]","",'|'.join(res))
        self.result["jdJob"]['certList'] = res.split('|')



    def regular_demand(self):

        res,linelist = [],[]

        pos = list(self.START_DEMAND.finditer(self.jdstr))
        if pos:
            linelist = [re.sub("[\s　]+"," ",line.strip()) for line in self.SPLIT_LINE.split(self.jdstr[pos[-1].span()[1]:]) if len(line)>3]

        linelist = filter(lambda x:len(x)>2,linelist)

        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DEMAND.search(line):
                continue
            if self.START_DUTY.search(line):
                break
            if re.match(u"\d[、\.\s]|[（\(]?[a-z\d][\.、\s]",line) or self.DEMAND.search(line) or self.DEMAND.search(line) or self.clf.predict(line)=='demand':
                res.append(self.clean_line(line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='demand':
                res.append(self.clean_line(line))
            else:
                break

        if not res:
            for line in self.linelist:
                if self.clf.predict(line)=='demand':
                    res.append(self.clean_line(line))

        res = [str(i+1)+'.'+line for i,line in enumerate(res)]

        self.result["jdJob"]['workDemand'] = '\n'.join(res)


    def regular_duty(self):

        res,linelist = [],[]

        pos = list(self.START_DUTY.finditer(self.jdstr))
        if pos:
            linelist = [re.sub("[\s　]+"," ",line.strip()) for line in self.SPLIT_LINE.split(self.jdstr[pos[-1].span()[1]:]) if len(line)>3]

        linelist = filter(lambda x:len(x)>2,linelist)

        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DUTY.search(line):
                continue
            if self.START_DEMAND.search(line):
                break
            if re.match(u"\d[、\.\s]|[（\(]?[a-z\d][\.、\s][\u25cf\ff0d]",line) or self.DUTY.search(line) or self.clf.predict(line)=='duty':
                res.append(self.clean_line(line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='duty':
                res.append(self.clean_line(line))
            else:
                break
        if not res:
            for line in self.linelist:
                if self.clf.predict(line)=='duty':
                    res.append(self.clean_line(line))

        res = [str(i+1)+'. '+line for i,line in enumerate(res)]

        self.result["jdJob"]['workDuty'] = '\n'.join(res)


    def regular_benefit(self):

        res = []
        tmp = self.jdsoup.find("p","publish_time")
        if tmp:
            res.append(re.sub(u"职位诱惑[:：\s　]+","",tmp.findPrevious("p").get_text()))

        self.result["jdJob"]['jobWelfare'] = '\n'.join(res)


    def regular_other(self):

        self.result["jdJob"]["jobDesc"] = self.jdstr
        # self.result["jdInc"] = self.result_inc
        # self.result["jdJob"] = self.result_job



    def parser_basic(self,htmlContent=None,fname=None,url=None):
        """
        只做基本抽取，保证99%以上正确
        """
        self.preprocess(htmlContent,fname,url)
        self.regular_inc_name()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_jobtag()
        self.regular_degree()
        self.regular_exp()
        self.regular_pay()
        self.regular_benefit()
        self.regular_workplace()
        self.regular_other()
        return self.result




    def parser_detail(self,htmlContent=None,fname=None,url=None):
        """
        进一步进行简单的语义信息抽取，争取90％以上准确率
        """
        self.preprocess(htmlContent,fname,url)
        self.regular_inc_name()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_jobtag()
        self.regular_sex()
        self.regular_age()
        self.regular_major()
        self.regular_degree()
        self.regular_exp()
        self.regular_skill()
        self.regular_workplace()
        self.regular_pay()
        self.regular_cert()
        self.regular_demand()
        self.regular_duty()
        self.regular_benefit()
        self.regular_other()

        return self.result




    def ouput(self):
        for k,v in self.result.iteritems():
            print k
            print v

if __name__ == "__main__":
    import json

    test = JdParserLagou()

    path = jd_path+'lagou/'
    # path = 'test_jds/wrong_answer/'
    fnames = [path + file for file in os.listdir(path) if file.endswith("html") and file.startswith("lagou")]

    count = 0
    for fname in fnames:
        print "==" * 20, fname
        # print chardet.detect('test_jds/test/51job.html')
        htmlContent = codecs.open(fname, 'r', 'utf-8').read()
        # print "simple"

        # result1 = test.parser_basic(htmlContent,fname=None,url=None)
        # print json.dumps(result1,ensure_ascii=False,indent=4)
        # print 'detail'
        result2 = test.parser_detail(htmlContent, fname=None, url=None)
        # print "incZipCode:",result2['jdInc']['incZipCode']
        #print '*'*200
        print "incIndusty:",result2['jdInc']["incIndustry"]
        #print json.dumps(result2, ensure_ascii=False, indent=4)
        # 生成又标签或者无标签的数据，用作CNN的数据集
        # generate_text_withlabel(result2, jdfrom="51job")
        # generate_text_withoutlabel(result2,jdfrom = "51job")
        count += 1
        print "the total jd parsed are:%d" % (count)
    # #result1 = test.parser_detail(fname=None,url="http://jobs.51job.com/guangzhou/57768855.html")
    # starttime = timeit.timeit()
    # result2 = test.parser_detail(fname=None,url="http://jobs.51job.com/shenzhen-ftq/74324473.html?s=0")
    # #print json.dumps(result2,ensure_ascii=False,indent=4)
    # enttime = timeit.timeit()
    # print "time:%f" %(enttime-starttime)
    # 生成又标签或者无标签的数据，用作CNN的数据集
    # generate_text_withlabel(result2, jdfrom="lagou")
    # generate_text_withoutlabel(result2,jdfrom = "lagou")

