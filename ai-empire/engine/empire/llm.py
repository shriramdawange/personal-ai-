import requests
from .config import settings

class ModelError(RuntimeError): pass

def chat(system: str, user: str, temperature: float = 0.2) -> str:
    """Call a local Ollama chat model. No cloud API key is required."""
    url = settings.ollama_base_url + '/api/chat'
    try:
        response = requests.post(url, json={
            'model': settings.ollama_model,
            'stream': False,
            'messages': [{'role':'system','content':system},{'role':'user','content':user}],
            'options': {'temperature': temperature}
        }, timeout=180)
        response.raise_for_status()
        payload = response.json()
        text = payload.get('message',{}).get('content','').strip()
        if not text: raise ModelError('The local model returned an empty response.')
        return text
    except requests.RequestException as exc:
        raise ModelError(f'Cannot reach Ollama at {url}. Start Ollama and make sure model {settings.ollama_model!r} is installed. Details: {exc}') from exc
