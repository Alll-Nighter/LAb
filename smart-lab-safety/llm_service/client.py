"""Ollama HTTP client for the LLM Service.

Provides a thin, synchronous wrapper around the Ollama ``/api/chat``
endpoint.  All LLM calls in the project go through this module so that
the transport layer is defined in exactly one place.
"""

import logging

import requests

# ---------------------------------------------------------------------------
# Configuration constants (importable by other modules)
# ---------------------------------------------------------------------------

OLLAMA_URL: str = "http://localhost:11434"
"""Base URL of the local Ollama server."""

OLLAMA_MODEL: str = "llama3.2"
"""Model name passed to Ollama for inference."""

OLLAMA_TIMEOUT_SECONDS: int = 120
"""HTTP timeout for a single Ollama request (seconds)."""

OLLAMA_TEMPERATURE: float = 0.3
"""Sampling temperature – low for deterministic, factual output."""

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class OllamaError(RuntimeError):
    """Raised when communication with Ollama fails.

    Covers connection errors, non-200 responses, malformed JSON, and
    empty replies.
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chat_with_ollama(messages: list[dict]) -> str:
    """Send a chat-completion request to the local Ollama server.

    Args:
        messages: A list of ``{"role": ..., "content": ...}`` dicts
                  (system + user messages built by ``prompts.py``).

    Returns:
        The assistant's reply as a plain string.

    Raises:
        OllamaError: On connection failure, bad status, malformed JSON,
                     or an empty reply from the model.
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
        },
    }

    # --- send request ---
    try:
        response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
    except requests.ConnectionError as exc:
        _log.error("Cannot reach Ollama at %s: %s", url, exc)
        raise OllamaError(
            f"Cannot reach Ollama at {url}. Is 'ollama serve' running?"
        ) from exc
    except requests.Timeout as exc:
        _log.error("Ollama request timed out after %ss", OLLAMA_TIMEOUT_SECONDS)
        raise OllamaError(
            f"Ollama request timed out after {OLLAMA_TIMEOUT_SECONDS}s"
        ) from exc
    except requests.RequestException as exc:
        _log.error("Ollama HTTP error: %s", exc)
        raise OllamaError(f"Ollama HTTP error: {exc}") from exc

    # --- check status ---
    if response.status_code != 200:
        _log.error("Ollama returned HTTP %s: %s", response.status_code, response.text)
        raise OllamaError(
            f"Ollama returned HTTP {response.status_code}: {response.text[:200]}"
        )

    # --- parse JSON ---
    try:
        data = response.json()
    except ValueError as exc:
        _log.error("Ollama returned invalid JSON: %s", response.text[:200])
        raise OllamaError("Ollama returned invalid JSON") from exc

    # --- extract reply ---
    content = _extract_content(data)
    if not content:
        _log.error("Ollama returned an empty reply: %s", data)
        raise OllamaError("Ollama returned an empty reply")

    return content


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _extract_content(data: dict) -> str:
    """Pull the assistant text out of an Ollama chat response.

    Expected shape: ``{"message": {"content": "..."}}``.
    Returns an empty string if the path is missing.
    """
    try:
        return (data.get("message") or {}).get("content", "").strip()
    except AttributeError:
        return ""
