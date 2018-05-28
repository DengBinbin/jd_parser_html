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



class JdParserJobUI(JdParserTop):
    """
    http://www.jobui.com/job/105454857/
    对结合html，对职友集 进行解析
    """
    def __init__(self):
        JdParserTop.__init__(self)
        


    def preprocess(self, htmlContent,fname=None,url=None):
        """
        预处理，改换换行符等
        """
        self.refresh()
        self.inc_url=""
        self.welfarw_url=""

        html = ""
        
        if url!=None:
            html = urlopen(url).read()
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read()
       
        if len(html)<60:
            raise Exception("input arguments error")
        self.soup = BeautifulSoup(html,"lxml")
        self.jdsoup = self.soup.find("div",{"class":"jk-box jk-matter j-job-detail"})
        
        find_comp = self.soup.find("div","aright")
        if find_comp and find_comp.find("span",text=re.compile(u"行业：")):
            self.compsoup = self.soup.find("div","aright").find("span",text=re.compile(u"行业：")).find_previous("ul")
        else:
            self.compsoup = ""
        jdstr = self.jdsoup.find("div","hasVist cfix sbox").get_text().strip()
        self.jdstr = self.CLEAN_TEXT.sub(" ",jdstr)

        self.linelist = [ line.strip() for line in self.SPLIT_LINE.split(self.jdstr) if len(line)>1]
    
        # 先存储下来，方便解析基本字段
        self.jdbasic_soup = self.jdsoup.find("ul","laver cfix").find_all("li")
        
        find_inc_name = self.soup.find("h1",{"id":"companyH1"})
        if find_inc_name:
            self.jd_type = 2  # jobui新版本 2016-02-19
        else:
            self.jd_type = 1
        self.result["jdFrom"]='jobui'
        #print self.jd_type   2


    def regular_incname(self):
        incname = "None"
        
        # 新版本jobui
        if self.jd_type == 2:
            self.result["jdInc"]["incName"] = self.soup.find("h1",{"id":"companyH1"}).get_text(strip=True)
            self.inc_url="http://www.jobui.com"+self.soup.find("div","middat cfix").find_all("a")[0].get("href")            
            self.welfarw_url =self.inc_url+'salary/'            
            return 
                
        
        # 侧边没有企业信息的情况
        if not self.compsoup and self.jdsoup.find_previous("div","sbox"):
            incname = self.jdsoup.find_previous("div","sbox").find("a","fs18 sbox f000 fwb block")
            if incname:
                self.result["jdInc"]['incName'] = incname.get_text().strip()
            return 
        
        # 正文上面寻找
        incname = self.compsoup.find_previous('h2').get_text()
        if re.search(u"概况",incname):
            incname = self.jdsoup.find_previous("div","sbox").find("a","fs18 sbox f000 fwb block").get_text()
        self.result["jdInc"]['incName'] = incname.strip()


    def regular_inc_tag(self):
        inc_tags = self.compsoup.find_all("span") if self.compsoup else []
        
        inc_tags2 = self.jdsoup.find_next("div","cfix jk-box jk-matter")
        if inc_tags2 and inc_tags2.find("dl","dlli"):
            inc_tags.extend(inc_tags2.find("dl","dlli").find_all("dt"))
        for tag in inc_tags:
            key = tag.get_text()
            if re.search(u"性质：",key):
                self.result["jdInc"]["incType"] = tag.find_next_sibling("span").get_text().strip()
            elif re.search(u"行业：",key) and tag.find_next_sibling("span"):
                self.result["jdInc"]['incIndustry'] = tag.find_next_sibling("span").get_text().strip()
            elif re.search(u"规模：",key) and tag.find_next_sibling("span"):
                self.result["jdInc"]["incScale"] = tag.find_next_sibling("span").get_text().strip()
            elif re.search(u"联系",key) and tag.find_next_sibling("dd"):
                self.result["jdInc"]["incContactInfo"] = tag.find_next_sibling("dd").get_text().strip()
                return
            elif re.search(u"地址：",key) and tag.find_next_sibling("dd"):
                self.result["jdInc"]["incLocation"] = tag.find_next_sibling("dd").get_text().strip().split('（')[0].split('(')[0]
                self.result["jdInc"]["incZipCode"] = tag.find_next_sibling("dd").get_text().strip().split(u"：",1)[1].split(u")",1)[0] if len(tag.find_next_sibling("dd").get_text().strip().split(u"：",1))==2 else ""
            elif re.search(u"网站：",key) and tag.find_next("a"):
                self.result["jdInc"]["incUrl"] = tag.find_next("a").get('href','None').strip()
        




    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """
        
        tmpsoup = self.jdsoup.find("div","cfix").find_all("dt")
        if tmpsoup:
            for tag in tmpsoup:
                if re.search(u"发布时|截止日",tag.get_text()):
                    self.result["pubTime"] = tag.find_next("dd").get_text().strip()
                
                elif re.search(u"截止时间|截止日",tag.get_text()):
                    self.result["jdJob"]["jobEndTime"] = tag.find_next("dd").get_text().strip()

                elif re.search(u"来源网站",tag.get_text()):
                    self.result["jdFrom"] = tag.find_next("dd").get_text().strip()


    def regular_jobname(self):

        if self.jd_type == 2:
            find_jobname = self.jdsoup.find("h1")
            self.result["jdJob"]['jobPosition'] = re.sub("\s+","",find_jobname.get_text(strip=True).lower())
        else:
            find_jobname = self.soup.find("body").find("div","head cfix")
            if find_jobname:
                self.result["jdJob"]["jobPosition"] = find_jobname.find("h1").get_text(strip=True)



    def regular_job_tag(self):
        
        if self.jd_type == 1:
            for li in self.jdbasic_soup:
                key = li.span.get_text()
                if re.search(u"职位类型",key):
                    self.result["jdJob"]["jobType"] = li.get_text().strip().replace(key,"")
                elif re.search(u"招聘人数",key):
                    self.result["jdJob"]['jobNum'] = li.get_text().strip().replace(key,"")
                elif re.search(u"类别",key):
                    self.result["jdJob"]["jobCate"] = li.get_text().strip().replace(key,"")

        elif self.jd_type == 2:
            find_job_tags = self.jdsoup.find("ul","laver cfix")
            if find_job_tags:
                tags = find_job_tags.find_all("li")
                for tag in tags: 
                    key = tag.get_text()
                    if re.search(u"工作地点",key):
                        self.result["jdJob"]['jobWorkCity'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"工作经验",key):
                        self.result["jdJob"]['jobWorkAge'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"职位类型",key):
                        self.result["jdJob"]['jobType'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"薪资",key):
                        self.result["jdJob"]['jobSalary'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"学历要求",key):
                        self.result["jdJob"]['jobDiploma'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"公司规模",key):
                        self.result["jdJob"]['incScale'] = tag.get_text(strip=True).split(u"：",1)[1]
                    elif re.search(u"招聘人数",key):
                        self.result["jdJob"]['jobNum'] = tag.get_text(strip=True).split(u"：",1)[1]



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
        agestr=u"不限"
        for line in self.linelist:
            if re.search(u"\d+后",line):continue
            if self.AGE.search(line):
                findage = re.search(u"\d{2}?\s?[\-　－到至]?\s?\d{2}周?岁|(至少|不低于|不超过|不大于|大概|大约|不少于|大于)\d+周?岁|\d+周岁(以上|左右|上下)",line)
                if findage:
                    agestr = findage.group()

        self.result["jdJob"]['age'] = agestr


    def regular_major(self):
        res = set()
        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.lower()
                if word in self.majordic:
                    res.add(word)
            if res:
                break

        self.result["jdJob"]["jobMajorList"] = list(res)



    def regular_degree(self):
        degree = ""
        for li in self.jdbasic_soup:
            key = li.span.get_text()
            if re.search(u"学历",key):
                degree = li.get_text().strip()
                break

        self.result["jdJob"]['jobDiploma'] = re.sub(u"学历要求：|\s+","",degree)
        return degree


    
    def regular_degree_detail(self):
        res = self.regular_degree()

        if not res:
            res = []
            for line in self.linelist:
                for word in jieba.cut(line):
                    if word in self.degreedic:
                        res.append(word)

            self.result["jdJob"]["jobDiploma"] = " | ".join(res)
        else:
            self.result["jdJob"]['jobDiploma'] = re.sub(u"学历要求：|\s+","",res)



    def regular_exp(self):

        expstr = ""
        for li in self.jdbasic_soup:
            if re.search(u"工作经验",li.span.get_text()):
                expstr = li.get_text()
                break

        self.result["jdJob"]['jobWorkAge'] = re.sub(u"工作经验：|\s+","",expstr)
    

    def regular_skill(self):
        res = []
        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.lower()
                if word in self.skilldic:
                    res.append(word)
        res =[w[0] for w in Counter(res).most_common(5)]
        self.result["jdJob"]["skillList"] = res



    def regular_workplace(self):
        res = ""
        for li in self.jdbasic_soup:
            key = li.span.get_text()
            if re.search(u"工作地点",key):
                res = li.get_text().strip().replace(key,"")
                break
        
        # self.result["jdJob"]['jobWorkLoc'] = res



    def regular_pay(self):

        paystr = ""
        for li in self.jdbasic_soup:
            key = li.span.get_text()
            if re.search(u"薪资",key):
                paystr = li.get_text().strip().replace(key,"")
       
        self.result["jdJob"]['jobSalary'] = paystr.replace(u"k","000")

    
    def regular_cert(self):
        res = []
        for line in self.linelist:
            findcert = self.CERT.search(line)
            if findcert and len(findcert.group())<6 and not re.search(u"保证",findcert.group()):
                res.append(findcert.group())
            else:
                findcert = re.search(u"有(.{2,5}证)",line)
                if findcert and not re.search(u"保证",findcert.group()):
                    res.append(findcert.group(1))
        res = re.sub(u"[通过或以上至少]","","|".join(res))
        self.result["jdJob"]['certList'] = res.split("|")

    


    def regular_demand(self):
        jdstr = self.jdsoup.find("div","hasVist cfix sbox").get_text()
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
        self.result["jdJob"]['workDemand'] = '\n'.join(res)

    def regular_duty(self):

        jdstr = self.jdsoup.find("div","hasVist cfix sbox").get_text()
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
        self.result["jdJob"]['workDuty'] = '\n'.join(res)



    def regular_benefit(self):

        find_welfare_tags = self.soup.find("div","company-tab-box sbox")
        if find_welfare_tags and find_welfare_tags.find("span"):
            tags = find_welfare_tags.get_text("|",strip=True).split("|")
            self.result["jdJob"]["jobWelfare"] = ("\n".join(tags)).replace("...","")
        else:
            self.result["jdJob"]['jobWelfare'] = ""


    def regular_other(self):
        jdstr = self.jdsoup.find("div","hasVist cfix sbox").get_text()
        self.result["jdJob"]["jobDesc"] = jdstr.strip()
    


    #公司介绍 zhangzq 20160314
    def get_inc_desc(self):
        if self.inc_url:
            try:
                html = urlopen(self.inc_url).read()
                soup = BeautifulSoup(html,"lxml")
                tag = soup.find("dl",{"class":"j-edit hasVist dlli mb10"}).find_all("dt")
            except:
                return
            for t in tag:
                if re.search(u"公司信息：",t.get_text()):
                    self.result["jdInc"]["incType"]=t.find_next("dd").get_text().split("/")[0]
                    if len(t.find_next("dd").get_text().split("/"))>1:
                        self.result["jdInc"]["incScale"] = t.find_next("dd").get_text().split("/")[1]
                elif re.search(u"公司行业：",t.get_text()):
                    self.result["jdInc"]["incIndustry"]=t.find_next("dd").get_text().strip()
            inc_desc =soup.find("p",{"class":"mb10 cmp-txtshow"}).get_text()
            self.result["jdInc"]["incIntro"]=inc_desc


    #薪酬福利
    def get_welfare(self):

        if self.welfarw_url:
            try:
                html = urlopen(self.welfarw_url).read()
                soup = BeautifulSoup(html,"lxml")
                tag = soup.find("div",{"class":"comTab sbox"})
            except:
                return
            if tag:
                self.result["jdJob"]['jobWelfare']= tag.get_text('\n')

    def parser_basic(self, htmlContent=None,fname=None,url=None):
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.get_inc_desc()

        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_degree()
        self.regular_exp()
        self.regular_workplace()
        self.regular_pay()
        #self.regular_benefit()
        self.get_welfare()
        self.regular_other()



        return self.result



    def parser_detail(self, htmlContent=None,fname=None,url=None):
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.get_inc_desc()

        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_sex()
        self.regular_age()
        self.regular_major()
        self.regular_degree_detail()
        self.regular_exp()
        self.regular_skill()
        self.regular_workplace()
        self.regular_pay()
        self.regular_cert()
        self.regular_demand()
        self.regular_duty()
        #self.regular_benefit()
        self.get_welfare()
        self.regular_other()


        return self.result

    


    def ouput(self):

        for k,v in self.result.iteritems():
            print  k
            if isinstance(v,dict):
                for kk,vv in v.items():
                    print kk
                    print vv
            else:
                print v
            print '--'*20
                



if __name__ == "__main__":
    import os,json
    test = JdParserJobUI()
    path = jd_path+'jobui/'
    # fnames = [ path+fname for fname in os.listdir(path) if fname.endswith(".html") ][:2]
    # for fname in fnames:
    #     print '=='*20,fname
    #     htmlContent = codecs.open(fname,'rb','utf-8').read()
    #
    #     print 'detail'
    #     result2 = test.parser_detail(htmlContent)
    #     print json.dumps(result2,ensure_ascii=False,indent=4)
    #     print ''
    
    result2 = test.parser_detail( url = "http://www.jobui.com/job/78809345/" )
    print json.dumps(result2,ensure_ascii=False,indent=4)
    # 生成又标签或者无标签的数据，用作CNN的数据集
    # generate_text_withlabel(result2, jdfrom="jobui")
    # generate_text_withoutlabel(result2,jdfrom = "jobui")

