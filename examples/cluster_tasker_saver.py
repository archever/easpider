import sys
sys.path.append('../')

from easpider import Spider
import json
from pymongo import MongoClient

spider = Spider()

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
    print('getting...{}'.format(type(data)))
    client = MongoClient('mongodb://localhost:27017')
    db = client.get_database('spider')
    cl = db.get_collection('neihan8')
    cl.insert(data)
    # filename = next(gen)
    # with open(filename, 'w') as fw:
    #     ret = json.dumps(data)
    #     fw.write(ret)

if __name__ == '__main__':
    spider.run()