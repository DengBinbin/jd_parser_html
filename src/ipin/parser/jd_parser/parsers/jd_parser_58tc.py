#!/usr/bin/env python
# coding=utf-8
import sys,re,codecs,jieba
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
from bs4 import BeautifulSoup
from urllib2 import urlopen
from collections import OrderedDict,Counter
from base import JdParserTop
from utils.path import *
import datetime
from utils.util import *
reload(sys)
sys.setdefaultencoding('utf-8')


class JdParser58tc(JdParserTop):
    """
    对58 同城 html 进行jd解析
    """
    def __init__(self):
        JdParserTop.__init__(self)



    def preprocess(self,htmlContent,fname=None,url=None):
        """
        预处理，改换换行符等
        """
        self.refresh()
        self.result["jdFrom"] = "58.com"


        html = ""
        if url!=None:
            html = urlopen(url).read()
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read()
        
        if len(html)<60:
            raise Exception("input arguments error")

        self.html= re.sub("<br.*?/?>|<BR.?/?>","\n",html)
        #self.html = self.replace(html)
        #self.html =html
        self.soup = BeautifulSoup(self.html,"lxml")

        self.jdsoup = self.soup.find("div","wb-main").find("div","posCont")
        self.compsoup = self.jdsoup.find("div","posSum")
        self.jdbasic_soup = self.jdsoup.find("div","xq").find_all("li","condition") if self.jdsoup.find("div","xq") else []


        jdstr = self.jdsoup.find("div",{"id":"zhiwei"})
        # self.jdstr = jdstr.find("div","posMsg borb").get_text().strip() if jdstr else ""
        #zhangzq @20160312
        if jdstr.find("div","posMsg borb").find_all("p"):
            self.jdstr = '\n'.join([item.get_text() for item in jdstr.find("div","posMsg borb").find_all("p")])
        else:
            self.jdstr = jdstr.find("div","posMsg borb").get_text().strip() if jdstr else ""




        self.linelist = [ line.strip() for line in self.SPLIT_LINE.split(self.jdstr) if len(line)>1]
    


    def regular_incname(self):
        find_incname_soup = self.compsoup.find("a","companyName")
        self.result['jdInc']["incName"] = find_incname_soup.get_text().strip()
        #self.result['jdInc']["incUrl"] = find_incname_soup.get("href","")



    def regular_inc_tag(self):
        find_comptag = self.compsoup.find("div","compMsg clearfix")      
        if not find_comptag:
            return 

        inc_tags = find_comptag.find("ul").find_all("li") if find_comptag.find("ul") else []
      
        for tag in inc_tags:
            
            key = tag.find("span").get_text()
      
            if re.search(u"行业",key):
                self.result['jdInc']['incIndustry'] = re.sub(u"行业：|\s","",tag.get_text().strip())
            elif re.search(u"性质",key):
                self.result['jdInc']["incType"] = re.sub(u"性质：|\s","",tag.get_text().strip())

            elif re.search(u"规模",key):
                self.result['jdInc']["incScale"] = re.sub(u"规模：|\s","",tag.get_text().strip())
        
        find_incname_soup = self.compsoup.find("a","companyName")
        incURL = find_incname_soup.get("href","")
        #add incLocation
       #dengbinbin @2016.03.31
       #公司地址里面有一些没有地址信息，例如德邦
        html = ""
        if incURL!=None:
            html = urlopen(incURL).read()
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read()
        
        if len(html)<60:
            raise Exception("input arguments error")
            
        html= re.sub("<br.*?/?>|<BR.?/?>","\n",html)
        soup = BeautifulSoup(html,"lxml")
        if soup.find("div","wb-main"):        
            jdsoup = soup.find("div","wb-main").find("div","wrap")          
            compsoup = jdsoup.find("table","")
            find_incLocation_soup = compsoup.find("td","adress")
            incLocation = find_incLocation_soup.get_text().strip().split('\n')[0] if find_incLocation_soup.get_text().strip()!=u"查看地图" else ""
            self.result['jdInc']["incLocation"]=incLocation
        
            


        find_inc_intro = self.soup.find("div",{"class":"compIntro","id":"gongsi"})

        if find_inc_intro and find_inc_intro.find("p"):

            self.result['jdInc']["incIntro"] = find_inc_intro.find("p").get_text().strip()
            self.result['jdInc']["incIntro"] = re.sub(u'\[查看全部\]\[收起\]$',u'',self.result['jdInc']["incIntro"])

        if len(self.result['jdInc']["incUrl"])<3 and self.result['jdInc']["incIntro"]:
            find_url = self.INC_URL.search(self.result['jdInc']["incIntro"])
            if find_url:
                self.result['jdInc']["incUrl"] = re.search(u"[\d\w\.:/_\-]+",find_url.group()).group()


    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """
        find_pubtime = self.jdsoup.find("div","headCon")
        if find_pubtime:
            # self.result["pubTime"] = find_pubtime.find("li").find_next("span").get_text().strip()
            pubtime=find_pubtime.find("li").find_next("span").get_text().strip()
            if pubtime==u'今天':
                self.result["pubTime"]=datetime.datetime.now().strftime("%Y-%m-%d")
                return
            days_ago= re.findall(u'(\d+)\s+天前',pubtime)
            if days_ago:
                day_num= int(days_ago[0].strip())
                pub_day=datetime.datetime.now() - datetime.timedelta(days=day_num)
                pub_time=pub_day.strftime("%Y-%m-%d")
                self.result["pubTime"] = pub_time



    def regular_jobname(self):

        jobname = self.jdsoup.find('h1').get_text() if self.jdsoup.find("h1") else "None"

        self.result['jdJob']['jobPosition'] = re.sub("\s+","",jobname.strip())



    def regular_job_tag(self):
        if self.jdbasic_soup:
            for li in self.jdbasic_soup:
               
                if re.search(u"工作性质",li.span.get_text()):
                    self.result['jdJob']["jobType"] = li.get_text()
                elif re.search(u"招聘人数|职位",li.span.get_text()):
                    find_jobnum =  re.search(u"\d+-\d+人|\d+人",li.get_text().strip())
                    if find_jobnum:
                        self.result['jdJob']['jobNum'] = find_jobnum.group()
                    #add jobCate 
                    #dengbinbin @ 2016.03.29                        
                    self.result['jdJob']["jobCate"] = li.get_text().strip().split('\n')[1].strip()
                elif re.search(u"类别",li.span.get_text()):
                    self.result['jdJob']["jobCate"] = li.get_text()

        find_job_type = re.search(u"实习|兼职",self.result["jdJob"]["jobPosition"])
        if find_job_type:
            self.result['jdJob']["jobType"] = find_job_type.group()


    def regular_sex(self):
        """
        @return: 不限, 男, 女
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
        degree = ""
        if self.jdbasic_soup:
            for li in self.jdbasic_soup:
                if re.search(u"学历要求",li.get_text()):
                    degree = re.sub(u"学历要求：|\s","",li.find("div","fl").get_text().strip())

        self.result['jdJob']['jobDiploma'] = degree



    def regular_exp(self):

        expstr = ""
        if self.jdbasic_soup:
            for li in self.jdbasic_soup:
                if re.search(u"工作年限",li.get_text()):
                    expstr = re.sub(u"工作年限：|\s","",li.find("div","fl").get_text())
                    break
        self.result['jdJob']['jobWorkAge'] = expstr
    

    def regular_skill(self):
        res = []
        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.lower()
                if word in self.skilldic:
                    res.append(word)
        res =[w[0] for w in Counter(res).most_common(5)]
        self.result['jdJob']["skillList"] = res



    def regular_workplace(self):
        locstr = ""
        if self.jdbasic_soup:
            for li in self.jdbasic_soup:
                if re.search(u"地址",li.span.get_text()):
                    addr_list=[i.get_text() for i in li.find_all("span",limit=3)[2].find_all("a")]
                    locstr = li.find_all("span",limit=3)[1].get_text().strip()
                    break

        self.result['jdJob']['jobWorkLoc'] = re.sub("\s","",locstr) if re.sub("\s","",locstr) else ""
        if len(addr_list)>1:
            self.result['jdJob']['jobWorkCity'] =  '-'.join(addr_list[:2])
        else:
            self.result['jdJob']['jobWorkCity'] =  '-'.join(addr_list)
        
    




    def regular_pay(self):
        
        paystr = ""
        if self.jdbasic_soup:
            for li in self.jdbasic_soup:
                if re.search(u"薪资|薪酬",li.span.get_text()):
                    paystr = li.find_next("span","salaNum").get_text()
                    break

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
        self.result['jdJob']['certList'] = res.split("|")

    


    def regular_demand(self):
        
        jdstr = self.jdstr
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
        self.result['jdJob']['workDemand'] = '\n'.join(res)

    def regular_duty(self):

        jdstr = self.jdstr
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
        self.result['jdJob']['workDuty'] = '\n'.join(res)



    def regular_benefit(self):

        res = []
       
        benefit_tags = []
        find_benefit = self.jdsoup.find("div","xq").find("li","condition hierarchy")
        if find_benefit:
            benefit_tags = find_benefit.find_all("li")
        
        for tag in benefit_tags:
            if tag.find("span"):
                res.append(tag.find("span").get_text().strip())

        self.result['jdJob']['jobWelfare'] = '\n'.join(res)


    def regular_other(self):
        jdstr = self.jdstr.strip()
        self.result["jdJob"]['jobDesc'] = jdstr


    
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


if __name__ == "__main__":
    import os,json

    test = JdParser58tc()
    path = jd_path+'58tc/'
    fnames = [ path + fname for fname in os.listdir(path) if fname.endswith(".html")]
    
    for fname in fnames:
        print '=='*20,fname
       
        htmlContent = codecs.open(fname,'rb','utf-8').read()
       
        result1 = test.parser_basic(htmlContent,fname=None,url=None)
        print json.dumps(result1,ensure_ascii=False,indent=4)

        print 'detail'
        result2 = test.parser_detail(htmlContent)
        print json.dumps(result2,ensure_ascii=False,indent=4)
        # 生成又标签或者无标签的数据，用作CNN的数据集
        # generate_text_withlabel(result2, jdfrom="51tc")
        # generate_text_withoutlabel(result2,jdfrom = "58tc")

