##coding=utf-8
import sys,os
import codecs
import re
#将某些结尾的词语进行转化生成新的词表
# fileDic = codecs.open("../data/jobposition.txt","rb","utf-8")
# fileNew = codecs.open("../data/jobposition_new.txt","wb","utf-8")
# # endWith = re.compile(u"学类$|学$|类$|工程$|技术$|理论$")
# endWith = re.compile(u"有限公司$")
# dic = set()
# for item in fileDic.readlines():
    # if item.find(u"与")!=-1:
    #     fileNew.writelines(item)
    #     words = item.split(u"与")
    #     if len(words)!=1:
    #         words[0]+=u'\n'
    #     for line in words:
    #         if line not in dic:
    #             fileNew.writelines(line)
    #             dic.add(line)
    #
    # else:
    #     if item not in dic:
    #         fileNew.writelines(item)
    #         dic.add(item)
    #     if endWith.search(item) and endWith.sub(u"", item) not in dic and len(item)>3:
    #         dic.add(endWith.sub(u"", item))
    #         subSent = endWith.sub(u"", item)
    #         fileNew.writelines(subSent)


    # if endWith.search(item):
    #     continue
    # else:
    #     fileNew.writelines(item)

#统计职位名后面2个字有什么规律
fileDic = codecs.open("../data/jobposition_new.txt","rb","utf-8")
fileNew = codecs.open("../data/jobposition_prefix.txt","wb","utf-8")
from collections import Counter
wordList = []
for line in fileDic.readlines():
    wordList.append(line.strip()[0:5])
for i in Counter(wordList).most_common():
    flag = True
    for chr in i[0]:
        if chr.isdigit():
            flag = False
            break
    if flag :
        fileNew.writelines(i[0]+u"\n")


#将某些认为是多余的词去掉
# fileDic = codecs.open("../data/jobposition.txt","rb","utf-8")
# fileNew = codecs.open("../data/jobposition_new.txt","wb","utf-8")
# endWith = re.compile(u"研究生$")
# dic = set()
# for line in fileDic.readlines():
#     if endWith.search(line) :
#         continue
#     else:
#         fileNew.writelines(line)