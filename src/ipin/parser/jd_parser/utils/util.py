#!/usr/bin/env python
# coding=utf-8

import sys
import os
import codecs,re
from path import *
import numpy as np
reload(sys)

sys.setdefaultencoding('utf-8')

def generate_text_withlabel(result2,jdfrom = None,file_path = None,count = None):
    jdName = file_path.split('/')[-2]
    file_name = os.path.join(file_path+'../jd_for_cnn/','{0}.txt'.format(count))
    # file_num = count/10000
    fileOld = codecs.open(file_path+'../jd_for_cnn/'+"51job.txt",'a','utf-8')
            #1、将解析出来的结果制作成一个初步的数据格式，包括分行和打上大标签，大标签用0-4表示
            # i=0
            # for key in result2.keys():
            #     strType = [type('1'), type(u'1')]
            #     if type(result2[key])in strType:
            #         fileOld.writelines(result2[key]+'\t'+str(i)+'\n')
            #     else:
            #         for secondKey in result2[key].keys():
            #             if secondKey == 'incIntro':
            #                 sents = result2[key][secondKey].split('\n')
            #                 for sent in sents:
            #                     if len(sent)>=2 and sent!='  ':
            #                         fileOld.writelines(sent +'\t'+ str(i)+'\n')
            #             elif secondKey == 'jobDesc':
            #                 sents = result2[key][secondKey].split('\n')
            #                 for sent in sents:
            #                     if len(sent) >= 2 and sent!='  ':
            #                         fileOld.writelines(sent + '\t' + str(i) + '\n')
            #             elif result2[key][secondKey]!='':
            #                 result2[key][secondKey]=re.sub('\n','',str(result2[key][secondKey]))
            #                 fileOld.writelines(str(result2[key][secondKey]) + '\t' +str(i)+'\n' )
            #     i+=1
            # fileOld.close()
            #2、将解析出来的结果制作成一个初步的数据格式，包括分行和打上小标签，小标签用0-47表示
    i = 0
    for key in result2.keys():
        strType = [type('1'), type(u'1')]
        if type(result2[key])in strType:
            fileOld.writelines(result2[key]+' '+str(i)+'\n')
            i += 1
        else:
            for secondKey in result2[key].keys():
                if secondKey == 'incIntro' or secondKey == 'jobDesc':
             #        sents = result2[key][secondKey].split('\n')
             #        for sent in sents:
			# sent = sent.strip()
             #            if len(sent) >= 2 and sent != '  ':
             #                fileOld.writelines(sent + ' ' + str(i) + '\n')
                    i += 1
                elif secondKey == "jobMajorList":
                    tmp = ''
                    if len(result2[key][secondKey])==0:
                        tmp +=' ' + str(i)
                    else:
                        for word in result2[key][secondKey][:-1]:
                            tmp+=word
                        tmp+=' '+result2[key][secondKey][-1]+' '+str(i)
                        fileOld.writelines(tmp.strip() +'\n')
                    i+=1
                elif result2[key][secondKey]!='':
                    result2[key][secondKey]=re.sub('\n','',str(result2[key][secondKey]))
		    #print result2[key][secondKey].strip(),result2[key][secondKey].strip()==''
		    if result2[key][secondKey].strip()!='':
                        fileOld.writelines(str(result2[key][secondKey].strip()) + ' ' +str(i)+'\n' )
                    i += 1
                else:
                    i+=1

    fileOld.close()

def generate_text_withoutlabel(result2,jdfrom = None,file_path = None,count = None):
    jdName = file_path.split('/')[-2]
    file_name = os.path.join(file_path + '../jd_for_cnn1', '{0}.txt'.format(count))

    fileOld = codecs.open(file_name, 'a', 'utf-8')

    for key in result2.keys():
        strType = [type('1'), type(u'1')]
        if type(result2[key])in strType:
            fileOld.writelines(result2[key]+'\n')
           
        else:
            for secondKey in result2[key].keys():
                if secondKey == 'incIntro' or secondKey == 'jobDesc':
                    sents = result2[key][secondKey].split('\n')
                    for sent in sents:
			sent = sent.strip()
                        if len(sent) >= 2 and sent != '  ':
                            fileOld.writelines(sent  + '\n')
                   
                elif secondKey == "jobMajorList":
                    tmp = ''
                    if len(result2[key][secondKey])==0:
                        tmp +=' ' 
                    else:
                        for word in result2[key][secondKey][:-1]:
                            tmp+=word
                        tmp+=' '+result2[key][secondKey][-1]
                    tmp = tmp.strip()
                    if tmp!=u'':
                        fileOld.writelines(tmp.strip() +'\n')
                  
                elif result2[key][secondKey]!='':
                    result2[key][secondKey]=re.sub('\n','',str(result2[key][secondKey]))
		    #print result2[key][secondKey].strip(),result2[key][secondKey].strip()==''
		    if result2[key][secondKey].strip()!='':
                        fileOld.writelines(str(result2[key][secondKey].strip())+'\n' )
                  
        
    fileOld.close()
def strQ2B(ustring):
    """
    中文全角转半角
    """
    res = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:
            continue
        elif inside_code >=65281 and inside_code <= 65374:
            inside_code -= 65248

        res += unichr(inside_code)
    return res


def leven_distance(s1,s2):
    """
    动态规划实现编辑距离
    """

    s1 = strQ2B(s1.decode('utf-8')).lower()
    s2 = strQ2B(s2.decode('utf-8')).lower()

    m,n = len(s1),len(s2)
    colsize,v1,v2 = m+1,[],[]

    for i in range((n+1)):
        v1.append(i)
        v2.append(i)

    for i in range(m+1)[1:m+1]:
        for j in range(n+1)[1:n+1]:
            cost = 0
            if s1[i-1]==s2[j-1]:
                cost = 0
            else:
                cost = 1
            minValue = v1[j]+1
            if minValue > v2[j-1]+1:
                minValue = v2[j-1]+1
            if minValue >v1[j-1]+cost:
                minValue = v1[j-1]+cost
            v2[j] = minValue
        for j in range(n+1):
            v1[j] = v2[j]

    return v2[n]


def lcs_string(a,b):
    lena,lenb = len(a),len(b)

    # length table
    c = [[0 for i in b] for j in a]

    # direction table
    flag = [[0 for i in b] for j in a]

    for i in range(lena):
        for j in range(lenb):
            if i==0 or j==0:
                c[i][j] = 0
                continue

            if a[i]==b[j]:
                c[i][j] = c[i-1][j-1]+1
                flag[i][j] = 3

            elif c[i-1][j]<c[i][j-1]:
                c[i][j] = c[i][j-1]
                flag[i][j] = 2
            else:
                c[i][j] = c[i-1][j]
                flag[i][j] = 1


    (p1,p2) = (lena-1,lenb-1)
    s = []
    while 1:
        d = flag[p1][p2]
        if d == 3:
            s.append(a[p1])
            p1 -= 1
            p2 -= 1 
        elif d == 2:
            p2 -= 1
        elif d == 1:
            p1 -= 1
        if p1==0 or p2==0:
            # solve the first element without print problem
            if a[p1]==b[p2]:
                s.append(a[p1])
            break
    s.reverse()
    return ''.join(s)


def lcs_len(a,b):
    c = [[0 for j in b] for i in a]
    for i in range(len(a)):
        for j in range(len(b)):
            if i==0 or j==0:
                continue
            if a[i]==b[j]:
                c[i][j] = c[i-1][j-1]+1
            else:
                c[i][j] = max(c[i-1][j],c[i][j-1])
    return c[i][j]




def lcs_from_list(input,jobnames):
    if input in jobnames:
        return input
    res = [(lcs_len(input,jobname),jobname) for jobname in jobnames]
    #print res
    res.sort()
    return res[-1][1]


def num2label(num):
    labelList = ["jdFrom", "pubTime", "incName", "incScale", "incType", "incIndustry", "incWorkLoc", "incUrl", \
                 "incStage", "incAliasName", "investIns", "incContactInfo", "incCity", "zipCode", "incContactName",
                 "incIntro", \
                 "jobType", "jobPosition", "jobCate", "jobSalary", "jobWorkAge", "jobDiploma", "jobNum", "jobWorkCity",
                 "jobWorkLoc", \
                 "jobWelfare", "age", "jobEndTime", "email", "gender", "jobMajorList", "jobDesc", \
                 "keyWords", "isFullTime", "jdRemedy", "posType", "urgent", "holidayWelfare", "livingWelfare",
                 "salaryCombine", \
                 "socialWelfare", "trafficWelfare", "jobDepartment", "jobReport", "jobReportDetail", "jobSubSize",
                 "language", "overSea"]

    return str(labelList[num])

# def dump_labelCounts():
#     #读入数据
#     import cPickle
#     x = cPickle.load(open(data_path+"51job_pinyin.p","rb"))
#     revs, W, W2, word_idx_map, vocab,idx_word_map = x[0], x[1], x[2], x[3], x[4],x[5]
#     #将label作为key，label的个数作为value加入到label_counts字典中去
#     label_counts = {}
#     for i in range(len(revs)):
#         if revs[i]['label'] in label_counts.keys():
#             label_counts[revs[i]['label']]+=1
#         else:
#             label_counts[revs[i]['label']] =1
#     file_label = file(data_path+'label_counts.pkl','w')
#     cPickle.dump(label_counts,file_label,protocol=cPickle.HIGHEST_PROTOCOL)

def get_idx_from_sent(sent, word_idx_map, max_l=51, k=200,pin = True):
    """
    Transforms sentence into a list of indices.
    """
    x = []
    words = sent

    if pin == True:
        for word in words:
            if pinyin(word)[0][0] in word_idx_map:
                x.append(word_idx_map[pinyin(word)[0][0]])
            else:
            #print (u"{0} not find".format(word[0]))
                x.append(word_idx_map[u'unknown'])
    else:
        for word in words:
            if word in word_idx_map:
                x.append(word_idx_map[word])
            else:
                # print (u"{0} not find".format(word[0]))
                x.append(word_idx_map[u'unknown'])
    if len(x)>=max_l:
        x = x[0:max_l]
    return x

def pad_sent(sent, word_idx_map, max_l=51, k=200, filter_h=5):
    x = []
    pad = filter_h - 1
    for i in xrange(pad):
        x.append(0)
    x.extend(sent)
    if len(x)>=max_l+2*pad:
        x = x[0:max_l+2*pad]
        return x
    else:
        while len(x) < max_l+2*pad:
            x.append(0)
        return x

def make_idx_data_cv(revs, word_idx_map, max_l=51, k=200, filter_h=5,pin = True,config = None):
    """
    Transforms sentences into a 2-d matrix.
    """
    data = []
    sents = []
    concatenate_length = (config.total_sents-1)/2

    # get all sents without padding
    for index in range(len(revs)):
        sents.append(get_idx_from_sent(revs[index], word_idx_map,max_l, k,pin))

    #pad the sents
    for index in range(len(revs)):

        new_sent = []
        left_pad = abs(concatenate_length-index)
        right_pad = abs(concatenate_length - (len(revs)-1-index))

        if left_pad>concatenate_length:
            left_pad = 0
        if right_pad>concatenate_length:
            right_pad = 0
        if left_pad!=0:
            for i in range(left_pad):
                new_sent+=[0 for i in range(config.max_len)]
        if left_pad!=concatenate_length:
            for i in range(concatenate_length-left_pad,0,-1):
                new_sent+=sents[index-i]
        new_sent+=sents[index]
        if right_pad!=concatenate_length:
            for i in range(1,concatenate_length-right_pad+1):
                new_sent+=sents[index+i]
        if right_pad!=0:
            for i in range(right_pad):
                new_sent+=[0 for i in range(config.max_len)]

        sent = pad_sent(new_sent, word_idx_map,max_l*config.total_sents, k,filter_h)
        data.append(sent)

    data = np.array(data,dtype="float32")
    return data



if __name__=="__main__":
    a = u"广东省深圳市"
    b = u"广东省梅州市"
    print lcs_from_list(a,b)
