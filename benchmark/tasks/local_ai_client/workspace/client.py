"""Client for an internal OpenAI-compatible endpoint (intentionally buggy)."""
import json
import urllib.request


class LocalAIError(RuntimeError):
    pass


class LocalAIClient:
    def __init__(self, base_url, model, timeout=2.0):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def summarize(self, text):
        payload = {"model": "default-model", "messages": [{"role": "user", "content": text}]}
        request = urllib.request.Request(
            self.base_url.rstrip('/') + '/chat/completions',
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LocalAIError(f"Request failed for {text}: {exc}") from exc
