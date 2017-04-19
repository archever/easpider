import sys
sys.path.append('../')

from easpider import Spider
import json
from bs4 import BeautifulSoup

spider = Spider()

@spider.parser
def parser(res):
    '''res 是 requests 标准的 res
    return json
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

@spider.tasker
def add_task():
    '''添加爬虫任务, 需要用 yield 返回结果
    ctx 是 requests 对象 request方法的 标准参数
    ctx == dict{
        method: ...,
        url: ...,
        headers: ..., 
        proxies: ...,
        params: ...,
        data: ...,
        cookies: ...,
    }
    '''
    ctx = dict(method='GET')
    print('http://www.neihan8.com')
    start = int(input('start page:'))
    end = int(input('end page:'))
    for i in range(start, end+1):
        url = 'http://www.neihan8.com/article/list_5_{}.html'.format(i)
        ctx['url'] = url
        yield ctx

def get_filename():
    counter = 0
    while 1:
        yield 'task_{}.json'.format(counter)
        counter += 1

gen = get_filename()

@spider.saver
def saver(data):
    '''获得 parser 返回的数据 字典
    @params data: dict
    '''
    filename = next(gen)
    with open(filename, 'w') as fw:
        ret = json.dumps(data)
        fw.write(ret)

if __name__ == '__main__':
    spider.run()
