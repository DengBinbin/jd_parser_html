#!/usr/bin/env python
# coding=utf-8

import sys,re,codecs,jieba
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
reload(sys)
sys.setdefaultencoding('utf-8')
from bs4 import BeautifulSoup
from urllib2 import urlopen
from collections import OrderedDict,Counter
from base import JdParserTop
from utils.util import *
from utils.path import *
reload(sys)
sys.setdefaultencoding('utf-8')


class JdParserZhiLian(JdParserTop):
    """
    对结合html 进行解析
    """
    def __init__(self):
        JdParserTop.__init__(self)


    def preprocess(self,htmlContent,fname=None,url=None):
        """
        预处理，改换换行符等
        """
        self.refresh()
        self.result["jdFrom"] = "zhilian"


        html = ""
        if url!=None:
            html = urlopen(url).read()
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read()

        if len(html)<60:
            raise Exception("input arguments error")

        # self.html= re.sub("<br.*?/?>|<BR.*?/?>","\n",html)
        self.html = html
        self.soup = BeautifulSoup(self.html,"lxml")

        self.jdsoup = self.soup.find("div","terminalpage-left")
        self.compsoup = self.soup.find("div","company-box")
        jdstr = self.jdsoup.find("div","tab-inner-cont").get_text('\n').strip()
        self.jdstr = self.CLEAN_TEXT.sub(" ",jdstr)

        self.linelist = [ line.strip() for line in self.SPLIT_LINE.split(self.jdstr) if len(line)>1]

        # 先存储下来，方便解析基本字段
        self.jdtop_soup = self.soup.find("div","fixed-inner-box").find("div","inner-left fl")
        self.jdbasic_soup = self.jdsoup.find("ul","terminal-ul clearfix").find_all("li")



    def regular_incname(self):
        if self.compsoup:
            incname = self.compsoup.find('p',"company-name-t").get_text()
            self.result["jdInc"]['incName'] = incname.strip()


    def regular_inc_tag(self):
        inc_tags = self.compsoup.find("ul").find_all("li") if self.compsoup else []
        for tag in inc_tags:
            key = tag.find("span").get_text()
            if re.search(u"规模",key):
                self.result["jdInc"]["incScale"] = tag.find("strong").get_text().strip()
            elif re.search(u"性质",key):
                self.result["jdInc"]["incType"] = tag.find("strong").get_text().strip()
            elif re.search(u"行业",key):
                self.result["jdInc"]['incIndustry'] = tag.find("strong").get_text().strip()
            elif re.search(u"主页",key):
                self.result["jdInc"]["incUrl"] = tag.find("strong").get_text().strip()
            elif re.search(u"地址",key):
                self.result["jdInc"]["incLocation"] = re.sub(u"查看公司地图|[\s　]","",tag.find("strong").get_text().strip())


        find_inc_intro = self.soup.find("div",{"class":"tab-inner-cont","style":"display:none;"})

        if re.search("公司介绍",self.html) and find_inc_intro:
            self.result["jdInc"]["incIntro"] = re.sub(u'该公司其他职位',u'',find_inc_intro.get_text().strip())


        if len(self.result["jdInc"]["incUrl"])<3 and self.result["jdInc"]["incIntro"]:
            find_url = self.INC_URL.search(self.result["jdInc"]["incIntro"])
            if find_url:
                self.result["jdInc"]["incUrl"] = re.search(u"[\d\w\.:/_\-]+",find_url.group()).group()



    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """
        for li in self.jdbasic_soup[:5]:
            if re.search(u"发布时|发布日",li.span.get_text()):
                self.result["pubTime"] = li.strong.get_text().strip()

            elif re.search(u"截止时|截止日",li.span.get_text()):
                self.result["endTime"] = li.strong.get_text().strip()
        if "pubTime" not in self.result:
            self.result["pubTime"] = ""



    def regular_jobname(self):
        jobname = self.jdtop_soup.find('h1').get_text()
        self.result["jdJob"]['jobPosition'] = re.sub("\s+","",jobname.strip())

       # self.result['jobName'] = self.clean_jobname(jobname.strip()) 更好，但比较慢


    def regular_job_tag(self):

        for li in self.jdbasic_soup:
            if li.span is None:
                pass
            else:
                if re.search(u"工作性质",li.span.get_text()):
                    self.result["jdJob"]["jobType"] = li.strong.get_text()
                elif re.search(u"招聘人数",li.span.get_text()):
                    self.result["jdJob"]['jobNum'] = li.strong.get_text()
                elif re.search(u"类别",li.span.get_text()):
                    self.result["jdJob"]["jobCate"] = li.strong.get_text()

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

        self.result['jdJob']['gender'] = str(res)


    def regular_age(self):
        """
        (minage,maxage)
        """
        agestr = u"不限"
        for line in self.linelist:
            if re.search(u"\d+后",line):continue
            if self.AGE.search(line):
                findage = re.search(u"\d{2}?\s?[\-　－到至]?\s?\d{2}周?岁|(至少|不低于|不超过|不大于|大概|大约|不少于|大于)\d+周?岁|\d+周岁(以上|左右|上下)",line)
                if findage:
                    agestr = findage.group()

        self.result['jdJob']['age'] = agestr


    def regular_major(self):
        res = []
        for line in self.linelist:
            for word in jieba.cut(line):
                if word in self.majordic:
                    res.append(word)
            if res:
                break

        self.result['jdJob']["jobMajorList"] = list(set(res))



    def regular_degree(self):
        degree = "None"
        for li in self.jdbasic_soup:
            # print li.span.get_text()
            if re.search(u"学历",li.span.get_text()):
                degree = li.strong.get_text()
                break

        self.result["jdJob"]['jobDiploma'] = degree



    def regular_exp(self):

        for li in self.jdbasic_soup:
            # print li.span.get_text()
            if re.search(u"工作经验",li.span.get_text()):
                expstr = li.strong.get_text()
                break

        self.result["jdJob"]['jobWorkAge'] = expstr


    def regular_skill(self):
        res = []
        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.lower()
                if word in self.skilldic:
                    res.append(word)
        res =[w[0] for w in Counter(res).most_common(5)]
        self.result_job["skillList"] = res



    def regular_workplace(self):
        if re.search(u"工作地点|工作地址",self.jdsoup.find("ul").get_text()):
            res = self.jdbasic_soup[1].strong.get_text()
            self.result['jdJob']['jobWorkCity'] = res




    def regular_pay(self):
        if re.search(u"职位月薪",self.jdsoup.find("ul").get_text()):
            paystr = self.jdbasic_soup[0].strong.get_text()
        self.result['jdJob']['jobSalary'] = paystr.strip()


    def regular_cert(self):
        res = []
        for line in self.linelist:
            findcert = self.CERT.search(line)
            if findcert and len(findcert.group()) and not re.search(u"保证",findcert.group())<5:
                res.append(findcert.group())
            else:
                findcert = re.search(u"有(.+资格证)",line)
                if findcert:
                    res.append(findcert.group())
        res = re.sub(u"[通过或以上至少]","","|".join(res))
        self.result_job['certList'] = res.split("|")




    def regular_demand(self):

        jdstr = self.jdsoup.find("div","tab-inner-cont").get_text()
        res,linelist = [],[]
        pos = list(self.START_DEMAND.finditer(jdstr))
        if len(pos)>0:
            linelist = [line.strip() for line in self.SPLIT_LINE.split(jdstr[pos[-1].span()[1]:]) if line>3]

        linelist = filter(lambda x:len(x)>2,linelist)
        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DUTY.search(line):
                break
            if re.match(u"\d[、.\s ]|[（\(【][a-z\d][\.、\s ]|[\u25cf\uff0d]",line) or self.DEMAND.search(line) or self.clf.predict(line)=="demand":
                res.append(self.CLEAN_LINE.sub("",line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='demand':
                res.append(self.CLEAN_LINE.sub("",line))
            else:
                break

        if not res:
            linelist = [ line.strip() for line in self.SPLIT_LINE.split(jdstr) if len(line.strip())>5]
            for line in linelist:
                if self.clf.predict(line)=='demand':
                    res.append(self.CLEAN_LINE.sub("",line))

        res = [ str(i)+". "+line for i,line in enumerate(res,1) ]
        self.result_job['workDemand'] = '\n'.join(res)

    def regular_duty(self):

        jdstr = self.jdsoup.find("div","tab-inner-cont").get_text()
        res,linelist = [],[]
        pos = list(self.START_DUTY.finditer(jdstr))
        if len(pos)>0:
            linelist = [ line.strip() for line in self.SPLIT_LINE.split(jdstr[pos[-1].span()[1]:]) if line.strip()>3]
        linelist = filter(lambda x:len(x)>2,linelist)
        for i in range(len(linelist)):
            line = linelist[i]
            if self.START_DUTY.search(line):
                continue
            if self.START_DEMAND.search(line) or self.DEMAND.search(line):
                break
            if re.match(u"^\d[、.\s ]|[（\(]?[a-z\d][\.、\s ]|[\u25cf\uff0d]",line) or self.DUTY.search(line) or self.clf.predict(line)=="duty":
                res.append(self.CLEAN_LINE.sub("",line))
            elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='duty':
                res.append(self.CLEAN_LINE.sub("",line))
            else:
                break
        if not res:
            linelist = [ self.CLEAN_LINE.sub("",line) for line in self.SPLIT_LINE.split(jdstr) if len(line.strip())>5]
            for line in linelist:
                if self.clf.predict(line)=='duty':
                    res.append(self.CLEAN_LINE.sub("",line))
        res = [ str(i)+". "+line for i,line in enumerate(res,1) ]
        self.result_job['workDuty'] = '\n'.join(res)



    def regular_benefit(self):

        res = []
        job_tags = self.jdtop_soup.find("div","welfare-tab-box")
        if job_tags:
            job_tags = job_tags.find_all("span")
            for tag in job_tags:
                res.append(tag.get_text())


        self.result['jdJob']['jobWelfare'] = '\n'.join(res)


    def regular_other(self):
        #老版本
        if self.jdsoup.find("div","tab-inner-cont").find_all("div") and len(self.jdsoup.find("div","tab-inner-cont").find_all("div"))<=1:

            #print "old"
            self.jdsoup= BeautifulSoup(re.sub("<br.*?/?>|<BR.*?/?>","\n",str(self.jdsoup)),'lxml')
            jdstr= '\n'.join([item.get_text().strip() for item in self.jdsoup.find("div","tab-inner-cont").find_all("div")])
        #新版本
        else:
            #print "new"
            self.jdsoup = BeautifulSoup(re.sub("<br.*?/?>|<BR.*?/?>", "\n", str(self.jdsoup)), 'lxml')

            jdstr = '\n'.join([item.get_text().strip() for item in self.jdsoup.find("div", "tab-inner-cont").find_all("p")])
            if jdstr.strip()=='':
               jdstr = self.jdsoup.find("div","tab-inner-cont").get_text('\n').strip()

        self.result["jdJob"]['jobDesc'] = re.sub(u'查看职位地图',u'',jdstr)

        #工作地址
        if self.jdsoup.find("div","tab-inner-cont").find_all("b"):
            for row in  self.jdsoup.find("div","tab-inner-cont").find_all("b"):
                if re.search(u"工作地址",row.get_text()):
                    self.result["jdJob"]['jobWorkLoc'] =re.sub(u'查看职位地图',u'',row.find_next("h2").get_text()).strip()






    def parser_basic(self,htmlContent=None,fname=None,url=None):
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_pay()
        self.regular_degree()
        self.regular_exp()
        self.regular_workplace()
        self.regular_benefit()
        self.regular_other()

        return self.result



    def parser_detail(self,htmlContent=None,fname=None,url=None):

        self.preprocess(htmlContent,fname,url)


        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_pay()

        self.regular_sex()
        self.regular_age()
        self.regular_major()
        self.regular_degree()
        self.regular_exp()
        # self.regular_skill()
        self.regular_workplace()
        # self.regular_cert()
        # self.regular_demand()
        # self.regular_duty()
        self.regular_benefit()
        self.regular_other()

        return self.result



    def ouput(self):
        for line in self.linelist:
            print line

        for k,v in self.result.iteritems():
            print  k
            print v


if __name__ == "__main__":
    import json,os
    test = JdParserZhiLian()
    path = jd_path+"zhilian/"
    # fnames = [ path+fname for fname in os.listdir(path) if fname[-4:]=="html" ][:5]
    # for fname in fnames:
    #     htmlContent = codecs.open(fname,'rb','utf-8').read()
    #     print '=='*20,fname
    #     print "basic:"
    #     result1 = test.parser_basic(htmlContent)
    #     print json.dumps(result1,ensure_ascii=False,indent=4)
    #
    #     print 'detail'
    #     result2 = test.parser_detail(htmlContent)
    #     print json.dumps(result2,ensure_ascii=False,indent=4)
    #     print "\n"
    result2 = test.parser_detail(fname=None, url="http://jobs.zhaopin.com/120072290283605.htm?ssidkey=y&ss=201&ff=03")
    print json.dumps(result2, ensure_ascii=False, indent=4)
    # result2 = test.parser_detail(fname=None,url="http://jobs.zhaopin.com/681043522264837.htm")
    # print json.dumps(result2,ensure_ascii=False,indent=4)

    # 生成又标签或者无标签的数据，用作CNN的数据集
    # generate_text_withlabel(result, jdfrom="zhilian")
    # generate_text_withoutlabel(result2,jdfrom = "zhilian")