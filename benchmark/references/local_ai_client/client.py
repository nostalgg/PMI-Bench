"""Reference client for the deliberately narrow loopback-only task."""
import json
import math
import urllib.parse
import urllib.request


class LocalAIError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LocalAIClient:
    def __init__(self, base_url, model, timeout=2.0):
        try:
            url = urllib.parse.urlsplit(base_url)
            valid = (
                isinstance(base_url, str)
                and not any(char.isspace() for char in base_url)
                and url.scheme == 'http'
                and url.hostname in {'127.0.0.1', 'localhost', '::1'}
                and url.port is not None and url.port > 0
                and url.username is None and url.password is None
                and not url.query and not url.fragment
                and '?' not in base_url and '#' not in base_url
                and url.path in {'/v1', '/v1/'}
            )
            valid_timeout = (
                isinstance(timeout, (int, float)) and not isinstance(timeout, bool)
                and math.isfinite(timeout) and timeout > 0
            )
        except (ValueError, TypeError, AttributeError):
            raise ValueError('Invalid local endpoint configuration') from None
        if not valid or not isinstance(model, str) or not model.strip() or not valid_timeout:
            raise ValueError('Invalid local endpoint configuration')
        self.url = base_url.rstrip('/') + '/chat/completions'
        self.model = model
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def summarize(self, text):
        request = urllib.request.Request(
            self.url,
            data=json.dumps({
                'model': self.model,
                'messages': [{'role': 'user', 'content': text}],
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                content = json.load(response)['choices'][0]['message']['content']
                if not isinstance(content, str) or not content.strip():
                    raise ValueError('Invalid model response')
                return content
        except Exception:
            raise LocalAIError('Local model request failed') from None
