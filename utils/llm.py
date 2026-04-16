import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_llm(prompt):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        })
        return response.json()["response"]
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"
