# easpider 易用的爬虫框架

简单易用的爬虫框架
* 实现 redis 分布式, 或者本地54队列爬取
* gevent 协程并发
* 自定义异常处理

## 使用说明
### 配置
`settings.py` 配置文件

```python
# 每次请求的延迟时间
SLEEP = 0
TIME_OUT = 10
# redis 配置
REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}
# 后台 队列, 本地用 queue, 分布用 redis
# BACKEND = 'queue'
BACKEND = 'redis'
```

后台队列支持 redis 分布式, 和本地的 queue

### 快速开始

```python
from easpider import Spider
# 初始化 spider
spider = Spider()

@spider.tasker
def tasker():
    '''添加任务到 task 队列'''
    # 创建任务, 组装标准的 requests 参数
    ctx = dict(
        method='GET',
        url='http://...',
        params=dict(),
        data=dict()
        cookies=dict(),
        proxies=dict(),
        headers=dict()
    )
    yield ctx

@spider.fail_handler
def fail_handler(ctx):
    '''错误处理, 接受 ctx 修改后返回 这个 ctx 重新处理'''
    proxies_list = [
        # "http": "http://user:pass@10.10.1.10:3128/",
        # {'http': 'mr_mao_hacker:sffqry9r@122.232.216.182:24224'},
        None
    ]
    ctx['proxies'] = random.choice(proxies_list)
    return ctx

@spider.parser
def parser(res):
    '''接收 task 队列消息 获得请求后 处理 添加到 res 队列'''
    # 处理请求结果, 返回字典, res 是 requests 标准的 res
    return dict()

@spider.saver
def saver(data):
    '''接受 res 队列消息'''
    # 接受 parser 处理后的 信息 dict
    # 保存数据, 数据库, 或者本地文件

if __name__ == '__main__':
    # 启动爬虫任务
    spider.run()
```

以上几个任务 可以用 redis 做分布单独处理
在主机端需要实现, saver, tasker 方法, 在从机端 需要实现 parser, fail_handler 方法

### demo

`all_in_demo`: 实现本地 爬取

`cluster_tasker_saver`: 实现 主服务器分配任务, 获得结果             
`cluster_parser`: 实现 slaver 服务器处理任务, 可以运行在多个主机