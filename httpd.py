from optparse import OptionParser
import logging
from os.path import isfile, isdir, join, getsize, splitext
from os import getcwd
import queue
import threading
import socket
from email.utils import formatdate


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
CONTENT_TYPES = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'swf': 'application/x-shockwave-flash',
}


class RequestWorker(threading.Thread):
    socket = None
    rfile = None
    address = None
    request_method = None
    request_path = None
    request_path_full = None
    request_protocol = None
    response_status = None
    response_headers = {}
    response_body = None
    allowed_methods = (GET, HEAD)

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
            ip, port = address
            self.address = f'{ip}:{port}'
            self.socket = sock
            self.rfile = sock.makefile('rb')
            self.request_method = None
            self.request_path = None
            self.request_path_full = None
            self.request_protocol = None
            self.response_status = None
            self.response_headers = {}
            self.response_body = None
            self.parse_request()
            self.process_request()
            self.set_response_headers()
            self.send_response()
            self.socket.close()
            self.rfile.close()
            self._queue.task_done()

    def parse_request(self):
        max_line_size = 65537
        request_line = self.rfile.readline(max_line_size).decode('utf-8')
        try:
            method, path, protocol = request_line.strip().split(' ')
        except ValueError:
            logging.error(f'{self.name} unable to parse request headers {request_line.strip().split(" ")}')
            return
        self.request_method = method.upper()
        self.request_path = path.strip('?')
        self.request_path_full = join(self.document_root, self.request_path[1:])
        self.request_protocol = protocol
        logging.info(f'{self.name} got new request {self.address} {method} {path} {protocol}')

    def process_request(self):
        if self.request_method not in self.allowed_methods:
            self.response_status = METHOD_NOT_ALLOWED
            return
        if isfile(self.request_path_full):
            self.response_status = OK
            self.response_body = self.request_path_full
            return
        if isdir(self.request_path_full):
            index_file = join(self.request_path_full, DEFAULT_INDEX)
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
            content_type = CONTENT_TYPES.get(extension[1:])
            if content_type:
                self.response_headers['Content-Type'] = content_type

    def send_response(self):
        message = MESSAGES.get(self.response_status)
        headers = f'HTTP/1.1 {self.response_status} {message}\r\n'
        for h in self.response_headers:
            headers += f'{h}: {self.response_headers.get(h)}\r\n'
        headers += '\r\n'
        self.socket.sendall(headers.encode())

        if self.response_body and self.request_method is not HEAD:
            with open(self.response_body, 'rb') as f:
                for line in f:
                    try:
                        self.socket.send(line)
                    except BrokenPipeError:
                        logging.info(f'{self.name} got broken pipe while processing request {self.address}')


class OtusServer:
    def __init__(self, ip, port, workers_num, document_root):
        self.server = None
        self.ip = ip
        self.port = port
        self.workers_num = workers_num
        self.document_root = document_root
        self.pool = []
        self.queue = queue.Queue()

    def serve_forever(self):
        self.create_worker_pool()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))
        self.server.listen(self.workers_num)
        while True:
            client_sock, address = self.server.accept()
            self.queue.put_nowait((client_sock, address))

    def create_worker_pool(self):
        for i in range(self.workers_num):
            worker = RequestWorker(self.queue, f'worker{i + 1}', self.document_root)
            worker.start()
            self.pool.append(worker)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-w", "--workers", action="store", type=int, default=10)
    op.add_option("-r", "--root", action="store", default=getcwd())
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-i", "--ip", action="store", default='0.0.0.0')
    op.add_option("-p", "--port", action="store", default=80)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )

    serv = OtusServer(opts.ip, opts.port, opts.workers, opts.root)
    serv.serve_forever()
