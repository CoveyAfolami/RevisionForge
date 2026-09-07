"""OpenAI-compatible LLM client (roadmap Phase 9).

One client, any provider: Groq, OpenRouter, Gemini, OpenAI, or a local
Ollama. The provider is chosen in .env with LLM_PROVIDER, and the matching
API key env var is picked up automatically — so switching providers later
never requires code changes.
"""

import json
import os
import re

import requests

from ..observability.errors import ConfigurationError, LLMError, ValidationError

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct:free",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,
        "default_model": "llama3.1:8b",
    },
}


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None,
                 api_key: str | None = None, temperature: float = 0.3,
                 max_attempts: int = 2, timeout: int = 60, transport=None):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        chosen = (provider or os.getenv("LLM_PROVIDER", "groq")).lower().strip()
        if chosen not in PROVIDERS:
            raise ConfigurationError(
                f"Unknown LLM_PROVIDER '{chosen}'. Choose from: {', '.join(PROVIDERS)}"
            )
        spec = PROVIDERS[chosen]
        self.provider = chosen
        self.base_url = spec["base_url"]
        self.model = model or os.getenv("LLM_MODEL") or spec["default_model"]
        self.temperature = temperature
        self.max_attempts = max_attempts
        self.timeout = timeout

        if spec["key_env"]:
            self.api_key = api_key or os.getenv(spec["key_env"])
            if not self.api_key:
                raise ConfigurationError(
                    f"Set {spec['key_env']} in .env to use the {chosen} provider"
                )
        else:
            self.api_key = api_key or "ollama"

        # Injectably fake-able for tests, same pattern as AnkiConnectClient.
        self._transport = transport or requests.post

    def generate_structured(self, system: str, user: str) -> dict:
        """Chat completion that must return parsed JSON.

        Retries on invalid JSON up to max_attempts, then fails loudly.
        """
        last_error: Exception | None = None
        for _ in range(self.max_attempts):
            raw = self._chat(system, user)
            try:
                return _parse_json(raw)
            except ValidationError as error:
                last_error = error
        raise ValidationError(
            f"LLM failed to return valid JSON after {self.max_attempts} "
            f"attempts: {last_error}"
        )

    def _chat(self, system: str, user: str) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = self._transport(
                f"{self.base_url}/chat/completions",
                json=payload, headers=headers, timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as error:
            raise LLMError(
                f"Cannot reach {self.provider} at {self.base_url} — check your "
                f"internet connection and API key"
            ) from error
        except requests.exceptions.Timeout as error:
            raise LLMError("LLM request timed out") from error

        if response.status_code != 200:
            raise LLMError(
                f"{self.provider} returned HTTP {response.status_code}: "
                f"{response.json().get('error', {}).get('message', '')[:200]}"
            )
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as error:
            raise LLMError("LLM response was missing message content") from error


def _parse_json(raw: str) -> dict:
    """Parse model output as JSON, tolerating markdown code fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValidationError(f"Invalid JSON from LLM: {error}") from error
