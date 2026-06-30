# src/llm_service/claude_api.py
"""
LLM Client — supports Claude API and Ollama local models.
Switch between them via config.USE_LOCAL_MODEL.
"""

import json
import logging
import requests as http_requests
from typing import Optional

import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

import config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Anthropic client — only used when USE_LOCAL_MODEL = False
client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _call_ollama(prompt_text: str, system_prompt: Optional[str] = None) -> str:
    """
    Calls local Ollama model.
    Used when config.USE_LOCAL_MODEL = True.
    """
    full_prompt = prompt_text
    if system_prompt:
        full_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {prompt_text}"

    logger.info(f"Calling Ollama [{config.LOCAL_MODEL}]...")

    response = http_requests.post(
        f"{config.LOCAL_BASE_URL}/api/generate",
        json={
            "model":  config.LOCAL_MODEL,
            "prompt": full_prompt,
            "stream": False
        },
        timeout=300 # local models can be slow
    )

    if response.status_code != 200:
        raise ConnectionError(
            f"Ollama error {response.status_code}: {response.text}"
        )

    result = response.json().get("response", "")
    logger.info(f"Ollama responded — {len(result)} chars")
    return result


@retry(
    wait=wait_exponential(
        multiplier=1,
        min=config.RETRY_WAIT_MIN_SECS,
        max=config.RETRY_WAIT_MAX_SECS,
    ),
    stop=stop_after_attempt(config.RETRY_MAX_ATTEMPTS),
    retry=retry_if_exception_type((
        anthropic.RateLimitError,
        anthropic.APIConnectionError
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _call_claude(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    model: str = config.CLAUDE_MODEL,
    max_tokens: int = config.MAX_TOKENS,
) -> str:
    """
    Calls Claude API.
    Used when config.USE_LOCAL_MODEL = False.
    """
    logger.info(f"Calling Claude [{model}]...")

    kwargs = {
        "model":      model,
        "max_tokens": max_tokens,
        "messages":   [{"role": "user", "content": prompt_text}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    message = client.messages.create(**kwargs)
    response_text = message.content[0].text
    logger.info(f"Claude responded — {len(response_text)} chars")
    return response_text


def get_claude_response(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    model: str = config.CLAUDE_MODEL,
    max_tokens: int = config.MAX_TOKENS,
) -> str:
    """
    Main LLM call function.
    Routes to Ollama or Claude based on config.USE_LOCAL_MODEL.

    This is the ONLY function other modules call.
    Switching between local and cloud = one config change.
    """
    if config.USE_LOCAL_MODEL:
        return _call_ollama(prompt_text, system_prompt)
    else:
        return _call_claude(prompt_text, system_prompt, model, max_tokens)


def get_structured_claude_response(
    prompt_text: str,
    system_prompt: Optional[str] = None,
    model: str = config.CLAUDE_MODEL,
    max_tokens: int = config.MAX_TOKENS,
) -> dict:
    """
    Returns parsed JSON dictionary from LLM response.
    Works with both Ollama and Claude.
    """
    json_enforced_prompt = (
        prompt_text
        + "\n\nCRITICAL: Return ONLY valid JSON. "
          "No explanation, no markdown code fences, no preamble. "
          "Start your response with { and end with }."
    )

    raw_response = get_claude_response(
        prompt_text=json_enforced_prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
    )

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.error(f"Raw response: {raw_response[:300]}")
        return {}


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mode = "Ollama" if config.USE_LOCAL_MODEL else "Claude"
    print(f"\nTesting with: {mode}")
    print("="*50)

    response = get_claude_response(
        prompt_text="In one sentence, what is digital marketing?",
        system_prompt="You are a concise marketing expert."
    )
    print(f"Response: {response}")