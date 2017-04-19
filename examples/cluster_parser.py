import sys
sys.path.append('../')

from easpider import Spider
from bs4 import BeautifulSoup

spider = Spider()

@spider.parser
def parser(res):
    '''处理请求后的数据, 需要返回处理要保存的字典
        @params: res 是 requests 标准的 res
        @return: dict
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
