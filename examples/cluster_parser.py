import sys
sys.path.append('../')

from easpider import Spider
from bs4 import BeautifulSoup
import random

spider = Spider()

@spider.fail_handler
def fail_handler(ctx):
    proxies_list = [
        # "http": "http://user:pass@10.10.1.10:3128/",
        # {'http': 'mr_mao_hacker:sffqry9r@122.232.216.182:24224'},
        # {'http': '115.231.105.109:8081'},
        # {'http': '218.22.219.133:808'},
        # {'http': '121.61.101.240:808'},
        # {'http': '175.155.25.54:808'},
        # {'http': '115.220.4.104:808'},
        # {'http': '124.88.67.81:80'},
        # {'http': '122.228.179.178:80'},
        # {'http': '49.86.62.24:808'},
        # {'http': '175.155.24.2:808'},
        # {'http': '120.43.48.92:808'},
        # {'http': '222.66.22.82:8090'},
        # {'http': '119.5.1.6:808'},
        # {'http': '61.191.173.31:808'},
        # {'http': '221.216.94.77:808'},
        None
    ]
    ctx['proxies'] = random.choice(proxies_list)
    return ctx

@spider.parser
def parser(res):
    '''
    @params: res requests 标准的 res
    @return json
    '''
    try:
        html = res.content.decode('gb2312')
    except:
        html = res.content.decode('gbk')
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('ul.piclist li')
    ret = []
    for i in items:
        title = i.select('a')[0].get_text().strip()
        article = i.select('.f18.mb20')[0].get_text().strip()
        ret.append(dict(title=title, article=article))
    return ret

if __name__ == '__main__':
    spider.run()
