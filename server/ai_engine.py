import requests
import json

OLLAMA_URL = "http://host.docker.internal:11434/api/generate"
MODEL = "tinyllama"


def ask_ollama(prompt, stream=False):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": stream,
    }

    response = requests.post(OLLAMA_URL, json=payload, stream=stream)

    if not stream:
        return response.json()["response"]

    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode())
            if "response" in data:
                yield data["response"]