
import pickle
import requests
import logging

from functools import wraps

from gevent.pool import Pool
from gevent.queue import Queue
from gevent import spawn, monkey, sleep
from gevent.greenlet import Greenlet
import gevent

import config

monkey.patch_all(thread=False, select=False)

class RedisQu:
    """
    redis queue 封装
    """
    def __init__(self):
        import redis
        pool = redis.ConnectionPool(**config.REDIS_CONF)
        self.r = redis.StrictRedis(connection_pool=pool) 
    
    def get(self, qu_name):
        while 1:
            rev = self.r.brpop(qu_name, 0)
            raw_ctx = rev[1]
            ctx = pickle.loads(raw_ctx)
            yield ctx
    
    def put(self, qu_name, ctx):
        self.r.lpush(qu_name, pickle.dumps(ctx))

class LocalQu:
    """
    local queue 封装
    """
    def __init__(self):
        self.task = Queue()
        self.res = Queue()
    
    def get_qu(self, qu_name):
        return self.__dict__.get(qu_name)
    
    def get(self, qu_name):
        qu = self.get_qu(qu_name)
        while 1:
            raw_ctx = qu.get()
            ctx = pickle.loads(raw_ctx)
            yield ctx

    def put(self, qu_name, ctx):
        qu = self.get_qu(qu_name)
        qu.put(pickle.dumps(ctx))
                

class Spider:
    """
    爬虫 main
    """
    def __init__(self, config=config):
        self.BACKEND = config.BACKEND
        self.SLEEP = config.SLEEP
        self.TIMEOUT = config.TIMEOUT
        self.parser_fn = None
        self.saver_fn = None
        self.task_fn = None
        self.fail_handler_fn = None
        self.qu = None
        self.ctx = dict(timeout=self.TIMEOUT)
    
    def get_ctx(self, **kws):
        """
        包装 ctx, 返回新的字典
        """
        ctx = dict(kws)
        ctx.update(self.ctx)
        return ctx
    
    def add_task(self, ctx, endpoint="main"):
        """
        添加任务
        """
        self.qu.put('task', (endpoint, ctx))
    
    def parser(self, fn):
        """
        装饰器: 解析任务
        """
        def wrapper(res, endpoint):
            ret = fn(res, endpoint)
            logging.info('parsing done {} to {}'.format(res.url, endpoint))
            return ret
        self.parser_fn = wrapper
    
    def saver(self, fn):
        """
        装饰器: 保存任务
        """
        def wrapper(data, endpoint):
            fn(data, endpoint)
            logging.info('saving done {} to {}'.format(type(data), endpoint))
        self.saver_fn = wrapper

    def tasker(self, endpoint="main"):
        """
        装饰器: 分配任务
        """
        def inner(fn):
            def wrapper():
                for ctx in fn():
                    self.qu.put('task', (endpoint, ctx))
                logging.info('add {} to {}'.format(ctx["url"], endpoint))
            self.task_fn = wrapper
        return inner
    
    def fail_handler(self, fn):
        """
        装饰器: 错误处理
        """
        def wrapper(ctx, endpoint):
            ctx_ = fn(ctx, endpoint)
            if ctx_:
                self.qu.put('task', (endpoint, ctx_))
        self.fail_handler_fn = wrapper
    
    def run(self):
        """
        启动爬虫
        """
        logging.info('spider runnning')
        # 初始化队列
        if self.BACKEND == 'redis':
            qu = RedisQu()
        elif self.BACKEND == 'queue':
            qu = LocalQu()
        else:
            logging.error('not a valid backend setting: {}'.format(self.BACKEND))
            exit(1)
        self.qu = qu

        # 初始化 分配任务函数
        if self.task_fn:
            self.task_fn()
        elif config.BACKEND == 'queue':
            logging.error('tasker is not defined')
            raise Exception('tasker is not defined')
        else:
            logging.warn('tasker is not defined if you are using redis for cluster crawing ignore this wranning')
        
        # 初始化 解析任务函数
        if self.parser_fn:
            dealer = Dealer(qu)
            dealer.fail_handler = self.fail_handler_fn
            dealer.parser = self.parser_fn
            dealer.start()
        elif config.BACKEND == 'queue':
            logging.error('parser is not defined')
            raise Exception('parser is not defined')
        else:
            logging.warn('parser is not defined, if you are using redis for cluster crawing ignore this wranning')

        # 初始化 保存任务函数
        if self.saver_fn:
            saver = Saver(qu)
            saver.saver = self.saver_fn
            saver.start()
        elif config.BACKEND == 'queue':
            logging.error('saver is not defined')
            raise Exception('saver is not defined')
        else:
            logging.warn('saver is not defined, if you are using redis for cluster crawing ignore this wranning')
        
        gevent.wait()
        logging.info('all done')

class Dealer(Greenlet):
    """
    网络请求, 任务处理
    """
    def __init__(self, qu):
        super().__init__()
        self.qu = qu
        self.pool = Pool()
        self.cookies = requests.cookies.RequestsCookieJar()
    
    def deal_tasks(self, ctx, endpoint):
        if ctx.get('cookies'):
            ctx['cookies'].update(self.cookies)
            logging.debug(ctx["cookies"])
        try:
            # 发起请求
            res = requests.request(**ctx)
            # 更新 cookies
            self.cookies.update(res.cookies)
            logging.info('getting done {}:{} to {}'.format(res, res.url, endpoint))
        except Exception as err:
            self.fail_handler and self.fail_handler(ctx, endpoint)
            logging.error('fialed {} to {} with {} '.format(ctx['url'], endpoint, err))
        else:
            if res.status_code == 200:
                try:
                    data = self.parser(res, endpoint)
                except Exception as err:
                    self.fail_handler and self.fail_handler(ctx, endpoint)
                    logging.error('fialed {} to {} with {} '.format(ctx['url'], endpoint, err))
                else:
                    if data:
                        self.qu.put('res', (endpoint, data))
                        logging.info('parsing done {} to {}'.format(ctx['url'], endpoint))
                    else:
                        self.fail_handler and self.fail_handler(ctx, endpoint)
                        logging.error('parsing {} returns None to {}'.format(ctx['url'], endpoint))
            else:
                self.fail_handler and self.fail_handler(ctx, endpoint)
                logging.error('fialed {} to {} with {} '.format(ctx['url'], endpoint, err))

    def shutdown(self):
        self.pool.kill()

    def _run(self):
        """
        启动 dealer
        """
        logging.info('dealer running')
        for endpoint, ctx in self.qu.get('task'):
            self.pool.spawn(self.deal_tasks, ctx, endpoint)
            sleep(config.SLEEP)
        logging.info('dealer done')

class Saver(Greenlet):
    def __init__(self, qu):
        super().__init__()
        self.qu = qu

    def _run(self):
        """
        启动 saver
        """
        logging.info('saver running')
        for ret in self.qu.get('res'):
            if ret:
                self.saver(ret[1], ret[0])
        logging.info('save done')
