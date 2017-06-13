
# 每次请求的延迟时间
SLEEP = 3
TIME_OUT = 3

# redis 配置
REDIS_CONF = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}

# 后台 队列, 本地用 queue, 分布用 redis
BACKEND = 'queue'
# BACKEND = 'redis'