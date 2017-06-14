
import logging

# 日志配置文件
logging.basicConfig(
    level=logging.INFO,  
    format='[%(asctime)s: %(levelname)-8s %(lineno)-4s] %(message)s',
    datefmt='%m-%d %H:%M',
    # filename='easpider.log',  
    # filemode='w'
)

# 每次请求的延迟时间
SLEEP = 2
# 请求的超时时间
TIMEOUT = 3

# redis 配置
REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}

# 后台 队列, 本地用 queue, 分布用 redis
BACKEND = 'queue'
# BACKEND = 'redis'