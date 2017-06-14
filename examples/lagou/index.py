
# import sys
# sys.path.append('../..')

import json
import logging
from pyquery import PyQuery

from easpider import Spider
import config

spider = Spider(config=config)

# spider.ctx 一个全局的上下文, 可以通过 get_ctx 使用这个 ctx
spider.ctx["method"] = "GET"
spider.ctx["headers"] = {
    "Host": "www.lagou.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
}
spider.ctx["cookies"] = {
    "user_trace_token": "20170613232027-d458fe9b-504b-11e7-9b38-5254005c3644"
}

# detail_url = "https://www.lagou.com/jobs/{position_id}.html"
list_url = "https://www.lagou.com/zhaopin/Python/{page}/"

@spider.tasker(endpoint="list")
def tasker():
    """
    定义列表页任务
    """
    start = int(input("start_page:"))
    end = int(input("end_page:"))
    for i in range(start, end+1):
        yield spider.get_ctx(url=list_url.format(page=i))

@spider.parser
def parser(res, endpoint):
    """
    解析res
    """
    jq = PyQuery(res.content)
    if endpoint == "detail":
        ret = dict()
        ret["advantage"] = jq.find(".job-advantage").html()
        ret["detail"] = jq.find(".job_bt").html()
        ret["address"] = jq.find(".job-address").html()
        ret["content"] = jq.find(".position-content-l").html()
        ret["company"] = jq.find(".job_company").html()
        return ret
    elif endpoint == "list":
        links = jq.find(".position_link")
        for idx, itm in enumerate(links):
            ctx = spider.get_ctx(url=links.eq(idx).attr("href"))
            spider.add_task(ctx, endpoint="detail")

@spider.saver
def saver(data, endpoint):
    """
    保存data
    """
    if endpoint == "detail":
        with open("./data/test.json", "a") as f:
            ret = json.dumps(data)
            f.write(ret)
            f.write("\n")

@spider.fail_handler
def failer(ctx, endpoint):
    """
    错误处理, 可以返回一个 新的 ctx, 或者不返回
    """
    with open("./data/failed.json", "a") as f:
        ctx["cookies"] = dict(ctx["cookies"])
        ret = json.dumps(ctx)
        f.write(ret)
        f.write("\n")

if __name__ == "__main__":
    # 启动爬虫
    spider.run()
