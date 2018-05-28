#coding=utf8
import os,sys
sys.path.append(os.path.abspath(os.path.join(__file__,"../","../")))
reload(sys)
import re
from collections import Counter
from utils.path import *
print len(os.listdir(xz_path+"yjs/"))
# fnames = filter(lambda x:x.endswith("html"),os.listdir(xz_path+"yjs/"))
path = xz_path + 'yjs/'
fnames = [path + fname for fname in os.listdir(path) if fname.endswith("html")]
cnt = Counter()
keywords = Counter()
start = 'class="info"'
end = 'class="mq_tw"'
table = 'table'
strong = re.compile("strong>(.*?)</strong")
noise =  re.compile(u"[()（）一二三四五六【】0-9\.、:：\s]")

for fname in fnames:
	with open(fname) as fi:
		flag = False
		for i,l in enumerate(fi):
			if not flag and l.find(start)!=-1:
				flag =True
			if flag and l.find(table)!=-1:
				cnt[fname] += 1
			if flag:
				for w in strong.findall(l):
				  word = w.decode("utf8").strip()
				  if len(word)>10:
					continue
				  word = noise.sub("",word)
				  keywords[word] +=1	
			if  flag and  l.find(end)!=-1:
				break
		if fname in cnt and cnt[fname]>1:
			print("{} have {} tables in content".format(fname,cnt[fname]))
print("{}/{} files have table in content block.".format(len(cnt),len(fnames)))

K = 200
print("Top {}/{} words in strong tag".format(K,len(keywords)))
for k,v in keywords.most_common(200):
	print(u"{},{}".format(k,v))
				
