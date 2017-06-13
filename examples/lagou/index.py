
import sys
sys.path.insert(0, '../..')
import json
import logging
from pyquery import PyQuery

from easpider import Spider
import config

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s: %(levelname)-8s %(lineno)-4s %(message)s',  
    datefmt='%m-%d %H:%M',  
    # filename='easpider.log',  
    # filemode='w'
) 

spider = Spider(config=config)

ctx = dict()
ctx["method"] = "GET"
ctx["headers"] = {
    "Host": "www.lagou.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
}
ctx["cookies"] = {
    "user_trace_token": "20170613232027-d458fe9b-504b-11e7-9b38-5254005c3644"
}

detail_url = "https://www.lagou.com/jobs/{position_id}.html"
list_url = "https://www.lagou.com/zhaopin/Python/{page}/"

@spider.tasker("list")
def tasker():
    start = int(input("start_page:"))
    end = int(input("end_page:"))
    for i in range(start, end+1):
        ctx_ = dict()
        ctx_.update(ctx)
        ctx_["url"] = list_url.format(page=i)
        yield ctx_

@spider.parser
def parser(res):
    if res.endpoint == "detail":
        jq = PyQuery(res.content)
        ret = dict()
        ret["advantage"] = jq.find(".job-advantage").html()
        ret["detail"] = jq.find(".job_bt").html()
        ret["address"] = jq.find(".job-address").html()
        ret["content"] = jq.find(".position-content-l").html()
        ret["company"] = jq.find(".job_company").html()
        return ret
    elif res.endpoint == "list":
        jq = PyQuery(res.content)
        print(res.url)
        links = jq.find(".position_link")
        for idx, itm in enumerate(links):
            ctx_ = dict()
            ctx_.update(ctx)
            ctx_["url"] = links.eq(idx).attr("href")
            print(ctx_["url"])
            spider.add_task(ctx_, "detail")

@spider.saver
def saver(ret):
    if ret["endpoint"] == "detail":
        with open("./data/test.json", "a") as f:
            ret = json.dumps(ret["data"])
            f.write(ret)
            f.write("\n")

@spider.fail_handler
def failer(ctx):
    with open("./data/failed.json", "a") as f:
        ctx["cookies"] = dict(ctx["cookies"])
        ret = json.dumps(ctx)
        f.write(ret)
        f.write("\n")

if __name__ == "__main__":
    spider.run()

