# print "first_num : {0}".format(self.first)
# print "second num : {0}".format(self.second)
# print "third num : {0}".format(self.third)
# length = []
# titleList = []
# data_list = []
# keywords = []
# titlewords = []
# widthList = []
# jobNameIdx = None
# rows = self.jdstr.find("table").find_all("tr")
# title_line = 0
# for row in rows:
#
#     cols = row.find_all("td")
#     for i in cols:
#         print i.attrs.has_key("width")
#     if len(widthList) == 0:
#         widthList = [col.width for col in cols if col.get_text().strip()]
#     cols = [col.get_text().strip() for col in cols if col.get_text().strip()]
#
#     length.append(len(cols))
#     if len(cols)>1 and len(titleList)==0:
#         for col in cols:
#             titleList.append(col)
#     elif len(titleList)>0:
#         data_list.append([col for col in cols])
#     else:
#         title_line+=1
# print widthList
# '''
# params:
# title_line：标题所出现的行号
# titleList：标题所包含的内容
# titlewords:标题中我们所需要的那些列的关键字
# keywords:找到标题title中我们所感兴趣的关键字
#
# '''
# for idx, key in enumerate(titleList):
#     if self.JOBNAME_LINE.search(key):
#         jobNameIdx = idx
#         titlewords.append([key, idx])
#     elif re.search(u"人数|数量",key):
#         keywords.append(["jobNum", idx])
#         titlewords.append([key, idx])
#     elif re.search(u"学历", key):
#         keywords.append(["jobDiploma", idx])
#         titlewords.append([key, idx])
#     elif re.search(u"工作地点|工作地址", key):
#         keywords.append(["jobWorkLoc", idx])
#         titlewords.append([key, idx])
#     elif re.search(u"专业", key):
#         keywords.append(["jobMajorlist", idx])
#         titlewords.append([key, idx])
#     elif re.search(u"岗位职责|任职要求|薪资|薪资待遇|任职条件",key):
#         keywords.append(["jobDesc", idx])
#         titlewords.append([key, idx])
#
# print titlewords
#
#
# print u"表格开头包含项:{0}".format(keywords)
# print jobNameIdx
# stand = True
# for le in length:
#     if le != length[0]:
#         stand = False
#         break
# print u"表格是否m*n列中间无缺失嵌套?:{0}".format(stand)
# if stand:
#     if jobNameIdx!=None:
#         for row in data_list:
#             #有职位名相同情况
#             if row[jobNameIdx] not in self.jobNameList:
#                 self.jobNameList.append(row[jobNameIdx])
#             else:
#                 self.jobNameList.append(row[jobNameIdx]+u" ")
#             #找职位类别
#             if self.jobNameList[-1].find(u"实习")!=1 and self.jdType==u"实习":
#                 self.jdJob[row[jobNameIdx]]["jobType"] = u"实习"
#             else:
#                 self.jdJob[row[jobNameIdx]]["jobType"] = u"全职"
#             #去找每个职位的信息
#             for key in keywords:
#                 if key[0]=="jobDesc":
#                     self.jdJob[row[jobNameIdx]][key[0]] += titlewords[key[1]]+u"\n"
#                     self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]] + u'\n'
#                 else:
#                     self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]]
#
#
#
# # else:
# #     print "ori jobNameList {0}".format(len(self.jobNameList))
# #     max_len = len(keywords)+1
# #     # del length[:jobNameIdx+1]
# #     print u"在表格中，每一行的列数分别是:{0}".format(length)
# #     keywords.append(['jobName', jobNameIdx])
# #     keywordsCopy = deepcopy(keywords)
# #     jobNameIdxCopy = deepcopy(jobNameIdx)
# #     if jobNameIdx != None:
# #         for idx,row in enumerate(data_list):
# #             #表宽大于最大关键词个数，不需要改变数据下标
# #             if len(row)>max_len:
# #                 # 有职位名相同情况
# #                 if row[jobNameIdx] not in self.jobNameList:
# #                     self.jobNameList.append(row[jobNameIdx])
# #                 else:
# #                     self.jobNameList.append(row[jobNameIdx] + u" ")
# #                 #判断职位类别
# #                 if self.jobNameList[-1].find(u"实习") != 1 and self.jdType == u"实习":
# #                     self.jdJob[row[jobNameIdx]]["jobType"] = u"实习"
# #                 else:
# #                     self.jdJob[row[jobNameIdx]]["jobType"] = u"全职"
# #                 #去找每一栏信息
# #                 for key in keywords:
# #                     if key[0] == "jobName":
# #                         continue
# #                     if key[0] == "jobDesc":
# #                         self.jdJob[row[jobNameIdx]][key[0]] += titleList[key[1]] + u"\n"
# #                         self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]] + u'\n'
# #                     else:
# #                         self.jdJob[row[jobNameIdx]][key[0]] += row[key[1]]
# #
# #             #表宽等于数据关键词个数，说明非关键词共用，需要进行一下排序重新进行排序，但为了不影响后序大于关键词个数的行
# #             #每次更改的都是副本
# #             elif len(row)==max_len:
# #                 keywordsCopy = sorted(keywordsCopy,key = lambda x:x[1])
# #
# #                 for idx,item in enumerate(keywordsCopy):
# #                     if item[0]=="jobName":
# #                         jobNameIdxCopy = idx
# #                     item[1] = idx
# #                 print "after change,the key words are{0}".format(keywordsCopy)
# #                 # 有职位名相同情况
# #                 if row[jobNameIdxCopy] not in self.jobNameList:
# #                     self.jobNameList.append(row[jobNameIdxCopy])
# #                 else:
# #                     self.jobNameList.append(row[jobNameIdxCopy] + u" ")
# #                 #判断职位类别
# #                 if self.jobNameList[-1].find(u"实习") != 1 and self.jdType == u"实习":
# #                     self.jdJob[row[jobNameIdx]]["jobType"] = u"实习"
# #                 else:
# #                     self.jdJob[row[jobNameIdx]]["jobType"] = u"全职"
# #                 # 去找每一栏信息
# #                 for col,key in enumerate(keywordsCopy):
# #                     print "*"*100
# #                     print col
# #                     print titlewords
# #                     if key[0]=="jobName":
# #                         continue
# #                     if key[0] == "jobDesc":
# #                         self.jdJob[self.jobNameList[-1]][key[0]] += titlewords[col][0] + u'\n'
# #                         self.jdJob[self.jobNameList[-1]][key[0]] += row[col] + u"\n"
# #                     else:
# #                         self.jdJob[self.jobNameList[-1]][key[0]] += row[col]
# #
# #             #出现了关键词也共用的情况
# #             elif len(row)>0 and len(row)<max_len:
# #                 print "share keywords"
# #
# #     print "find jobPos : {0}".format(len(self.jobNameList))