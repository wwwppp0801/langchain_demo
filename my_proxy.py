
import os
import sys
import logging
import signal
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.websocket
import tornado.gen
import tornado.httpclient
import socket
import asyncio
import hashlib
from urllib.parse import urlparse

#logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s %(message)s')
#logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s',filename="openai.log")
def getLogger():
    logger = logging.getLogger('proxy_logger')
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler('openai.log')
    fh.setLevel(logging.INFO)

    # 定义handler的输出格式
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fh.setFormatter(formatter)
    # 给logger添加handler
    logger.addHandler(fh)


    # 创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger=getLogger()


DEFAULT_BACKEND_SERVER="https://api.openai.com"
#DEFAULT_BACKEND_SERVER="https://www.baidu.com"
#DEFAULT_BACKEND_SERVER="https://www.baidu.com"


def get_proxy(url):
    url_parsed = urlparse(url, scheme='http')
    proxy_key = '%s_proxy' % url_parsed.scheme
    return os.environ.get(proxy_key)

def fetch_request(url, **kwargs):

    logger.debug("fetch_request %s",url)
    proxy = get_proxy(url)
    if proxy:
        logger.debug('Forward request via upstream proxy %s', proxy)
        tornado.httpclient.AsyncHTTPClient.configure(
            'tornado.curl_httpclient.CurlAsyncHTTPClient')
        host, port = parse_proxy(proxy)
        kwargs['proxy_host'] = host
        kwargs['proxy_port'] = port


    req = tornado.httpclient.HTTPRequest(url, **kwargs)
    client = tornado.httpclient.AsyncHTTPClient(defaults=dict(request_timeout=60))
    return client.fetch(req, raise_error=False)

def parse_proxy(proxy):
    proxy_parsed = urlparse(proxy, scheme='http')
    return proxy_parsed.hostname, proxy_parsed.port


cache_db = {}
def get_cache_key(request):
    key=request.uri + request.method + str(request.body)
    ## 计算key的sha1值
    key = hashlib.sha1(key.encode('utf-8')).hexdigest()
    return key

def set_cache(request,response):
    if response.code!=200 or response.headers.get('Content-Type','').find('application/json')==-1:
        return
    
    entry = {}
    entry['headers'] = dict(response.headers)
    entry['response_body'] = response.body
    logger.debug("set_cache %s",request.uri)
    logger.debug(request.body)
    
    cache_db[get_cache_key(request)] = entry

def get_cache(request):
    return cache_db.get(get_cache_key(request),None)
    

class ProxyHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS','CONNECT']

    @tornado.gen.coroutine
    def prepare(self):
        # Check if the request is using WebSocket protocol
        if self.request.headers.get('Upgrade', '').lower() == 'websocket':
            self.upgrade_protocol()
            return

        # Parse the request URL
        self.parsed_url = urlparse(self.request.uri)

        # Check if the request is using HTTPS protocol
        self.is_secure = self.request.headers.get('X-Scheme', '').lower() == 'https' or \
                self.request.headers.get('X-Forwarded-Proto', '').lower() == 'https' or \
                self.parsed_url.scheme == 'https'

        # Create a new HTTP client instance
        self.http_client = tornado.httpclient.AsyncHTTPClient(defaults=dict(request_timeout=60))
    
    async def connect(self):
        logger.debug('Start CONNECT to %s', self.request.uri)
        host, port = self.request.uri.split(':')
        client = self.request.connection.stream

        async def relay(reader, writer):
            try:
                while True:
                    data = await reader.read_bytes(1024*64, partial=True)
                    if writer.closed():
                        return
                    if data:
                        writer.write(data)
                    else:
                        break
            except tornado.iostream.StreamClosedError:
                pass

        async def start_tunnel():
            logger.debug('CONNECT tunnel established to %s', self.request.uri)
            client.write(b'HTTP/1.0 200 Connection established\r\n\r\n')
            await asyncio.gather(
                    relay(client, upstream),
                    relay(upstream, client)
            )
            client.close()
            upstream.close()

        async def on_proxy_response(data=None):
            if data:
                first_line = data.splitlines()[0]
                http_v, status, text = first_line.split(None, 2)
                if int(status) == 200:
                    logger.debug('Connected to upstream proxy %s', proxy)
                    await start_tunnel()
                    return

            self.set_status(500)
            self.finish()

        async def start_proxy_tunnel():
            upstream.write('CONNECT %s HTTP/1.1\r\n' % self.request.uri)
            upstream.write('Host: %s\r\n' % self.request.uri)
            upstream.write('Proxy-Connection: Keep-Alive\r\n\r\n')
            data = await upstream.read_until('\r\n\r\n')
            on_proxy_response(data)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        upstream = tornado.iostream.IOStream(s)

        proxy = get_proxy(self.request.uri)
        if proxy:
            proxy_host, proxy_port = parse_proxy(proxy)
            await upstream.connect((proxy_host, proxy_port))
            await start_proxy_tunnel()
        else:
            await upstream.connect((host, int(port)))
            await start_tunnel()

    async def get(self):
        await self.proxy_request('GET')

    async def post(self):
        await self.proxy_request('POST')

    async def put(self):
        await self.proxy_request('PUT')

    async def delete(self):
        await self.proxy_request('DELETE')

    async def head(self):
        await self.proxy_request('HEAD')

    async def options(self):
        await self.proxy_request('OPTIONS')

    async def proxy_request(self, method):

        logger.debug('Handle %s request to %s', self.request.method,
                     self.request.uri)

        def handle_response(response):
            if (response.error and not
                    isinstance(response.error, tornado.httpclient.HTTPError)):
                self.set_status(500)
                self.write('Internal server error:\n' + str(response.error))
            else:
                self.set_status(response.code, response.reason)
                self._headers = tornado.httputil.HTTPHeaders() # clear tornado default header

                for header, v in response.headers.get_all():
                    if header not in ('Content-Length', 'Transfer-Encoding', 'Content-Encoding', 'Connection'):
                        self.add_header(header, v) # some header appear multiple times, eg 'Set-Cookie'

                if response.body:
                    self.set_header('Content-Length', len(response.body))
                    self.write(response.body)
                    try:
                        import json
                        request_body_json=json.loads(self.request.body)
                        body_json=json.loads(response.body)
                        logger.info("openai messages: %s",json.dumps({"request":request_body_json,
                                                                      "response":body_json},
                                                                     ensure_ascii=False))
                        set_cache(self.request,response)
                    except Exception as e:
                        None
            self.finish()

        body = self.request.body
        if not body:
            body = None

        #try:
        #    import json
        #    body_json=json.loads(body)
        #    logger.info("openai messages: %s",json.dumps(body_json,ensure_ascii=False))
        #except Exception as e:
        #    None
                
        try:
            if 'Proxy-Connection' in self.request.headers:
                del self.request.headers['Proxy-Connection']

            if self.request.uri.startswith("/"):
                self.request.uri = DEFAULT_BACKEND_SERVER + self.request.uri
                parsed=urlparse(self.request.uri)
                self.request.headers["Host"]=parsed.netloc
                logger.debug("fetch_request %s %s %s",self.request.uri,str(self.request.headers),str(parsed))
                cache = get_cache(self.request)
                if cache != None:
                    logger.debug("cache hit %s",self.request.uri)
                    logger.debug(cache)
                    self.set_status(200)
                    self.set_header('Content-Type', cache["headers"].get('Content-Type',""))
                    self.write(cache['response_body'])
                    self.finish()
                    return

            resp = await fetch_request(
                self.request.uri,
                method=self.request.method, body=body,
                headers=self.request.headers, follow_redirects=False,
                allow_nonstandard_methods=True)
            handle_response(resp)
        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                handle_response(e.response)
            else:
                self.set_status(500)
                self.write('Internal server error:\n' + str(e))
                self.finish()



    def upgrade_protocol(self):
        # Create a new WebSocket client instance
        self.ws_client = tornado.websocket.websocket_connect(self.request.uri, on_message_callback=self.on_ws_message)

    @tornado.gen.coroutine
    def on_ws_message(self, message):
        # Write the WebSocket message back to the client
        self.write_message(message)

    def write_error(self, status_code, **kwargs):
        logger.error('Proxy request error: %s', self._reason)
        self.set_status(status_code)
        self.write('Internal Server Error')
        self.finish()

def make_app():
    return tornado.web.Application([
        (r'.*', ProxyHandler),
        ])

def start_proxy_on_thread(port=8123,address="127.0.0.1",default_backend_server="https://api.openai.com"):
    import threading
    import time
    global DEFAULT_BACKEND_SERVER
    DEFAULT_BACKEND_SERVER=default_backend_server
    print(port,address,default_backend_server)
    def start_ioloop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # # Create the HTTP server instance
        app = make_app()
        server = tornado.httpserver.HTTPServer(app, xheaders=True)

        # Set the server port and start listening
        server.bind(port=port,address=address)
        server.start(1)


        # Start the I/O loop
        logger.debug('Listening on port %d', port)
        tornado.ioloop.IOLoop.current().start()
    

    ioloop_thread = threading.Thread(target=start_ioloop)
    ioloop_thread.daemon=True
    ioloop_thread.start()
    # Register the signal handlers
    def stop():
        loop.stop()
        ioloop_thread.stop()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    
    def check_port(address, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((address, port))
        sock.close()
        return result == 0

    while True:
        if check_port(address, port):
            break
        time.sleep(0.1)
    return ioloop_thread



if __name__ == '__main__':
    #t=start_proxy_on_thread()
    import _env
    default_backend_server = _env.proxy_default_backend_server
    if default_backend_server == "":
        default_backend_server = "https://api.openai.com"
    # os.environ["http_proxy"]=_env.proxy_logger_host+":"+str(_env.proxy_logger_port)
    # os.environ["https_proxy"]=os.environ["http_proxy"]
    # print(os.environ['http_proxy'])
    t=start_proxy_on_thread(port=_env.proxy_logger_port,
                                   address=_env.proxy_logger_host,
                                   default_backend_server=default_backend_server,
                                   )
    t.join()
    
#    # Parse the command line arguments
#    # if len(sys.argv) < 2:
#    #     logger.error('Usage: python %s <port>', os.path.basename(sys.argv[0]))
#    #     sys.exit(1)
#    # port = int(sys.argv[1])
#    port = 8123
#    # # Create the HTTP server instance
#    app = make_app()
#    server = tornado.httpserver.HTTPServer(app, xheaders=True)
#
#    # Set the server port and start listening
#    server.bind(port)
#    server.start(1)
#
#    # Register the signal handlers
#    signal.signal(signal.SIGTERM, lambda sig, frame: tornado.ioloop.IOLoop.current().add_callback_from_signal(
#        lambda: tornado.ioloop.IOLoop.current().stop()))
#    signal.signal(signal.SIGINT, lambda sig, frame: tornado.ioloop.IOLoop.current().add_callback_from_signal(
#        lambda: tornado.ioloop.IOLoop.current().stop()))
#
#    # Start the I/O loop
#    logger.debug('Listening on port %d', port)
#    tornado.ioloop.IOLoop.current().start()
