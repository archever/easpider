
import json
import logging

import redis
import requests

from functools import wraps

from gevent.pool import Pool
from gevent.queue import Queue
from gevent import spawn, monkey, sleep
from gevent.greenlet import Greenlet
import gevent

import settings

monkey.patch_socket()

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s: %(levelname)-8s %(lineno)-4s %(message)s',  
    datefmt='%m-%d %H:%M',  
    # filename='easpider.log',  
    # filemode='w'
) 

class RedisQu:
    def __init__(self):
        pool = redis.ConnectionPool(**settings.REDIS_CONF)
        self.r = redis.StrictRedis(connection_pool=pool) 
    
    def get(self, qu_name):
        while 1:
            rev = self.r.brpop(qu_name, 0)
            raw_ctx = rev[1]
            ctx = json.loads(raw_ctx)
            yield ctx
    
    def put(self, qu_name, ctx):
        self.r.lpush(qu_name, json.dumps(ctx))

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
            ctx = json.loads(raw_ctx)
            yield ctx

    def put(self, qu_name, ctx):
        qu = self.get_qu(qu_name)
        qu.put(json.dumps(ctx))
                

class Spider:
    def __init__(self):
        self.BACKEND = settings.BACKEND
        self.SLEEP = settings.SLEEP
        self.parser_fn = None
        self.saver_fn = None
        self.task_fn = None
        self.session_fn = None
        self.fail_handler_fn = None
        self.qu = None
    
    def parser(self, fn):
        '''@decorator'''
        def wrapper(res):
            ret = fn(res)
            logging.debug('put in res {}'.format(len(ret)))
            self.qu.put('res', ret)
        self.parser_fn = wrapper
    
    def saver(self, fn):
        '''@decorator'''
        def wrapper(data):
            fn(data)
            logging.info('saving done {}'.format(type(data)))
        self.saver_fn = wrapper
    
    def tasker(self, fn):
        '''@decorator'''
        def wrapper():
            for task in fn():
                self.qu.put('task', task)
            logging.info('add tasks done')
        self.task_fn = wrapper
    
    def fail_handler(self, fn):
        '''@decorator'''
        def wrapper(ctx):
            ctx = fn(ctx)
            logging.warn('fialed and will try again {}'.format(ctx['url']))
            self.qu.put('task', ctx)
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
        elif settings.BACKEND == 'queue':
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
        elif settings.BACKEND == 'queue':
            logging.error('parser is not defined')
            raise Exception('parser is not defined')
        else:
            logging.warn('parser is not defined, if you are using redis for cluster crawing ignore this wranning')

        if self.saver_fn:
            saver = Saver(qu)
            saver.saver = self.saver_fn
            saver.start()
            join_list.append(saver)
        elif settings.BACKEND == 'queue':
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
        self.TIME_OUT = settings.TIME_OUT
    
    def deal_tasks(self, ctx):
        try:
            res = requests.request(**ctx, timeout=self.TIME_OUT)
            logging.info('getting done {}'.format(res))
        except Exception as err:
            self.fail_handler and self.fail_handler(ctx)
            logging.error('{} fialed with {} and will be handled agian'.format(ctx['url'], err))
        else:
            if res.status_code == 200:
                data = self.parser(res)
                self.qu.put('res', data)
                logging.info('parsing done {}'.format(ctx['url']))
            else:
                self.fail_handler and self.fail_handler(ctx)
                logging.error('{} fialed with {} and will try again'.format(ctx['url'], res))

    def shutdown(self):
        self.pool.kill()

    def _run(self):
        logging.info('dealer running')
        for ctx in self.qu.get('task'):
            self.pool.spawn(self.deal_tasks, ctx)
            sleep(settings.SLEEP)
        logging.info('dealer done')

class Saver(Greenlet):
    '''处理 数据队列'''
    def __init__(self, qu):
        super().__init__()
        self.qu = qu

    def _run(self):
        logging.info('saver running')
        for data in self.qu.get('res'):
            if data:
                self.saver(data)
        logging.info('save done')
