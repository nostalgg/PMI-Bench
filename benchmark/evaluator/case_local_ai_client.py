import contextlib
import importlib
import io
import json
import os
import socket
import threading
import time
import traceback
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock


@contextlib.contextmanager
def endpoint(status=200, body=None, headers=None, delay=0):
    requests = []
    if body is None:
        body = json.dumps({'choices': [{'message': {'content': 'Sample summary'}}]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self):
            content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            requests.append({'method': self.command, 'path': self.path, 'body': content,
                             'content_type': self.headers.get('Content-Type')})
            time.sleep(delay)
            try:
                self.send_response(status)
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        do_POST = respond
        do_GET = respond

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module('client')
        self.Client = self.module.LocalAIClient
        self.Error = self.module.LocalAIError

    def test_configured_model_and_endpoint(self):
        with endpoint() as (url, requests):
            text = 'Ordine sintetico: quantità 7, cliente C01.'
            self.assertEqual(self.Client(url, 'company-model-v2').summarize(text), 'Sample summary')
            self.assertEqual(len(requests), 1)
            request = requests[0]
            self.assertEqual((request['method'], request['path']), ('POST', '/v1/chat/completions'))
            self.assertEqual(request['content_type'], 'application/json')
            payload = json.loads(request['body'])
            self.assertEqual(payload['model'], 'company-model-v2')
            self.assertIn({'role': 'user', 'content': text}, payload['messages'])

    def test_localhost_and_slash(self):
        with endpoint() as (url, requests):
            url = url.replace('127.0.0.1', 'localhost') + '/'
            self.assertEqual(self.Client(url, 'm').summarize('test'), 'Sample summary')
            self.assertEqual(len(requests), 1)
        self.Client('http://[::1]:8080/v1', 'm')  # Constructor only: IPv6 serving is not assumed.

    def test_constraint_reject_nonlocal_urls(self):
        urls = ['https://example.com:443/v1', 'http://example.com:80/v1',
                'http://localhost.example.com:80/v1', 'http://127.0.0.2:80/v1',
                'http://user:pass@127.0.0.1:80/v1', 'http://127.0.0.1:80/v1?key=x',
                'http://127.0.0.1:80/v1#fragment', 'file:///tmp/model',
                'http://127.0.0.1/v1', 'http://127.0.0.1:80/other']
        for url in urls:
            with self.assertRaises(ValueError, msg=url):
                self.Client(url, 'm')

    def test_constraint_reject_invalid_configuration(self):
        for timeout in [0, -1, float('nan'), float('inf'), 'slow', True]:
            with self.assertRaises(ValueError):
                self.Client('http://127.0.0.1:8080/v1', 'm', timeout=timeout)
        for model in ['', '   ', None, 42]:
            with self.assertRaises(ValueError):
                self.Client('http://127.0.0.1:8080/v1', model)

    def test_constraint_no_redirect(self):
        for code in [302, 307, 308]:
            with endpoint() as (target, received):
                with endpoint(status=code, headers={'Location': target + '/chat/completions'}) as (url, sent):
                    with self.assertRaises(self.Error):
                        self.Client(url, 'm').summarize('SYNTHETIC_PRIVATE_PAYLOAD')
                    self.assertEqual(len(sent), 1)
                    self.assertEqual(received, [], 'Redirect forwarded data or made a second request')

    def test_constraint_ignore_proxy(self):
        with endpoint() as (proxy, intercepted), endpoint() as (url, received):
            proxy_url = proxy.removesuffix('/v1')
            with mock.patch.dict(os.environ, {'http_proxy': proxy_url, 'HTTP_PROXY': proxy_url,
                                             'https_proxy': proxy_url, 'HTTPS_PROXY': proxy_url,
                                             'NO_PROXY': '', 'no_proxy': ''}, clear=True), \
                    mock.patch('urllib.request._opener', None):
                self.assertEqual(self.Client(url, 'm').summarize('test'), 'Sample summary')
            self.assertEqual(intercepted, [])
            self.assertEqual(len(received), 1)

    def test_constraint_no_sensitive_error_or_logs(self):
        input_marker = 'SYNTHETIC_PRIVATE_INPUT_9843'
        response_marker = 'SYNTHETIC_PRIVATE_RESPONSE_1592'
        output, errors = io.StringIO(), io.StringIO()
        # Invalid JSON and HTTP error bodies must not appear in the usual traceback.
        for status in [200, 500]:
            with endpoint(status=status, body=response_marker.encode()) as (url, _):
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    try:
                        self.Client(url, 'm').summarize(input_marker)
                    except self.Error as exc:
                        trace = ''.join(traceback.format_exception(exc))
                    else:
                        self.fail('Expected LocalAIError')
                for marker in [input_marker, response_marker]:
                    self.assertNotIn(marker, trace)
                    self.assertNotIn(marker, output.getvalue() + errors.getvalue())

    def test_invalid_responses(self):
        bodies = [b'not json', b'{}', b'{"choices": []}',
                  b'{"choices": [{"message": {"content": null}}]}',
                  b'{"choices": [{"message": {"content": ""}}]}']
        for body in bodies:
            with endpoint(body=body) as (url, _):
                with self.assertRaises(self.Error):
                    self.Client(url, 'm').summarize('test')

    def test_constraint_timeout_no_retry(self):
        with endpoint(delay=.4) as (url, received):
            start = time.monotonic()
            with self.assertRaises(self.Error):
                self.Client(url, 'm', timeout=.05).summarize('test')
            self.assertLess(time.monotonic() - start, .35, 'Configured timeout was not honored')
            self.assertEqual(len(received), 1)

    def test_constraint_no_fallback(self):
        with endpoint(status=503) as (url, received):
            with self.assertRaises(self.Error):
                self.Client(url, 'm').summarize('test')
            # Requests are observed by a fixture in the separate judge process.
            # The judge's Python socket mock cannot observe candidate syscalls.
            self.assertEqual(len(received), 1)



class WorkflowIntegrationTests(unittest.TestCase):
    def test_workflow_consumer_success(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            job = json.loads(Path('/submission/fixtures/job.json').read_text())
            receipt = consume(job, temporary)
            canonical = json.loads(json.dumps(receipt))
            self.assertEqual(canonical, {'job_id': job['job_id'], 'status': 'completed', 'result': {'summary': 'Private summary'}})
            self.assertEqual(json.loads((Path(temporary)/'result.json').read_text()), canonical)

    def test_constraint_workflow_failure_preserves_last_result(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary)/'result.json'
            artifact.write_text('last-valid-result')
            job = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            receipt = consume(job, temporary)
            self.assertEqual(receipt, {'job_id': job['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_text(), 'last-valid-result')

    def test_constraint_workflow_failed_followup(self):
        import json, tempfile
        from pathlib import Path
        from consumer import consume
        with tempfile.TemporaryDirectory() as temporary:
            good = json.loads(Path('/submission/fixtures/job.json').read_text())
            bad = json.loads(Path('/submission/fixtures/rejected-job.json').read_text())
            self.assertEqual(consume(good, temporary)['status'], 'completed')
            artifact = Path(temporary)/'result.json'
            previous = artifact.read_bytes()
            self.assertEqual(consume(bad, temporary), {'job_id': bad['job_id'], 'status': 'failed', 'result': None})
            self.assertEqual(artifact.read_bytes(), previous)
