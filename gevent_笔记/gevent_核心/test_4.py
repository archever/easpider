import gevent.monkey
gevent.monkey.patch_socket()

import gevent
from urllib import request
import json

def fetch(pid):
    response = request.urlopen('http://www.baidu.com')
    result = response.read()
    print('Process %s: %s' % (pid, len(result)))
    return len(result)

def synchronous():
    for i in range(1,5):
        fetch(i)

def asynchronous():
    threads = []
    for i in range(1,5):
        threads.append(gevent.spawn(fetch, i))
    gevent.joinall(threads)

print('Synchronous:')
synchronous()

print('Asynchronous:')
asynchronous()