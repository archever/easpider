
import json
import logging
from queue import Queue

# from gevent import spawn, monkey, sleep
from time import sleep
import redis
import requests

import settings
from functools import wraps
from threading import Thread

# monkey.patch_socket()
# monkey.patch_thread()

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
            try:
                rev = self.r.brpop(qu_name, 0)
                raw_ctx = rev[1]
            except Exception as err:
                logging.exception(err)
            else:
                ctx = json.loads(raw_ctx)
                yield ctx
    
    def put(self, qu_name, ctx):
        logging.debug('put in {} count: {}'.format(qu_name, self.r.llen(qu_name)))
        self.r.lpush(qu_name, json.dumps(ctx))

class LocalQu:
    def __init__(self):
        self.task = Queue()
        self.res = Queue()
    
    def get_qu(self, qu_name):
        try:
            qu = self.__dict__.get(qu_name)
        except Exception as err: 
            raise er
        return qu
    
    def get(self, qu_name):
        qu = self.get_qu(qu_name)
        while 1:
            try:
                raw_ctx = qu.get()
            except Exception as err:
                logging.exception(err)
            else:
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
                logging.debug('put in task {}'.format(type(task)))
                self.qu.put('task', task)
            logging.info('add tasks done')
        self.task_fn = wrapper
    
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

        if self.task_fn:
            self.task_fn()
        elif settings.BACKEND == 'queue':
            logging.error('tasker is not defined')
            raise Exception('tasker is not defined')
        else:
            logging.warn('tasker is not defined if you are using redis for cluster crawing ignore this wranning')
        
        if self.parser_fn:
            dealer = Dealer(qu)
            dealer.parser = self.parser_fn
            dealer.start()
        elif settings.BACKEND == 'queue':
            logging.error('parser is not defined')
            raise Exception('parser is not defined')
        else:
            logging.warn('parser is not defined if you are using redis for cluster crawing ignore this wranning')
        
        if self.saver_fn:
            saver = Saver(qu)
            saver.saver = self.saver_fn
            saver.start()
        elif settings.BACKEND == 'queue':
            logging.error('saver is not defined')
            raise Exception('saver is not defined')
        else:
            logging.warn('saver is not defined if you are using redis for cluster crawing ignore this wranning')

class Dealer(Thread):
    '''
    gevent 处理任务 and parser
    '''
    def __init__(self, qu):
        super().__init__()
        self.qu = qu
    
    def deal_tasks(self, ctx):
        try:
            res = requests.request(**ctx)
            logging.info('getting done {}'.format(res))
        except Exception as err:
            self.qu.put('task', ctx)
            logging.error('{} fialed with {} and, it will try again'.format(ctx, err))
            raise err
        else:
            data = self.parser(res)
            self.qu.put('res', data)
            logging.info('parsing done {}'.format(ctx['url']))

    def run(self):
        logging.info('dealer running')
        for ctx in self.qu.get('task'):
            # spawn(self.deal_tasks, ctx)
            self.deal_tasks(ctx)
            sleep(settings.SLEEP)
        logging.info('dealer done')

class Saver(Thread):
    '''处理 数据队列'''
    def __init__(self, qu):
        super().__init__()
        self.qu = qu
    
    def run(self):
        logging.info('saver running')
        for data in self.qu.get('res'):
            if data:
                self.saver(data)
        logging.info('save done')
