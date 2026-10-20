"""Resilient adapter for the local Ollama chat API."""
import time

import requests

from .config import settings


class ModelError(RuntimeError):
    """Raised when local model inference cannot produce a usable response."""


def _is_retryable(exc: requests.RequestException) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError):
        response = exc.response
        return response is not None and (
            response.status_code == 429 or response.status_code >= 500
        )
    return False


def chat(system: str, user: str, temperature: float = 0.2) -> str:
    """Call local Ollama with bounded retries; no cloud API key is required."""
    url = settings.ollama_base_url + "/api/chat"
    attempts = settings.llm_retries + 1
    last_error = None

    for attempt in range(attempts):
        try:
            response = requests.post(
                url,
                json={
                    "model": settings.ollama_model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "options": {"temperature": temperature},
                },
                timeout=settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            answer = payload.get("message", {}).get("content", "").strip()
            if not answer:
                raise ModelError("The local model returned an empty response.")
            return answer
        except requests.RequestException as exc:
            last_error = exc
            if attempt + 1 >= attempts or not _is_retryable(exc):
                break
            # Short bounded backoff prevents hammering a busy local model.
            time.sleep(min(2 ** attempt, 4))

    raise ModelError(
        f"Cannot complete inference with Ollama at {url} using model "
        f"{settings.ollama_model!r} after {attempt + 1} attempt(s). "
        f"Check that Ollama is running, the model is installed, and memory "
        f"is available. Details: {last_error}"
    ) from last_error
