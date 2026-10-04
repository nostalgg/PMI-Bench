"""Protected loopback fixture. No model inference or external network."""
import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@contextlib.contextmanager
def endpoint(mode):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length', '0')))
            self.send_response(200)
            self.end_headers()
            body = {'choices': [{'message': {'content': 'Private summary'}}]} if mode == 'valid' else {}
            self.wfile.write(json.dumps(body).encode())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)
