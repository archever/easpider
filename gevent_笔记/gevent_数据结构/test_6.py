import gevent
from gevent import getcurrent
from gevent.pool import Group

group1 = Group()

def hello_from(n):
    print('Size of group %s' % len(group1))
    print('Hello from Greenlet %s' % id(getcurrent()))

group1.map(hello_from, range(3))

def intensive(n):
    gevent.sleep(3-n)
    return 'task', n

print('Ordered')

group2 = Group()
for i in group2.imap(intensive, range(3)):
    print(i)

print('Unordered')

group3 = Group()
for i in group3.imap_unordered(intensive, range(3)):
    print(i)