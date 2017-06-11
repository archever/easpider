import sys
sys.path.append('../')

from easpider import Spider
from bs4 import BeautifulSoup
import random

spider = Spider()

@spider.fail_handler
def fail_handler(ctx):
    with open('failed.json', 'a') as fa:
       data = json.dumps(ctx['data']) + ', \n'
       fa.write(data)

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
