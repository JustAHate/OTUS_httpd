from optparse import OptionParser
import logging
from os.path import isfile, isdir, join, getsize, splitext, normpath
from os import getcwd
import queue
import threading
import socket
from email.utils import formatdate
import mimetypes


GET = 'GET'
HEAD = 'HEAD'
OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405
MESSAGES = {
    OK: 'OK',
    FORBIDDEN: 'Forbidden',
    NOT_FOUND: 'Not Found',
    METHOD_NOT_ALLOWED: 'Method Not Allowed'
}
DEFAULT_INDEX = 'index.html'
BACKLOG_SIZE = 100


class Request:
    address = None
    socket = None
    rfile = None
    method = None
    path = None
    path_full = None
    request_protocol = None
    document_root = None

    def __init__(self, sock, address, document_root):
        ip, port = address
        self.address = f'{ip}:{port}'
        self.socket = sock
        self.rfile = sock.makefile('rb')
        self.document_root = document_root

    def parse_request(self):
        max_line_size = 65537
        request_line = self.rfile.readline(max_line_size).decode('utf-8')
        try:
            method, path, protocol = request_line.strip().split(' ')
        except ValueError:
            logging.error(f'Unable to parse request headers {request_line}')
            return
        self.method = method.upper()
        self.path = normpath(path.strip('?'))
        self.path_full = join(self.document_root, self.path.lstrip('/'))
        self.request_protocol = protocol
        logging.info(f'Got new request {self.address} {method} {path} {protocol}')


class Response:
    response_status = None
    response_headers = {}
    response_body = None
    allowed_methods = (GET, HEAD)

    def __init__(self, request):
        self.request = request

    def process(self):
        if self.request.method not in self.allowed_methods:
            self.response_status = METHOD_NOT_ALLOWED
            return
        if isfile(self.request.path_full):
            self.response_status = OK
            self.response_body = self.request.path_full
            return
        if isdir(self.request.path_full):
            index_file = join(self.request.path_full, DEFAULT_INDEX)
            if isfile(index_file):
                self.response_status = OK
                self.response_body = index_file
                return
        self.response_status = NOT_FOUND

    def set_response_headers(self):
        self.response_headers = {
            'Date': formatdate(timeval=None, localtime=False, usegmt=True),
            'Server': 'Otus httpd',
            'Connection': 'close',
            'Content-Type': 'text/html; charset="utf8"',
            'Content-Length': 0
        }
        if self.response_body:
            self.response_headers['Content-Length'] = getsize(self.response_body)
            name, extension = splitext(self.response_body)
            content_type = mimetypes.types_map.get(extension)
            if content_type:
                self.response_headers['Content-Type'] = content_type

    def send(self):
        self.set_response_headers()
        message = MESSAGES.get(self.response_status)
        headers = f'HTTP/1.1 {self.response_status} {message}\r\n'
        for h in self.response_headers:
            headers += f'{h}: {self.response_headers.get(h)}\r\n'
        headers += '\r\n'
        self.request.socket.sendall(headers.encode())

        if self.response_body and self.request.method is not HEAD:
            with open(self.response_body, 'rb') as f:
                for line in f:
                    try:
                        self.request.socket.send(line)
                    except BrokenPipeError:
                        logging.info(f'Got broken pipe while processing request {self.request.address}')
        self.close()

    def close(self):
        self.request.rfile.close()
        self.request.socket.close()


class Worker(threading.Thread):
    def __init__(self, q, name, document_root):
        super().__init__()
        self._queue = q
        self.name = name
        self.document_root = document_root
        logging.info(f'Created worker {name}')

    def run(self):
        while True:
            try:
                sock, address = self._queue.get_nowait()
            except queue.Empty:
                continue
            request = Request(sock, address, self.document_root)
            request.parse_request()
            response = Response(request)
            response.process()
            response.send()
            self._queue.task_done()


class OtusServer:
    def __init__(self, ip, port, workers_num, document_root, backlog):
        self.server = None
        self.ip = ip
        self.port = port
        self.workers_num = workers_num
        self.document_root = document_root
        self.pool = []
        self.queue = queue.Queue()
        self.backlog_size = backlog

    def serve_forever(self):
        self.create_worker_pool()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen(self.backlog_size)
        while True:
            client_sock, address = self.server.accept()
            self.queue.put_nowait((client_sock, address))

    def create_worker_pool(self):
        for i in range(self.workers_num):
            worker = Worker(self.queue, f'worker{i + 1}', self.document_root)
            worker.start()
            self.pool.append(worker)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-w", "--workers", action="store", type=int, default=10)
    op.add_option("-r", "--root", action="store", default=getcwd())
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-i", "--ip", action="store", default='0.0.0.0')
    op.add_option("-p", "--port", action="store", default=80)
    op.add_option("-b", "--backlog", action="store", default=BACKLOG_SIZE)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    serv = OtusServer(opts.ip, opts.port, opts.workers, opts.root, opts.backlog)
    serv.serve_forever()
