import requests
import json

# Global configuration for the API endpoint, this is the default from `ollama serve`
OLLAMA_API_ENDPOINT = "http://localhost:11434"


def call_ollama_api(model_name, prompt_text):
    url = f"{OLLAMA_API_ENDPOINT}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt_text,
        "stream": False,
    }

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed with status code {response.status_code}")


def get_ollama_version():
    url = f"{OLLAMA_API_ENDPOINT}/api/version"
    response = requests.get(url)
    return response.json()


if __name__ == "__main__":
    # Print Ollama API version
    version_info = get_ollama_version()
    print(f"Ollama API version: {version_info['version']}")

    # Example usage
    result = call_ollama_api("nuextract", "count to 10")
    print(json.dumps(result, indent=2))  # Pretty print the result
