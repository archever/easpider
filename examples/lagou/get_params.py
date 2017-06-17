
# import sys
# sys.path.append('../..')

import json
import logging
from pyquery import PyQuery
from collections import defaultdict

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

params_url = "https://www.lagou.com/jobs/list_"
all_cities_url = "https://www.lagou.com/jobs/allCity.html"

params = dict(
    px="new",
    city="%E5%8C%97%E4%BA%AC",
    district="%E6%9C%9D%E9%98%B3%E5%8C%BA",
    bizArea="%E5%BB%BA%E5%A4%96%E5%A4%A7%E8%A1%97",
    gj=""
)

areas = dict()
gj = list()
xl = list()

@spider.tasker(endpoint="city")
def tasker():
    ctx = spider.get_ctx(url=all_cities_url)
    yield ctx

@spider.parser
def parser(res, endpoint):
    global areas, gj, xl
    global params_url
    jq = PyQuery(res.content)
    if endpoint == "city":

        # 城市
        cities = jq(".city_list a")
        for idx, itm in enumerate(cities):
            city = cities.eq(idx).text()
            if city == "不限":
                continue
            areas[city] = dict()
            params = dict(px="new", city=city)
        # 测试
        params = dict(px="new", city="长沙")
        ctx = spider.get_ctx(url=params_url, params=params)
        spider.add_task(ctx, endpoint="district")
        print(areas)

        # 工作经验
        gj_list = jq("a[data-lg-tj-id='8r00']")
        print("=="*40)
        print(repr(gj_list))
        print("=="*40)
        for idx, itm in enumerate(gj_list):
            gj_data = gj_list.eq(idx).text().strip()
            if gj_data == "不限":
                continue
            gj.append(gj_data)
        with open("./data/gj.json", "w") as f:
            json.dump(gj, f)
        print(gj)

        # 学历要求
        xl_list = jq("a[data-lg-tj-id='8s00']")
        print("=="*40)
        print(repr(xl_list))
        print("=="*40)
        for idx, itm in enumerate(xl_list):
            xl_data = xl_list.eq(idx).text().strip()
            if xl_data == "不限":
                continue
            xl.append(xl_data)
        with open("./data/xl.json", "w") as f:
            json.dump(xl, f)
        print(xl)

    elif endpoint == "district":
        districts = jq(".detail-district-area a")
        city = jq.find(".current_city").text()
        for idx, itm in enumerate(districts):
            district = districts.eq(idx).text()
            if district == "不限":
                continue
            areas[city][district] = list()
            params = dict(px="new", city=city, district=district)
            ctx = spider.get_ctx(url=params_url, params=params)
            spider.add_task(ctx, endpoint="biz_area")
        print(areas)
    elif endpoint == "biz_area":
        biz_areas = jq.find(".detail-bizArea-area a")
        city = jq.find(".current_city").text()
        district = jq.find(".current_district").text()
        for idx, itm in enumerate(biz_areas):
            biz_area = biz_areas.eq(idx).text()
            if biz_area == "不限":
                continue
            areas[city][district].append(biz_area)
        print(areas)

@spider.saver
def saver(data, endpoint):
    pass

@spider.fail_handler
def failer(ctx, endpoint):
    with open("./data/failed_params_info.json", "a") as f:
        ctx["cookies"] = dict(ctx["cookies"])
        ret = json.dumps(ctx)
        f.write(ret)
        f.write("\n")

def save():
    with open("./data/params_info.json", "w") as f:
        json.dump(areas, f)

if __name__ == "__main__":
    spider.run()
    save()
