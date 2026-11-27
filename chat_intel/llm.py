"""Thin wrapper around the Gemini API.

The rest of the project only calls generate(), so switching to another
provider later means changing this one file.
"""
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

DEFAULT_MODEL = "gemini-3.8-flash"      # override with LLM_MODEL in .env
RETRY_CODES = {429, 500, 503, 504}      # rate limit / temporary server trouble

FATAL_CODES = {400, 401, 403, 404}      # wrong key, wrong model name, no access: retrying cannot help


class LLMError(RuntimeError):
    """A model-setup problem, reported with a short readable message."""


_client = None


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = genai.Client(api_key=key)
    return _client


def generate(prompt: str, system: str = None, json_mode: bool = False,
             max_retries: int = 4, model: str = None) -> str:
    """Send a prompt to the model and return its text answer.

    temperature=0 makes answers as repeatable as possible.
    json_mode=True asks the model to reply with valid JSON only.
    Temporary errors (429/5xx) are retried with a growing wait.
    """
    model = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0,
        response_mime_type="application/json" if json_mode else None,
    )
    for attempt in range(max_retries + 1):
        try:
            response = _get_client().models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.text or ""
        except errors.APIError as err:
            if err.code in RETRY_CODES and attempt < max_retries:
                wait = 2 ** (attempt + 1)
                print(f"[llm] error {err.code}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            if err.code in FATAL_CODES:
                reason = str(getattr(err, "message", err))[:200]
                raise LLMError(
                    f"The model request failed ({err.code}) for model '{model}': {reason}\n"
                    "Check LLM_MODEL in your .env and that your key can use that model."
                ) from None
            raise
