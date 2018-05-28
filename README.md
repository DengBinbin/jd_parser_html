## 一、 JD、CO解析 

1. 作用：对输入的半结构化ＪＤ、CO文本解析解析为结构化的文本。  
2. 原理：使用句子分类器＋规则＋相关词库匹配生成。  
3. *演示地址: http://192.168.1.91:8081/jdparser*  
4. 输入与输出  
    - 输入：2个参数  
    --1. htmlContent : lagou,liepin,51job,智联,职友集，智联卓聘的招聘html转换为unicode编码后的内容**不包括智联、猎聘的校招**  
    --2. jdFrom : lagou,51job,zhilian,liepin,highpin,jobui 中的一个  

    [jd_type 字段的 具体定义](http://192.168.1.22/rpc_gen/etl_gen_py/blob/master/idl/jd/jd_type.thrift)

    -- 输出thrift　定义类型, jdRaw  
    ```python
    struct JdRaw {
        1:string jdId,
        2:string jdFrom,
        3:string jdUrl,
        4:JdIncRaw jdInc,
        5:JdJobRaw jdJob,
        6:string pubTime,
        7:string endTime,
    }
    ```

5. 具体抽取字段和准确率（有待测试）  

6. 代码: 所有代码文件在91号机子 */home/weihong/jd_parser/* 下  
    - thrift 调用接口   
    --1. [thrift服务器端调用文件 thrift_server_jd.py](thrift_server_jd.py)    
    --2. [thrift客户端调用文件 thrift_client_jd.py](thrift_client_jd.py)  
    - http调用接口:   


```python

import sys
sys.path.append("./src/ipin/parser/jd_parser/")
from api.api_jd_parser import JdParser
from utils.path import *
import codecs
test = JdParser()
htmlContent1 = codecs.open(jd_path+'lagou/1.html').read()
htmlContent2 = codecs.open(co_path+'lagou/1.html').read()
result1 = test.parser(htmlContent=htmlContent1,jdFrom="lagou",type="jd_detail")
result2 = test.parser(htmlContent=htmlContent2,jdFrom="lagou",type="co")
import json
print json.dumps(result1,ensure_ascii=False,indent=4)
print json.dumps(result2,ensure_ascii=False,indent=4)

```  



## 二. 接口部署本地安装及使用   


1. 下载源码到本地 git clone 
2. cd ./thrift_api_install_first/common_gen_py/  `sudo python setup.py install`
3. cd ./thrift_api_install_first/etl_gen_py/    ` sudo python setup.py install`
4. 安装api_jd_parser接口 python setup.py install --user
5. 使用: 
    
```python
import sys
sys.path.append("./src/ipin/parser/jd_parser/")
from api.api_jd_parser import JdParser
from utils.path import *
import codecs
test = JdParser()
htmlContent1 = codecs.open(jd_path+'lagou/1.html').read()
htmlContent2 = codecs.open(co_path+'lagou/1.html').read()
result1 = test.parser(htmlContent=htmlContent1,jdFrom="lagou",type="jd_detail")
result2 = test.parser(htmlContent=htmlContent2,jdFrom="lagou",type="co")
import json
print json.dumps(result1,ensure_ascii=False,indent=4)
print json.dumps(result2,ensure_ascii=False,indent=4)
```



## 三. 演示demo： 


localhost:8081/jdparser  

---

>> by-　dengbinbin@ipin.com
>> @2016.08