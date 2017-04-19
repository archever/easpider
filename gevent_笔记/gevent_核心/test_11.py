import gevent
from gevent import Timeout

time_to_wait = 2 # seconds

class TooLong(Exception):
    pass

with Timeout(time_to_wait, TooLong):
    gevent.sleep(10)