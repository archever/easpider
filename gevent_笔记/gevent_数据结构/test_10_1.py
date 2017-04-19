import gevent

def f1():
    x = 1
    print(x)

def f2():
    y = 2
    print(y)

    try:
        x
    except AttributeError:
        print("x is not local to f2")
    except Exception:
        print("x is not local to f2")

g1 = gevent.spawn(f1)
g2 = gevent.spawn(f2)

gevent.joinall([g1, g2])