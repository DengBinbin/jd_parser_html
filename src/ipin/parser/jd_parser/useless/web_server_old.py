#!/usr/bin/env python
# coding=utf-8
'''
老版本demo主程序
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

        self.render("inputjd.html",source=source_text,result=result)


    def post(self):
        source_text = self.get_argument("source","")
        detail = self.get_argument("detail","False")

        if "jdfile" in self.request.files:
            file_metas = self.request.files["jdfile"]

            for meta in file_metas:
                source_text = meta["body"]

                #source_text = unicode(source_text)
                if re.search(u"lagou.com",source_text):

                    result = jdParser.parser(htmlContent=source_text,jdFrom="lagou",detail=detail)
                elif re.search(u"51job.com",source_text):
                    result = jdParser.parser(htmlContent=source_text,jdFrom="51job",detail = detail)

                elif re.search(u"zhaopin.com",source_text):
                    result = jdParser.parser(htmlContent=source_text,jdFrom="zhilian",detail = detail)

                elif re.search(u"jobui.com",source_text):
                    result = jdParser.parser(htmlContent=source_text,jdFrom="jobui",detail = detail)

                elif re.search(u"highpin.com",source_text):
                    result = jdParser.parser(htmlContent=source_text,jdFrom="highpin",detail = detail)

                else:
                    result = {'error':'input file is wrong'}

        else:


            if re.search("www.lagou.com/jobs/\d+.html",source_text):
                result = jdParser.parser(url=source_text,jdFrom="lagou",detail = detail)
            elif re.search(u"jobs.zhaopin.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="zhilian",detail = detail)

            elif re.search("jobs.51job.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="51job",detail = detail)

            elif re.search("job.liepin.com/\d+",source_text) or re.search("a.liepin.com/\d+/job_\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="liepin",detail = detail)

            elif re.search("sz.58.com",source_text):
                result = jdParser.parser(url=source_text,jdFrom="58.com",detail = detail)

            elif re.search("jobui.com/job/\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="jobui",detail = detail)

            elif re.search("highpin.cn/job/",source_text):
                result = jdParser.parser(url=source_text,jdFrom="highpin",detail = detail)

            else:
                print 'url',source_text
                result = {'error':'input url is wrong','url':source_text}

        result = json.dumps(result,ensure_ascii=False,indent=4)

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


            elif url.find("jobui")>1:
                source_text=re.sub('<script.*?>.*?</script>','',source_text)
            else:
                source_text = urllib2.urlopen(source_text).read()
        self.render("outputjd.html",source=source_text,result=result)




class JdUrlHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            source_text = self.get_argument("input_url")
            detail = self.get_argument("detail",'False')

            if re.search("www.lagou.com/jobs/\d+.html",source_text):
                result = jdParser.parser(url=source_text,jdFrom="lagou",detail = detail)

            elif re.search(u"jobs.zhaopin.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="zhilian",detail = detail)

            elif re.search("jobs.51job.com/.+\d+.htm",source_text):
                result = jdParser.parser(url=source_text,jdFrom="51job",detail = detail)

            elif re.search("job.liepin.com/\d+",source_text) or re.search("a.liepin.com/\d+/job_\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="liepin",detail = detail)

            elif re.search("sz.58.com",source_text):
                result = jdParser.parser(url=source_text,jdFrom="58tc",detail = detail)

            elif re.search("jobui.com/job/\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="jobui",detail = detail)

            elif re.search("highpin.com/job/\d+",source_text):
                result = jdParser.parser(url=source_text,jdFrom="highpin",detail = detail)

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
            result = jdParser.parser(htmlContent = htmlContent,jdFrom=jdFrom)
        except Exception,e:
            result ={ "error":str(e)}
        self.write(result)


if __name__ == "__main__":

    jdParser = JdParser()


    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers = [(r'/',JdParserHandler),(r'/jdparser',JdParserHandler),(r"/jdUrl",JdUrlHandler)],
        template_path = os.path.join(os.path.dirname(__file__),"templates"),
        debug=True,
        autoescape=None,
        )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    print "starting tornado at port %d..." % options.port
    tornado.ioloop.IOLoop.instance().start()
