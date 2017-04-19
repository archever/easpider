from gevent.pool import Pool
from gevent import socket


class SocketPool(object):

    def __init__(self):
        self.pool = Pool(1000)
        self.s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_server.bind(('', 9994))
        self.s_server.listen()
    
    def server(self):
        while True:
            sock, _ = self.s_server.accept()
            self.add_handler(sock)

    def listen(self, socket):
        while True:
            data = socket.recv(1024)
            print(data)
            if data == b'\n':
                self.shutdown()

    def add_handler(self, socket):
        if self.pool.full():
            raise Exception("At maximum pool size")
        else:
            self.pool.spawn(self.listen, socket)

    def shutdown(self):
        self.pool.kill()
    
    def run(self):
        self.pool.spawn(self.server).join()

if __name__ == '__main__':
    server = SocketPool()
    server.run()