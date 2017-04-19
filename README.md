# easpider 易用的爬虫框架

## 使用说明
### 配置
`settings.py` 配置文件
```python
# 每次请求的延迟时间
SLEEP = 0

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

### demo

```python
from easpider import Spider
# 初始化 spider
spider = Spider()

@spider.tasker
def tasker():
    '''添加任务到 task 队列'''
    # 创建任务, 组装标准的 requests 参数
    yield ctx

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

以上三个任务 可以用 redis 做分布单独处理

## TODO

* 使用协程 处理任务