#!/usr/bin/env python
# coding=utf-8
'''
新版本demo主程序
'''
import tornado.httpserver
import tornado.options
import tornado.web
from tornado.options import define,options
import simplejson as json
import urllib2
import sys,os,re

from api_jd_parser import JdParser

import  requests
reload(sys)
sys.setdefaultencoding('utf-8')

define("port",default=8081,help="run on the given port",type=int)


class JdParserHandler(tornado.web.RequestHandler):
    def get(self):
        result = self.get_argument("result",{})
        source_text = self.get_argument("source","")

        self.render("inputjd_co.html",source=source_text,result=result)


    def post(self):
        source_text = self.get_argument("source","")
        type = self.get_argument("type")


        if "jdfile" in self.request.files:
            file_metas = self.request.files["jdfile"]

            for meta in file_metas:
                source_text = meta["body"]

                #source_text.decode('utf-8')
                if re.search(u"lagou.com",source_text):
                    result= jdParser.parser(htmlContent=source_text, jdFrom="lagou", type=type)
                elif re.search(u"51job.com",source_text):
                    result= jdParser.parser(htmlContent=source_text,jdFrom="51job",type=type)

                elif re.search(u"zhaopin.com",source_text):
                    result= jdParser.parser(htmlContent=source_text, jdFrom="zhilian", type=type)

                elif re.search(u"jobui.com",source_text):
                    result,= jdParser.parser(htmlContent=source_text, jdFrom="jobui", type=type)
                elif re.search(u"liepin.com", source_text):
                    result= jdParser.parser(htmlContent=source_text, jdFrom="liepin", type=type)
                elif re.search(u"highpin.com",source_text):
                    result = jdParser.parser(htmlContent=source_text,jdFrom="highpin",type=type)

                else:
                    result = {'error':'input file is wrong'}

        else:


            if re.search("www.lagou.com/jobs/\d+.html",source_text) or re.search("www.lagou.com/gongsi/\d+.html",source_text):
                result = jdParser.parser(url=source_text, jdFrom="lagou", type=type)
            elif re.search(u"jobs.zhaopin.com/.+\d+.htm",source_text) or re.search(u"company.zhaopin.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text, jdFrom="zhilian", type=type)

            elif re.search("jobs.51job.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="51job",type=type)

            elif re.search("job.liepin.com/\d+",source_text) or re.search("a.liepin.com/\d+/job_\d+",source_text)\
                    or re.search("company.liepin.com/\d+",source_text):
                result = jdParser.parser(url=source_text, jdFrom="liepin", type=type)

            elif re.search("sz.58.com",source_text):
                result = jdParser.parser(url=source_text,jdFrom="58.com",type=type)

            elif re.search("jobui.com/job/\d+",source_text) or re.search("jobui.com/company/\d+",source_text):
                result = jdParser.parser(url=source_text, jdFrom="jobui", type=type)
            elif re.search("highpin.cn/job/",source_text):
                result = jdParser.parser(url=source_text,jdFrom="highpin",type=type)

            else:
                print 'url',source_text
                result = {'error':'input url is wrong','url':source_text}
        #print logo
        json_str = json.dumps(result,ensure_ascii=False,indent=4)
        if source_text.startswith("http"):
            url = source_text


            if url.find("51job")>1:
                # if source_text.find("jobui.com")>1:
                #     return
                #
                # source_text = source_text.replace("gb2312","utf-8")
                #
                # source_text = unicode(source_text,u"gb18030",errors='ignore')
                res = requests.get(url)
                res.encoding = 'gb18030'
                source_text = res.text


            # elif url.find("jobui")>1:
            #     source_text=re.sub('<script.*?>.*?</script>','',source_text)
            else:
                source_text = urllib2.urlopen(source_text).read()
        logo = result["coInc"]["incLogo"] if type=="co" else None
        photo = result["coInc"]["incPhoto"] if type=="co" else None

        self.render("outputjd_co.html",source=source_text,result=json_str,logo =logo ,photo = photo)




class JdUrlHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            source_text = self.get_argument("input_url")
            # detail = self.get_argument("detail",'False')
            type = self.get_argument("jd_detail")
            if re.search("www.lagou.com/jobs/\d+.html",source_text):
                result = jdParser.parser(url=source_text,jdFrom="lagou",type=type)

            elif re.search(u"jobs.zhaopin.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="zhilian",type=type)

            elif re.search("jobs.51job.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="51job",type=type)

            elif re.search("job.liepin.com/\d+",source_text) or re.search("a.liepin.com/\d+/job_\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="liepin",type=type)

            elif re.search("sz.58.com",source_text):
                result = jdParser.parser(url=source_text,jdFrom="58tc",type=type)

            elif re.search("jobui.com/job/\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="jobui",type=type)

            elif re.search("highpin.com/job/\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="highpin",type=type)

            else:
                result ={ "error":"input url is wrong",'url:':source_text }

        except Exception,e:
            result ={ "error":"sorry,sth wrong happened","reason":e }

        self.write(result)


class JdStringHandler(tornado.web.RequestHandler):

    def post(self):
        try:
            htmlContent = self.get_argument("htmlContent","")
            jdFrom = self.get_argument("jdFrom","")
            result = jdParser.parser(htmlContent = htmlContent,jdFrom=jdFrom,type=type)
        except Exception,e:
            result ={ "error":str(e)}
        self.write(result)


if __name__ == "__main__":

    jdParser = JdParser()


    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers = [(r'/',JdParserHandler),(r'/jdparser',JdParserHandler),(r"/jdUrl",JdUrlHandler)],
        #handlers=[(r'/', JdParserHandler),(r'/jdparser',JdParserHandler)],
        template_path = os.path.join(os.path.dirname(__file__),"templates"),
        static_path='/home/deng/workplace/jd_data/test_cos/',
        debug=True,
        autoescape=None,
        )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    print "starting tornado at port %d..." % options.port
    tornado.ioloop.IOLoop.instance().start()
