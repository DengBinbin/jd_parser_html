#!/usr/bin/env python
# coding=utf-8
import numpy as np
import jieba,sys,re
import os
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
reload(sys)
sys.setdefaultencoding('utf-8')
from datetime import datetime,timedelta
from collections import OrderedDict,defaultdict,Counter
import codecs
from copy import deepcopy
from tgrocery import Grocery
from simhash import Simhash
from utils.util import *
from utils.path import *



class JdParserPlain(object):

    def __init__(self):
        self.degreedic = set( line.strip() for line in codecs.open('./data/degrees.txt','rb','utf-8'))  # 载入学历词库
        self.majordic =set( line.strip() for line in codecs.open('./data/majordic.txt','rb','utf-8'))   # 载入专业词库
        self.citydic = set( line.strip() for line in codecs.open("./data/citydic.txt",'rb','utf-8'))    # 载入城市词库
        self.firmnames =set( line.strip() for line in codecs.open('./data/firm.txt','rb','utf-8'))      # 载入公司缩写名库
        self.jobdic = set(line.strip() for line in codecs.open('./data/jobposition.txt','rb','utf-8') ) # 载入招聘职位名库
        self.skills = set( line.strip() for line in codecs.open('./data/skills.txt','rb','utf-8'))
#        self.wordlisttf = pickle.load(open('./data/wordlist.pkl'))  # 出现频率最高的2000个单词
        # self.w2vdict = json.load(open('./data/word2vec_50.json')) # 2000个词的word2vector

        self.clf = Grocery("./jdclf")        # 句子分类器，分为demand，duty，other
        self.clf.load()
        
        self.SEX = re.compile(u"性别不限|性别|男|女")
        self.AGE = re.compile(u"\d+周?岁|年龄")
        self.DEGREE = re.compile(u"(全日制)?(初中|高中|中专|大专|专科|大学专科|中职|本科|大学本科|硕士|研究生|博士|博士后)(.?以上)?")
        self.MAJOR = re.compile(u"\S+(相关专业|专业优先|及其.专业|[类等]专业[优先]?)")
        self.EXP = re.compile(u"工作经验：|工作经[历验]|工作年限|年.{0,4}经[历验]|经[历验].{1,6}年")
        self.PUB_TIME = re.compile(u"(\d+)(天前发布)")
        
        self.INCNAME = re.compile(u"\S+(有限公司|酒店|银行|集团|研究中心|研究所|学校|旅行社|分?公司|研发中心|技术部|事.部|招聘)") 
        self.NOT_INC = re.compile(u"职位|描述|收藏|推荐|地址|邮箱|主页|介绍|欢迎|加入|要求|简介|险一金|奖金|包吃住|社区|厂房|人员|职责") 
        self.INCTAG = re.compile(u"大公司|五百强|全球500强|小公司|成长型公司|创业公司|私有经济|集体经济|集团|外企|已上市|稳定性高|平均年龄\d+岁|妹纸多|学历高|福利待遇好|晋升机会大|民营公司|民营企业|互联网|创业型|国企|央企")

        self.JOBNAME = re.compile(u'\S*(研发工程师|工程师|经理|助理|顾问|前台|秘书|主管|研究员|实习生|操作员|专员|教学人员|技术人员|管理员|业务员|公关|程序员|教师|老师|培训生|\
                                  文员|研究员|策划|主任|总监|设计师|分析师|架构师|摄影师|编辑|BD|游戏UI|Android(开发)?|PHP(开发)?|Python(开发)?|.?(急招|急聘|初级|中级|高级|方向).?[\s）】\)])|\
                                  |行政人事|网店设计|客服|会计|电话销售|外贸跟单|web前端|游戏UI|后.开发|产品运营|商业数据分析')

        self.START_DEMAND = re.compile(u"(岗位要求|应聘条件|任职要求|岗位资格|任职资格|岗位条件|工作要求|任职条件|人员条件|职位.求|职位条件|职位描述|岗位资格|职位资格|具备条件)[:：\s]\
                                       |如果你.{0,10}[:：\s]|我们希望你.{0,12}[:：\s]|(要求|条件)[:：\s]|你需要?具备什么.+[？\?:：\s]|任职资格[:：\s]")
        self.DEMAND = re.compile(u"熟悉|熟练|具有|善于|懂得|掌握|具备|能够|优先|不少于|不超过|至少|团队.作|良好的|工作经验|开发经验|实习经历|能力强|富有|以上学历|经验|喜欢|\
                                 较强的.{2,8}能力|相关专业|相关学历|者优先|精通|了解|及以上|技术全面|.强的责任心|[能有]独立|英文流利")

        self.DUTY = re.compile(u"跟进|协助|负责|配合|其他工作|领导交办的|对.+提供|审核|参与|提出|跟踪|报告|为.+提出|日常.+工作|指导|对.+进行|为.+提供|跟进|拓展|运营|用户|客户|协调|拟写|通过|协同|完成|沟通|需求|秘书.{2,5}翻译")
        self.START_DUTY = re.compile(u"(岗位职责|岗位描述|职位描述|职责描述|任职描述|职位职责|工作职责|工作职能|职位职能|工作内容|实习内容|职位内容)[:：\s]|做这样的事[:：\s]|职责.{0,5}[:：\s]")
        self.PAY = re.compile(u"薪酬|待遇|月薪|薪资|年薪|底薪|\d+k|\d+万|\d+元|工资|报酬|薪水|福利")
        self.BENEFIT = re.compile(u"周休|补助|补贴|假日|餐补|提成|交通补助|食宿|加班工资|期权|年假|领导|扁平化|管理|氛围|空间|休假|月假|带薪|全休|晋升|培训|舒适的|旅游|奖励|过节费|五险一金|奖金|\
        |弹性工作|氛围|成长空间|实训|培训|高薪|前景|旅游|活动|分红")
        
        self.SPLIT_JD = re.compile(u"岗位[【（]?[一二三四五六七八九][】）][:：\s]|(^招聘岗位\S+|岗位\d|岗位[一二三四五六])[:：\s]")
        self.CLEAR_NUM = re.compile(u"^\d[\.: ：。、]|^[\(（【]?\d[\))】\.]")
        self.CLEAR_COLO = re.compile(u"^[\s\.。）（【】，,]|[。；，\.;,]$|^\d[\.]")
        self.SKILL = re.compile(u"精通|了解|熟练|熟悉|掌握|懂得|优先|具备|具有|者优先|擅长|善于|较强的.{2,6}能力|良好的|有.+经验|能力|极强的")
        
        jieba.load_userdict('./data/majordic.txt')
        jieba.load_userdict('./data/skills.txt')
        jieba.load_userdict('./data/firm.txt')
        jieba.load_userdict('./data/degrees.txt')
        jieba.load_userdict('./data/benefits.txt')


        self.jdStr = ""
        self.linelist = []
        self.lineindex = defaultdict(int)
        self.result = OrderedDict() 

    
    # 分句，预处理
    def preprocess(self,jdstr):
        self.result.clear()
        jdstr = re.sub(u"[【】◆　\u25cf\u25c6\u2605]","",jdstr.decode('utf-8'))
        self.linelist = [ line.strip() for line in jdstr.split('\n') if len(line)>1 ]
        self.jdStr = '\n'.join(self.linelist)
        for line in self.linelist:
          #  print self.clf.predict(line),'\t',line
            self.lineindex[re.sub(u"[\s ]+"," ",line)] = 0

    def line2vec(self,line):
        vec = np.zeros(50)
        cnt = 1
        for word in jieba.cut(line):
            if word in self.w2vdict:
                vec += self.w2vdict[word] 
                cnt += 1
        vec = vec/cnt
        return vec

    # 抽取性别要求
    def regular_sex(self):
        """
        不限:0
        男:1
        女:2
        """
        res = set()
        sex = '0'
        for line in self.linelist:
            if self.clf.predict(line)=='demand' or self.DEMAND.search(line):
                findsex = self.SEX.search(line)
                if findsex:
                    getsex = re.search(u"性别不限|男|女",line.replace(u"男女不限",u"性别不限"))
                    if getsex:
                        res.add(getsex.group())
                        break
        if res:
            sexstr = '/'.join(res)
            if re.search(u"男",sexstr):
                sex = '1'
            elif re.search(u"女",sexstr):
                sex = '2'

        self.result['sex'] = sex


    # 抽取年龄要求
    def regular_age(self):
        res = []
        for line in self.linelist:
            if re.search(u'\d{2}后',line):continue
            findage = self.AGE.search(line)
            if findage:
                findage = re.search(u"(\d{2}[\-－到])\d{2}岁|(至少|不低于|不超过|不高于|不大于|大概|大约)?\d+岁|\d+岁(以上|左右|以下)?",line)
                if findage:
                    agestr = findage.group()
                    age = re.findall(u'\d{2}',agestr)
                    age = map(int,age)
                    if len(age)>=2:
                        res = (age[0],age[1])
                    elif len(age)==1:
                        if re.search(u'以上|不低于|至少|大于',line):
                            res = (age[0],100)
                        elif re.search(u"小于|低于|不超过|不得?高于|以下|不大于",line):
                            res = (0,age[0])
                        elif re.search(u"左右|大约|大概",line):
                            res = (age[0]-3,age[0]+3)
                    break
        if len(res)<1:
            res = (0,100)
        self.result['age'] = res
        return res



    # 抽取专业要求
    def regular_major(self):
        res = []
        
        for line in self.linelist:
            findmajor = re.search(u"专业要求[:：\s]",line)
            if findmajor:
                items = self.clean_line(line[findmajor.span()[1]:]).split()
                items = filter(lambda x: x not in self.degreedic and not re.search(u"薪酬|经验|元|\d+|月",x),items)
                res.append(' / '.join(items))
                break

        if not res:
            for line in self.linelist:
                if re.search(u"专业.限|.限专业",line) and not re.search(u"专业优先",line):
                    res.append(u"专业不限")
                    break
                else:
                    findmajor = self.MAJOR.search(line)
                    if findmajor:
                        majoritem = re.split(u'[\s,，;； ]',findmajor.group())
                        for item in majoritem:
                            if re.search(u'学历|年龄|岁|学校|公司|性格|具有|具备|能够|经验|有|毕业|性别|男|女',item):continue
                            if self.BENEFIT.search(line):continue
                            if re.search(u"专业",item) and len(item)<3:continue
                            res.append(self.clean_line(item))
                        break
                        if not res:
                            for majorword in jieba.cut(line):
                                if majorword in self.majordic or majorword[:-2] in self.majordic:
                                    res.append(majorword)

                            if re.search(u"[等及类]?相关专业",self.jdStr) and len(res)==1:
                                res[0]+=u"等相关专业"
        if not res:
            res.append(u"专业不限")

        self.result['major'] = res
        

    # 抽取学历要求
    def regular_degree(self):
        """
        抽查学历信息，先整找关键字，而后再切词，用词典匹配
        """
        # degree=[u'小学',u'初中',u'中专',u'中技',u'高中',u'专科',u'大专',u'本科',u'硕士',u'博士',u'博士后']
        res = set()
        for line in self.linelist:
            finddegree = re.search(u"学历要求[:：\s]",line)
            if finddegree:
                items =self.clean_line(line[finddegree.span()[1]:]).split()
                items = filter(lambda x: not re.search(u"薪酬|经验|元|月|年|\d+",x),items)
                res.add(' / '.join(items))
                break

        if not res:
            for line in self.linelist:
                if re.search(u"学历不限|学历要求不限|不限学历",line):
                    res.add(u"学历不限")
                    break
                else:
                    finddegree = self.DEGREE.search(line)
                    if finddegree:
                        res.add(finddegree.group())
                        break

        # 如果没有匹配到学历的要求信息，就整个文本切词后匹配查找
        if len(res)==0:
            for word in jieba.cut(self.jdStr):
                if word in self.degreedic:
                    res.add(word)
                    break
        
        self.result['degree'] = list(res)[0]



   
    # 抽取工作经验年限要求    
    def regular_exp(self):
        
        cnyear = u"[一二三四五六七八九半两十]年"
        jdStr = self.jdStr

        res = []
        if re.search(u'经[历验]不限|不限[经验]',jdStr):
            res = (0,100)
            return res
        
        for line in self.linelist:
            findexp = self.EXP.search(line)
            if findexp:
                exp = re.search(u"(\d[\-－])?\d{1,2}年|(不少于)?半\d?年|经[历验]\d[\-－]\d{1,2}年",line)
                if not exp:
                    exp = re.search(cnyear,line)
                if exp:
                    expstr = exp.group() # 缩小查找范围
                    expstr = expstr.replace(u"两",u"2").replace(u"十",u"10").replace(u"半",u"0.5").replace(u"三",u"3").replace(u"一",u'1')
                    year = re.findall(u"\d{1,2}",expstr)
                    if not year:
                        continue
                    year = map(int,year)
                    if len(year)>1:
                        res = (year[0],year[-1])

                    elif len(year)==1:
                        if re.search(u'以上|不低于',line):
                            res = (year[0],100)
                        elif re.search(u"不超过|不高于|以下",line):
                            res = (0,year[0])
                        elif re.search(u"大概|大约|左右",line):
                            if year[0]-3<0.001:
                                minyear = 0
                            res = (minyear,year[0]+3)
                    break
        if not res:
            res = (0,100)
        self.result["exp"] = tuple(res)
        return res

    def regular_jobtag(self):
        """
        有关职位标签信息
        """
        res = []
        job_tag = re.search(u"应届生|全职|兼职|实习生|应届毕业生|社招|急招|急聘",self.jdStr)
        if job_tag:
            res.append(job_tag.group())
        
        job_tag = re.search(u"招聘人数[:：]?|招聘[:：\s]|人数[：:\s]",self.jdStr)
        if job_tag:
            jdstr = self.jdStr[job_tag.span()[1]:]
            for line in jdstr.split():
                if len(line.strip())<1:continue
                else:
                    num = re.search(u"(\d+\-)?\d+人?|若干|\d+位",line)
                    if num:
                        res.append(u"招聘人数："+num.group())
                    break

        job_tag = re.search(u"(职能类别|职位标签)[:： ]?",self.jdStr)
        if job_tag:
            jdstr = self.jdStr[job_tag.span()[1]:]
            for line in jdstr.split('\n'):
                if len(line.strip())<3:continue
                else:
                    res.append("职业标签："+line.strip())
                    break
                if len(line)>25:break

        #  根据产品部需求专门切割出包含经验的句子等有关职位标注信息,句子进行更精细化切割
        linelist = [ line for line in re.split(u"[，。；\s]",self.jdStr) if 5<len(line)<15 ]
        for line in linelist:
            if re.search(u"经验",line) and not re.search(u"月薪|地点|日期",line):
                if re.search(u"\d+k|[。？）\)\]]",line):continue
                res.append(self.clean_line(line))
                break

        self.result["job_tag"] = res
        return res

    # 清除句子前的数字和标点符合
    def clean_line(self,line):
        line = self.CLEAR_NUM.sub("",line.strip())
        line = self.CLEAR_COLO.sub("",line)
        return line


    # 抽取工作地点
    def regular_workplace(self):
        res = set() 
        jdstr = self.jdStr
        pos = list(re.finditer(u"(工作地.|上班地.|实习地.|地址|地点)[:：\s]",jdstr))
        if pos:
            jdstr = jdstr[pos[0].span()[1]:]

            for line in jdstr.split():
                if len(line.strip())<2:continue
                if len(line)<26:
                    res.add(line.strip().replace(":","").replace("：",""))
                else:
                    for city in jieba.cut(line):
                        if city in self.citydic and city[:-1] not in res:
                            res.add(city)
                break
        if not res: 
            for city in jieba.cut(jdstr):
                if city in self.citydic and city[:-1] not in res and u"国" not in city:
                    res.add(city)
                    break
        self.result["workplace"] = " / ".join(res)
        return res




    # 抽取证书获奖情况等其他要求
    def regular_cert(self):
        res = set()
        linelist = [line for line in re.split(u"[\s ,。；，]",self.jdStr) if len(line)>3]
        for line in linelist:
            findcert = re.search(u"(\S+证书|CET-\d|普通话|英语|口语|.语|日文|雅思|托福|托业)(至少)?(通过)?[\d一二三四五六七八九]级[及或]?(以上)?|(英语)?CET-\d级?(以上)?|职业资格|律师证|会计证",line)
            if findcert:
                res.add(findcert.group())
            else:
                findcert = re.search(u"有(.+证)书?",line)
                if findcert:
                    res.add(findcert.group(1))
                else:
                    findcert = re.search(u"有.+资格",line)
                    if findcert:
                        res.add(findcert.group())

        self.result['cert'] = re.sub(u"[或及以上]","",' / '.join(res))
        if self.result['cert']:
            self.result['cert'] = self.result['cert'].split(' / ')
        else:
            self.result['cert'] = []

    
    # 利用技能词库抽取相关技能
    def regular_skill(self,num=6):
        res = []
        for line in self.linelist:
            if self.DEMAND.search(line) or self.clf.predict(line)=='demand':
                for word in jieba.cut(line):
                    word = strQ2B(word).lower()
                    if word in self.skills:
                        res.append(word)

        sorted_words = [w[0] for w in Counter(res).most_common(2*num)]
        
        for word in jieba.cut(self.result['job_name']):
            word = strQ2B(word).lower()
            if word in self.skills and word not in sorted_words:
                sorted_words.insert(0,word)

        after_top3 = sorted_words[3:]
        np.random.shuffle(after_top3)
        keywords = sorted_words[:3]+after_top3[:num-3]
        keywords.sort()
        self.result['skill'] = keywords


    # 抽取岗位职责
    def regular_duty(self):
        res = []
        jdStr = self.jdStr
        pos = list(self.START_DUTY.finditer(jdStr))
        if len(pos)>0:
            linelist =[ re.sub("[\s ]+"," ",line) for line in jdStr[pos[-1].span()[1]:].split("\n") if len(line)>1]
            for i in xrange(len(linelist)):
                line = linelist[i]
                if self.START_DUTY.search(line) or self.lineindex[line]==1 or re.search(u".年来|谢谢|请在|公司介绍|举报|收藏|岗位职责|介绍|描述|[\-=\.]{3,}",line):continue
                if re.search(u"要求[:：\s]?|岗位要求",line) and len(line)<6:break
                if re.match(u"\d{1,2}|\u25cf|[\uff0d（\(\-\+]|[a-z][\.、\s]",line.strip()) or self.DUTY.search(line) or self.clf.predict(line)=='duty':
                    res.append(line.strip())
                elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='duty':
                    res.append(line)
                else:
                    break
        if not res:
            for line in self.linelist:
                if re.search(u"粉丝团",line) and len(line)<12:continue
                if self.DUTY.search(line) and self.clf.predict(line) == "duty":
                    if self.lineindex[line]!=1:
                        res.append(line)

        self.result["duty"] ="\n".join(res)
        for line in res:
            self.lineindex[line]=1

        return res


    # 抽取岗位要求
    def regular_demand(self):
        res = []
        jdStr =self.jdStr
        pos = list(self.START_DEMAND.finditer(jdStr))
        if len(pos)>0:
            tmppos = pos[-1].span()[0]
            if re.search(u"具有|具备",jdStr[tmppos-5:tmppos+5]) or re.search(u"证书|证",jdStr[tmppos:tmppos+8]):
                pos.pop()
            if pos:
                linelist =[ re.sub("[\s ]+"," ",line) for line in jdStr[pos[-1].span()[1]:].split("\n") if len(line)>2]
            else:
                linelist = []
            for i in xrange(len(linelist)):
                line = linelist[i]
                if self.START_DEMAND.search(linelist[i]) or re.search(u"谢谢|请在|公司介绍|举报|收藏|\d+k?元|加分",line):continue
                if re.match(u"\d{1,2}|\u25cf|[\uff0d（\(\-\+]|[a-z][\.、\s]",line) or self.DEMAND.search(line) or self.clf.predict(line)=='demand':
                    res.append(line)
                elif i<len(linelist)-1 and self.clf.predict(linelist[i+1])=='demand':
                    res.append(line)
                else:
                    break
        if not res:
            for line in self.linelist:
                if self.lineindex[line]==1 or len(line.split())>6:continue # 如果该句已经被处理过，就不再重复显示
                if self.clf.predict(line)=='demand' or self.DEMAND.search(line):
                    res.append(line.strip())
                    
        self.result['demand'] = '\n'.join(res)
        for line in res:
            self.lineindex[line]=1

        return res
    
    # 招聘的职位名
    def regular_jobname(self):
        res = set()
        jdStr = self.jdStr
        findpos = re.search(u"(招聘岗位|招聘职位|职位名称|岗位名称|岗位[一二三四五六七八九])[：、:\s ]",jdStr)
#        if not findpos:
#            findpos = re.search(u"(职位类别|职位职能)[:：\s ]",jdStr)

        if findpos:
            pos = findpos.span()[1]    
            linelist = jdStr[pos:].split("\n")
            for line in linelist:
                if len(line)<2:continue
                if len(line)>=2 and len(line)<20:
                    if re.search(u"职位描述|查看|地址|工作|分享|举报|下一条|时间|福利|待遇|周末|双休",line):continue
                    res.add(re.sub(u"聘请|高薪诚聘|诚聘|[，。、\d！]+","",line.strip()))
                    break

        # 如果没有匹配到招聘的具体职位信息，就切词后到职位列表去匹配
        if not res:
            for line in self.linelist:
                if re.search(u"招聘|高薪|诚聘",line):continue
                if len(line)<6 and not re.search(u'岗位|岗位内容|工作内容|职责|任职|资格',line) and self.clf.predict(line)=='job_name':
                    res.add(line)
                    break
                findPos = self.JOBNAME.search(line)
                if findPos and len(findPos.group())<20 and not re.match(u'\d',findPos.group()):
                    jobname = findPos.group()
                    res.add(re.sub(u"聘请|高薪诚聘|诚聘|急.|[，。、！]+","",jobname))
                    break
                #   res.add(re.sub(u"\(.+\)|（.+）|【.+】|[，。、\s\d]+|聘请|高薪诚聘|诚聘|急招|","",line.strip()))

        if not res:
            for line in self.linelist:
                for word in jieba.cut(line.lower()):
                    if word in self.jobdic:            
                        res.add(word)
                        self.result["job_name"] = " / ".join(res)
                        return res
        if not res:
            tag = re.search(u"实习生|兼职",self.jdStr)
            if tag:
                res.add(tag.group())
        self.result["job_name"] = strQ2B(" / ".join(res)).lower()
        return res
    
    # 薪酬
    def regular_pay(self):
        paystr = ""
        lagoup =  re.search(u"(\d+[kK][-——]\d+[kK])|(\d{3,5}-\d{3,5}元?/[月日天])|(\d{3,5}-\d{3,5}元)|((\d+[-~]\d+)万.[年月])|底薪\d+(-\d+)?元?|\d{3,5}元(左右|以上)?|年薪\d+万?元(左右|以上)?",self.jdStr) # 针对拉勾网，没有待遇等关键字符
        if lagoup:
            paystr = lagoup.group()
        else:
            findpay = self.PAY.search(self.jdStr)
            if findpay:
                pos = findpay.span()[1]
                jdstr = self.jdStr[max(0,pos-5):min(pos+10,len(self.jdStr))]
                if re.search(u"面议",jdstr):
                    paystr = u"面议"
                else:
                    findpay = re.findall(u"\d{3,7}",jdstr)
                    paystr = "-".join(findpay)

        paystr = paystr.replace(u'k','000').replace(u'K','000').replace(u"万","0000")
        pay = re.findall('\d+',paystr)
        pay = map(int,pay)
        if len(pay)>1:
            res = tuple((pay[0],pay[-1]))
        elif len(pay)==1:
            res = (pay[0],0)
        else:
            res = (0,0)
        self.result['pay'] = res
        return res


    # 抽取薪资福利
    def regular_benefits(self):
        res = []
        jdStr = self.jdStr 
        findpos =list(re.finditer(u"薪酬福利[:：\s]|(福利|待遇)\s?[:：】]",jdStr))
        if not findpos:
            findpos =list(re.finditer(u"(晋升制度|工作环境|职位诱惑|你会获得什么)\s?[？\?:：】]",jdStr))
        if findpos:
            pos = findpos[-1].span()[1]
            linelist = jdStr[pos:].split('\n')
            for line in linelist:
                if len(line.strip())<3:continue
                if re.match(ur"[（(]?\d+",line) or self.BENEFIT.search(line):
                    res.append(line.strip())
                    self.lineindex[line.strip()] = 1
                else:
                    break
        
        if not res:
            for line in jdStr.split():
                if len(line)>1 and re.search(u"带薪|双休|股票期权|五险一金|发展空间|福利|诱惑|休假|薪酬|补助|年假|弹性工作",line):
                    if re.search(u"福利|待遇|诱惑",line) and len(line.strip())<6:continue
                    res.append(line.strip())

        if len(res)==1 and re.search(u"险一金",res[0]) and not re.search(u"[，、]",res[0]):
            res[0] = self.clean_line(' '.join(jieba.cut(res[0])))

        self.result["benefits"] ="\n".join(res)
        return res


    # 抽取发布时间和截止时间
    def regular_pubtime(self):

        pub_time = ""
        end_time = ""
        for line in self.linelist:
            findpos = re.search(u"(发布时间|发布日期|添加时间|刷新日期|有效日期)[:：\s]?",line)  # 发布时间
            if findpos and len(line)>6:
                findtime = re.search(u"\d{2,4}.\d{1,2}.\d{1,2}日?",line[findpos.span()[1]:])
                if findtime:
                    pub_time= findtime.group()
                else:
                    pub_time = line[findpos.span()[1]:]
                self.lineindex[line]=1
            
            findpos = re.search(u"(截止时间|截止日期|有效日期)[:：\s]?",line)  # 发布时间
            if findpos and len(line)>6:
                findtime = list(re.finditer(u"\d{2,4}.\d{1,2}.\d{1,2}日?",line[findpos.span()[1]:]))
                if findtime:
                    end_time= findtime[-1].group()
                else:
                    end_time = line[findpos.span()[1]:]
                self.lineindex[line]=1

        # 如果是当天，就加上当天日期       
        if re.match(u"\d{1,3}[:：]\d{1,3}发布$",pub_time.strip()):
            pub_time = datetime.today().strftime("%Y-%m-%d  ")+pub_time.replace(u"发布","") 

        # 如果是n天前发布
        isBefore = self.PUB_TIME.search(pub_time)
        if isBefore:
            tmpdate = datetime.today() - timedelta(days = int(isBefore.group(1).encode('utf-8')))
            pub_time = tmpdate.strftime("%Y-%m-%d ")

        self.result["pub_time"] = re.sub(u"[年月]","-",pub_time).replace(u"日","")
        self.result["end_time"] = re.sub(u"[年月]","-",end_time).replace(u"日","")

        return pub_time+" "+ end_time

    # 企业名抽取
    def regular_inc_name(self):
        res = set ()
        for line in self.linelist:
            if self.clf.predict(line) in ['inc_name','other','job_name']:
                if self.START_DUTY.search(line) or self.START_DEMAND.search(line):continue
                if self.NOT_INC.search(line):continue
                findinc = self.INCNAME.search(line)
                if findinc:
                    if len(findinc.group())<26:
                        res.add(findinc.group().replace("招聘",""))
                        break
        if not res:
            for line in self.linelist:
                if self.START_DUTY.search(line) or self.START_DEMAND.search(line):continue
                for item in jieba.cut(line):
                    if item in self.firmnames:
                        res.add(item)
                if self.clf.predict(line)=='inc_name' and 3<len(line)<20:
                    res.add(line)
                    break
                if len(res)>0:break
        res = filter(lambda x:len(x)>1 and not re.search(u'^\d|参与|负责|协助|的|[，。:：！？，薪]|招聘|诚聘|补贴|吃住|险一金|奖金',x),list(res))
        self.result["inc_name"] = strQ2B(' / '.join(res))

        return res
   

    # 公司标签，如公司规模，是否已上市，外企，员工稳定性等
    def regular_inc_tag(self):

        res = set()
        jdStr = self.jdStr

        # 公司性质
        findTag = re.search(u"(公司性质|企业性质)[：:\s]\s?",jdStr)
        if findTag:
            jdstr =jdStr[findTag.span()[1]:]
            for line in jdstr.split()[:3]:
                if len(line.strip())<2:continue
                elif len(line)<15 and not re.search(u'地址',line): 
                    res.add(u"性质："+line.strip())
                    break
        else:
            findTag = re.search(u"欧美外资|非欧美外资|欧美合资|非欧美合资|外企代表处|政府机关|事业单位|民营公司|民营企业|创新型公司|非盈利机构|其他性质",jdStr)
            if findTag:
                res.add(findTag.group())

        # 所属行业
        findTag = re.search(u"(公司行业|所属行业|领域)[：:\s]|行业[：:]",jdStr)
        if findTag:
            jdstr =jdStr[findTag.span()[1]:]
            for line in jdstr.split():
                if len(line.strip())<2:continue
                elif len(line)<35: 
                    res.add(u"行业："+line.strip())
                    break

        else:
     #       P1 = re.compile(ur"教育培训|采矿/金属|医疗健康|移动互联网|互联网|科技|医疗器械|新材料|奢侈品/珠宝|通信|航天/造船|出版|军工/国防|农/林/牧/渔|家电/数码产品|造纸|人力资源|体育|会计/审计|艺术/工艺|管理咨询|印刷/包装|运输/铁路/航空|环境保护|物流/仓储|化工|原油/能源|生物技术|翻译|原材料/加工|专业服务|报纸/杂志|医疗/卫生|酒店|IT信息|制造工业|服装/纺织|互联网|休闲/娱乐/健身|/基金/期货|计算机软件|广播|私人/家政服务|建材|初中等教育|烟草业|旅游|银行|汽车|法律|电子商务|游戏|政府部门|服务业|公共事业|IT服务|建筑/房地产|批发/零售|非营利组织|计算机硬件|电子/半导体|食品/饮料|机械/自动化|检测/认证|日用品/化妆品|研究所/研究院|建筑设计/规划|贸易物流|商店/超市|图书馆/展览馆|医药|文化传媒|广告/公关/会展|房地产|进出口|土木工程|动漫|餐饮业?|医疗/护理|培训|消费品|金融|影视|高等教育|酒品|家具/家居|物业管理|装修装潢")
            P1 = re.compile(u"教育培训|(移动)?互联网|餐饮业|政府部门|装修装潢")      
            findTag = P1.search(jdStr)
            if findTag:
                res.add(findTag.group())

        # 公司规模
        pos = re.search(u"公司规模|员工人数|规模[：:\s]",jdStr)
        if pos:
            jdStr = jdStr[max(0,pos.span()[1]-3):min(pos.span()[1]+20,len(jdStr))]
            scale = re.search(ur"\d{2,}[\-~——]\d{2,}人|(\d+人以下)|(\d{3,}人以上)|少于\d+人|\d+人",jdStr)
            if scale:
                res.add(u"规模："+scale.group())

        # 其他特别信息
        if len(res)<2:
            for line in self.linelist:
                find_tag = re.search(u"大公司|五百强|世界500强|全球500强|小公司|成长型公司|创业公司|私有经济|集体经济|集团|外企|已上市|稳定性高|平均年龄\d+岁|妹纸多|学历高|福利待遇好|晋升机会大|民营公司|民营企业|创业型|国企|央企|500强",line)
                if find_tag:
                    res.add(find_tag.group())

        self.result["inc_tag"] =list(res)


    # 将剩余未处理的标记出来
    def regular_other(self):
        res = []
        cnt = 0.0
        for line in self.linelist:
            if (re.search(u"内容|描述|职责|要求|条件|制度|时间|工作地.|福利|岗位|如果你|这样的事|资格|阶段|说明",line) and len(line)<6):continue
            if self.START_DUTY.search(line) and self.START_DEMAND.search(line) and len(line)<10:continue
            if self.lineindex[re.sub(u"[\s+ ]+"," ",line)]!=1:
                res.append(line)
                cnt += 1
#        print "处理百分率%.3f"%(1.0-cnt/len(self.linelist))
        self.result["other"] ="\n".join(res)




    def output_last(self):
        """
        最后善后处理个别工作内容与要求混合在一起的特殊情况，防止分错
        """
        duty = []
        demand = []
        if re.search(u"岗位描述|职业描述|职责描述|工作描述|职位描述",self.jdStr):
            if len(self.result['demand'].split('\n'))<1 :
                tmp=self.result['duty'].split('\n')
                tmp.extend(self.result['demand'].split('\n'))
                linelist = [line for line in tmp if len(line)>3]
                id1,id2 = 1,1
                for line in linelist:
                    if re.match(u"\d{1,2}|[\uff0d【（\(\-\+]|[a-z][\.。、\s]",line.strip()):
                        self.result['demand']=self.result['duty']
                        self.result['duty'] = ""
                        return 
                    if self.DEMAND.search(line):
                        demand.append(str(id1)+". "+self.clean_line(line.strip()))
                        id1 += 1
                    elif self.DUTY.search(line):
                        duty.append(str(id2)+". "+self.clean_line(line.strip()))
                        id2 += 1
                self.result['demand'] = "\n".join(demand)
                self.result['duty'] = "\n".join(duty)



    def parser(self,jdstr):
        self.preprocess(jdstr)
        self.regular_inc_name()   # 企业名称
        self.regular_inc_tag()    # 企业标签
        self.regular_pubtime()    # 发布时间，截止时间
        self.regular_jobname()    # 职位名称
        self.regular_jobtag()     # 职位标签
        self.regular_sex()        # 性别
        self.regular_age()        # 年龄
        self.regular_major()      # 专业
        self.regular_degree()     # 学历
        self.regular_exp()        # 经验
        self.regular_skill()      # 技能,默认抽取6个技能词汇
        self.regular_workplace()  # 工作地点
        self.regular_pay()        # 薪酬
        self.regular_cert()       # 证书
        self.regular_demand()     # 要求
        self.regular_duty()       # 职责
        self.regular_benefits()   # 福利
        self.regular_other()      # 其他
        self.output_last()
        if len(self.result.keys())!=19:
            print len(self.result.keys()),'wrong'
        return deepcopy(self.result)

    def split_multi_jd(self,jdstr):
        jds =[ jd for jd in self.SPLIT_JD.split(jdstr) if len(jd)>10 ]
        res = []
        for jd in jds:
            result = self.parser(jd)
            res.append(deepcopy(result))
        return res

    def cosine_sim(self,x,y):
        num = sum(x[i]*y[i] for i in range(len(x)))
        den = np.sqrt(sum([i*i for i in x]))*np.sqrt(sum([i*i for i in y]))
        if den<0.001:
            return 0
        return "%.2f%%" %(num/den)


    def pearson_sim(self,v1,v2):
        n = len(v1)
        num = sum( v1[i]*v2[i] for i in range(n))-sum(v1)*sum(v2)/n
        den = np.sqrt((sum([i1 * i1 for i1 in v1])-np.power(np.sum(v1),2)/n)*(sum([i2 * i2 for i2 in v2])-np.power(np.sum(v2),2)/n))
        if den==0:
            return 1
        return "%.2f%%" %(num/den)



    def match(self,jd_skill,cv_skill):
        # type: (object, object) -> object
        res = {}
        res['jd_skill'] = '\n'.join(list(set(jd_skill.split('\n'))))
        res['cv_skill'] = '\n'.join(list(set(cv_skill.split('\n'))))
        v1 = self.line2vec(jd_skill)
        v2 = self.line2vec(cv_skill)
        euclidean_sim = sum([pow(v1[i]-v2[i],2) for i in range(len(v1))])
        pearson_sim = self.pearson_sim(v1,v2)
        res['pearson_sim'] = pearson_sim
        res['cosine_sim'] = self.cosine_sim(v1,v2)
        res['euclidean_sim']=1./(1+np.sqrt(euclidean_sim))
        dis = Simhash(jd_skill).distance(Simhash(cv_skill))
        if dis>25:
            dis *= 3
        if dis>100:
            dis =100

        res['sim'] = str(100.-dis)+'%'
        return res

        


if __name__ == "__main__":
    test = JdParserPlain()
    jdstr = [line.strip() for line in open('data/jd_text.txt')]
    result = test.split_multi_jd('\n'.join(jdstr))

    for k,v in result[0].items():
        print "{}:{}".format(k,v)
