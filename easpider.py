
import pickle
import logging

import redis
import requests

from functools import wraps

from gevent.pool import Pool
from gevent.queue import Queue
from gevent import spawn, monkey, sleep
from gevent.greenlet import Greenlet
import gevent

import config

monkey.patch_all(thread=False, select=False)

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s: %(levelname)-8s %(lineno)-4s %(message)s',  
    datefmt='%m-%d %H:%M',  
    # filename='easpider.log',  
    # filemode='w'
) 

class RedisQu:
    def __init__(self):
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
    def __init__(self, config=config):
        self.BACKEND = config.BACKEND
        self.SLEEP = config.SLEEP
        self.parser_fn = None
        self.saver_fn = None
        self.task_fn = None
        self.session_fn = None
        self.fail_handler_fn = None
        self.init_session_fn = None
        self.qu = None
        self.ctx = dict()
    
    def add_task(self, ctx, endpoint="main"):
        ctx.update(dict(endpoint=endpoint))
        self.qu.put('task', ctx)
    
    def parser(self, fn):
        def wrapper(res):
            endpoint = res.endpoint
            ret = fn(res)
            return dict(data=ret, endpoint=endpoint)
        self.parser_fn = wrapper
    
    def saver(self, fn):
        def wrapper(data):
            fn(data)
            logging.info('saving done {}'.format(type(data)))
        self.saver_fn = wrapper

    def tasker(self, endpoint="main"):
        def inner(fn):
            def wrapper():
                for task in fn():
                    task["endpoint"] = endpoint
                    self.qu.put('task', task)
                logging.info('add to {} done'.format(endpoint))
            self.task_fn = wrapper
        return inner
    
    def fail_handler(self, fn):
        def wrapper(ctx):
            ctx_ = fn(ctx)
            if ctx_:
                self.qu.put('task', ctx_)
        self.fail_handler_fn = wrapper
    
    def run(self):
        logging.info('spider runnning')
        if self.BACKEND == 'redis':
            qu = RedisQu()
        elif self.BACKEND == 'queue':
            qu = LocalQu()
        else:
            logging.error('not a valid backend setting: {}'.format(self.BACKEND))
            exit(1)
        self.qu = qu

        join_list = []

        if self.task_fn:
            self.task_fn()
        elif config.BACKEND == 'queue':
            logging.error('tasker is not defined')
            raise Exception('tasker is not defined')
        else:
            logging.warn('tasker is not defined if you are using redis for cluster crawing ignore this wranning')

        if self.parser_fn:
            dealer = Dealer(qu)
            dealer.fail_handler = self.fail_handler_fn
            dealer.parser = self.parser_fn
            dealer.start()
            join_list.append(dealer)
        elif config.BACKEND == 'queue':
            logging.error('parser is not defined')
            raise Exception('parser is not defined')
        else:
            logging.warn('parser is not defined, if you are using redis for cluster crawing ignore this wranning')

        if self.saver_fn:
            saver = Saver(qu)
            saver.saver = self.saver_fn
            saver.start()
            join_list.append(saver)
        elif config.BACKEND == 'queue':
            logging.error('saver is not defined')
            raise Exception('saver is not defined')
        else:
            logging.warn('saver is not defined, if you are using redis for cluster crawing ignore this wranning')
        try:
            gevent.joinall(join_list)
        except:
            logging.info('all done')

class Dealer(Greenlet):
    '''
    gevent 处理任务 and parser
    '''
    def __init__(self, qu):
        super().__init__()
        self.qu = qu
        self.pool = Pool()
        self.cookies = requests.cookies.RequestsCookieJar()
        self.TIME_OUT = config.TIME_OUT
    
    def deal_tasks(self, ctx):
        endpoint = ctx.pop("endpoint")
        try:
            if ctx.get('cookies'):
                ctx['cookies'].update(self.cookies)
                print(ctx['cookies'])
            res = requests.request(**ctx, timeout=self.TIME_OUT)
            res.endpoint = endpoint
            self.cookies.update(res.cookies)
            logging.info('getting done {}'.format(res))
        except Exception as err:
            ctx["endpoint"] = endpoint
            self.fail_handler and self.fail_handler(ctx)
            logging.error('{} fialed with {} '.format(ctx['url'], err))
        else:
            if res.status_code == 200:
                try:
                    data = self.parser(res)
                except Exception as err:
                    self.fail_handler and self.fail_handler(ctx)
                    logging.error('{} parsing fialed with {} '.format(ctx['url'], err))
                else:
                    if data:
                        self.qu.put('res', data)
                        logging.info('parsing done {}'.format(ctx['url']))
                    else:
                        self.fail_handler and self.fail_handler(ctx)
                        logging.error('{} parsing returns None '.format(ctx['url']))
            else:
                self.fail_handler and self.fail_handler(ctx)
                logging.error('{} fialed with {} and will try again'.format(ctx['url'], res))

    def shutdown(self):
        self.pool.kill()

    def _run(self):
        logging.info('dealer running')
        for ctx in self.qu.get('task'):
            self.pool.spawn(self.deal_tasks, ctx)
            sleep(config.SLEEP)
        logging.info('dealer done')

class Saver(Greenlet):
    def __init__(self, qu):
        super().__init__()
        self.qu = qu

    def _run(self):
        logging.info('saver running')
        for data in self.qu.get('res'):
            if data:
                self.saver(data)
        logging.info('save done')
