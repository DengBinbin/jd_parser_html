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
from utils.util import *
from utils.path import *



class JdParserHighPin(JdParserTop):
    """
    对智联卓聘jd进行解析
    """
    def __init__(self):
        JdParserTop.__init__(self)

    def preprocess(self,htmlContent,fname=None,url=None):

        self.refresh()
        self.result["jdFrom"] = "highpin"

        html = ""
        if url!=None:
            html = urlopen(url).read().decode("utf-8")
        elif htmlContent:
            html = htmlContent
        elif fname:
            html = open(fname).read().decode("utf-8")
        
        if len(html)<60:
            raise Exception("input arguments error")

        self.soup = BeautifulSoup(html,"lxml")

        self.jdsoup = self.soup.find("div",{"id":"main"})
        self.jdtitles = self.jdsoup.find_all("h5","v-title-con")

        
        find_demandsoup = ""
        for line in self.jdtitles:
            if re.search(u"职位描述",line.get_text()):
                find_demandsoup = line
                break
        if find_demandsoup:
            self.demandsoup = find_demandsoup.find_next_sibling("div")
            self.linelist = self.demandsoup.get_text(";",strip=True).split(";")
            self.jdstr = '\n'.join(self.linelist)
        else:
            self.demandsoup = ""
            self.linelist = []
            self.jdstr = ""



    def regular_incname(self):
        # 在 regular_inc_tag 中抽取，改为对公司介绍进行抽取
        tmpsoup = ""
        
        for line in self.jdtitles:
            if re.search(u"公司介绍",line.get_text()):
                tmpsoup = line.find_next("p","view-aboutUs")
                break
        
        if tmpsoup:
            self.result["jdInc"]["incIntro"] = tmpsoup.get_text(strip=True)


    def regular_inc_tag(self):

        tmpsoup = ""
        
        for line in self.jdtitles:
            if re.search(u"招聘公司",line.get_text()):
                tmpsoup = line.find_next("ul","view-ul")
                break
        if tmpsoup:
            tags = tmpsoup.find_all("li")
            for tag in tags:
                if re.search(u"公司名",tag.span.get_text()):
                    self.result['jdInc']["incName"] = tag.get_text("|",strip=True).split("|")[-1]
                    # if tag.find("a"):
                    #     self.result['jdInc']["incUrl"] = tag.find("a").get("href","")
                elif re.search(u"所属行业",tag.span.get_text()):
                    self.result['jdInc']["incIndustry"] = tag.get_text("|",strip=True).split("|")[-1]
                elif re.search(u"公司性质",tag.span.get_text()):
                    self.result['jdInc']["incType"] = tag.get_text("|",strip=True).split("|")[-1]
                elif re.search(u"公司规模",tag.span.get_text()):
                    self.result['jdInc']["incScale"] = tag.get_text("|",strip=True).split("|")[-1]
                elif re.search(u"公司地址",tag.span.get_text()):
                    self.result['jdInc']["incLocation"] = "".join(tag.get_text("|",strip=True).split("|")[1:])
                    self.result['jdInc']["incLocation"] = self.result['jdInc']["incLocation"].replace(u"查看地图","")

    def regular_pubtime(self):
        """
        发布时间 & 截止时间
        """
        # 在基本信息 job_tag 中处理

        self.result["pubTime"] = ""



    def regular_jobname(self):
        """
        包括福利亮点
        """
        find_jobname = self.jdsoup.find("h1","postitonName")
        if find_jobname:
            jobname = find_jobname.find("span").get_text().strip()
            self.result['jdJob']["jobPosition"] = jobname
            find_welfare = find_jobname.find("div","labelList")
            if find_welfare:
                tags = [ tag.get_text() for tag in find_welfare.find_all("span") ]
                self.result['jdJob']["jobWelfare"] = "\n".join(tags)
                


    def regular_job_tag(self):

        tmpsoup = ""
        for line in self.jdtitles:
            if re.search(u"基本信息",line.get_text()):
                tmpsoup = line.find_next_siblings("ul","view-ul")
                break
        if tmpsoup:
            tags = [ tag for tmpul in tmpsoup for tag in tmpul.find_all("li") ]
            for tag in tags:
                if re.search(u"职位类",tag.get_text()):
                    # jobCate =tag.get_text("|",strip=True).split("|")[-1]
                    # res["jobCate"] = re.sub(u'\.\.\.',u'',jobCate)
                    self.result['jdJob']["jobCate"] = tag["title"]
                elif re.search(u"所属部门",tag.span.get_text()):
                    self.result['others']["jobDepartment"]=tag["title"]
                    #
                    # jobDepartment=''.join(tag.get_text("|",strip=True).split("|")[1:])
                    # self.result_job["others"]["jobDepartment"] =re.sub(u'\.\.\.',u'',jobDepartment)


                elif re.search(u"工作地点",tag.span.get_text()):
                    self.result['jdJob']["jobWorkCity"] = ''.join(tag.get_text("|",strip=True).split("|")[1:])

                elif re.search(u"发布时间",tag.span.get_text()):
                    self.result["pubTime"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"截止时间",tag.span.get_text()):
                    self.result['jdJob']["jobEndTime"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"汇报对象",tag.span.get_text()):
                    self.result['others']["jobReport"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"下属人数",tag.span.get_text()):
                    self.result['others']["jobSubSize"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"招聘人数",tag.span.get_text()):
                    self.result['jdJob']["jobNum"] = tag.get_text("|",strip=True).split("|")[-1]


    
    def regular_pay(self):
        
        tmpsoup = ""
        for line in self.jdtitles:
            if re.search(u"薪酬信息",line.get_text()):
                tmpsoup = line.find_next_sibling("ul")
                break

        if tmpsoup:
            res = tmpsoup.find("li").get_text(strip=True)
            self.result['jdJob']["jobSalary"] = res
   


    def regular_sex(self):
        find_sex = re.search(u"男|女|性别不限|不限男女",self.jdstr)
        if find_sex:
            self.result['jdJob']["gender"] = find_sex.group()



    def regular_skill(self):
        res = {}

        for line in self.linelist:
            for word in jieba.cut(line):
                word = word.strip().lower()
                if word in self.skilldic:
                    res[word] = res.get(word,0) + 1
        sorted_res = sorted(res.items(),key=lambda d:d[1],reverse=True)
        res = [ word for word,count in sorted_res[:5] ]

        self.result['jdJob']["skillList"] = res


    
    def regular_cert(self):
        res = []
        linelist = [line for line in re.split(u"[\s，。；、]",self.jdstr) if 3<len(line)<10 ]
        for line in linelist:
            findcert = re.search(u"(\S+证书|CET-\d|普通话|英语|口语|.语|日文|雅思|托福|托业)(至少)?(通过)?[\d一二三四五六七八九]级[及或]?(以上)?|(英语)?CET-\d级?(以上)?|职业资格|律师证|会计证",line)
            if findcert:
                res.append(findcert.group())
            else:
                findcert = re.search(u"有(.+证)书?",line)
                if findcert:
                    res.append(findcert.group(1))
                else:
                    findcert = re.search(u"有.+资格",line)
                    if findcert:
                        res.append(findcert.group())

        self.result['jdJob']['certList'] = res
    


    def regular_demand(self):
        res = "" 
        if self.demandsoup:
            find_demand = self.demandsoup.find("div","v-p-lable",text=re.compile(u"任职资格"))
            if find_demand:
                res = find_demand.find_next("div").get_text(strip=True)

        self.result['jdJob']['workDemand'] = res



    def regular_duty(self):
        res = ""
        if self.demandsoup:
            find_duty = self.demandsoup.find("div","v-p-lable",text=re.compile(u"岗位职责"))
            if find_duty:
                res = find_duty.find_next("div").get_text(strip=True)

        self.result['jdJob']['workDuty'] = res



    def regular_other(self):

        tmpsoup = ""
        for line in self.jdtitles:
            if re.search(u"其他要求",line.get_text()):
                tmpsoup = line.find_next_sibling("div","add-div800 clearfix")
                break
         
        if tmpsoup:
            tags = tmpsoup.find_all("li")
            tags.extend( tmpsoup.find_next_siblings("div","clearfix") )
            res = {}
            for tag in tags:
                if re.search(u"工作经验",tag.get_text()):
                    self.result['jdJob']["jobWorkAge"] = "".join(tag.get_text("|",strip=True).split("|")[1:])

                elif re.search(u"学历要求",tag.get_text()):
                    self.result['jdJob']["jobDiploma"] = tag.get_text("|",strip=True).split("|")[-1]
                
                elif re.search(u"年龄",tag.get_text()):
                    self.result['jdJob']["age"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"是否统招全日制",tag.get_text()):
                    self.result['others']["isFullTime"] = tag.get_text(strip=True)[8:]
                
                elif re.search(u"海外经历",tag.get_text()):
                    self.result['others']["overSea"] = tag.get_text("|",strip=True).split("|")[-1]

                elif re.search(u"专业要求",tag.get_text()):
                    self.result['jdJob']["jobMajorList"] = [tag.get_text("|",strip=True).split("|")[-1]]

                elif re.search(u"语言要求",tag.get_text()):
                    self.result['others']["language"] = tag.get_text("|",strip=True).split("|")[-1]
                
                elif re.search(u"补充说明",tag.get_text()):
                    self.result['others']["jdRemedy"] = "".join(tag.get_text("|",strip=True).split("|")[1:])
       
        find_jobreport = self.jdsoup.find("h6",text=re.compile(u"汇报对象")) 
        self.result['others']["posType"] = u"企业JD" if find_jobreport else u"猎头JD"
        # find_jobreport = self.jdsoup.find("h6",text=re.compile(u"汇报对象"))
        # if find_jobreport:
        #     self.result['others']["jobReport"] = find_jobreport.find_next("div").find("ul").get_text().strip()


        self.result['jdJob']["jobDesc"] = self.jdstr




    def parser_basic(self,htmlContent=None,fname=None,url=None):
        """
        页面简单抽取
        """
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_pay()
        # self.regular_duty()
        # self.regular_demand()
        self.regular_other()
        
        return self.result


    def parser_detail(self,htmlContent=None,fname=None,url=None):
        """
        进一步简单的语义解析，卓聘一样
        """
        
        self.preprocess(htmlContent,fname,url)
        self.regular_incname()
        self.regular_inc_tag()
        self.regular_pubtime()
        self.regular_jobname()
        self.regular_job_tag()
        self.regular_sex()
        self.regular_pay()
        self.regular_skill()
        self.regular_cert()
        self.regular_duty()
        self.regular_demand()
        self.regular_other()
        
        return self.result




if __name__ == "__main__":
    import os,json 

    test = JdParserHighPin()
    path = jd_path+'highpin/'
    fnames = [ path+fname for fname in os.listdir(path) ][:0]
    for fname in fnames:
        print '==='*20,fname
        htmlContent = codecs.open(fname,'rb','utf-8').read()
        result1 = test.parser_basic(htmlContent,fname=None)
        print json.dumps(result1,ensure_ascii=False,indent=4)

        print "detail"
        result2 = test.parser_detail(htmlContent)
        print json.dumps(result2,ensure_ascii=False,indent=4)

    result2 = test.parser_detail(url="http://www.highpin.cn/job/b34814.html")
    print json.dumps(result2,ensure_ascii=False,indent=4)
    # 生成又标签或者无标签的数据，用作CNN的数据集
    # generate_text_withlabel(result2, jdfrom="highpin")
    # generate_text_withoutlabel(result2,jdfrom = "highpin")