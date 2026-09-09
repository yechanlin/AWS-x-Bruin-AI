"""Selects the configured LLM provider (OpenAI, Gemini, or AWS Bedrock; explicit LLM_PROVIDER or auto-detected by API key) and returns parsed JSON, with a JSON-repair fallback and no-provider handling."""

from __future__ import annotations

import logging
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger(__name__)

# How long a single provider call may run before we give up on it and try the
# next configured provider. Override with LLM_TIMEOUT_SECONDS.
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

def _clean_json(text: str) -> str:
    if text is None:
        return ""
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1]
    return t


def try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    cleaned = _clean_json(text)
    try:
        return json.loads(cleaned)
    except Exception:
        fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            return json.loads(fixed)
        except Exception:
            return None


def _run_with_timeout(fn: Callable[..., Any], args: tuple, timeout: float) -> Optional[Dict[str, Any]]:
    """Run fn(*args) on a worker thread and give up after `timeout` seconds.

    Python can't force-kill a thread, so a timed-out call keeps running in
    the background and its result is discarded - that's fine here since
    fn's own return value is all the caller ever wanted. shutdown(wait=False)
    is deliberate: the default `wait=True` would block here until the slow
    call finishes, defeating the point of the timeout.
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn, *args)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        logger.warning(f"[LLM] {fn.__name__} timed out after {timeout}s")
        return None
    except Exception as e:
        logger.warning(f"[LLM] {fn.__name__} raised unexpectedly: {e}")
        return None
    finally:
        executor.shutdown(wait=False)


def _call_openai_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None
    mdl = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(f"[LLM] OpenAI call model={mdl} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
    client = OpenAI(api_key=api_key, timeout=LLM_TIMEOUT_SECONDS)
    try:
        completion = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            # Structurally forces valid JSON syntax (every agent prompt already
            # says "JSON", which this mode requires). Doesn't guarantee the
            # right *shape* - callers still validate against a Pydantic model -
            # but it rules out plain-prose responses entirely.
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            return None
        logger.info(f"[LLM] OpenAI response chars={len(content)}")
        return try_parse_json(content)
    except Exception as e:
        logger.warning(f"[LLM] OpenAI call failed: {e}")
        return None


def _call_gemini_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Call Gemini via the `google-genai` SDK (the maintained replacement for
    the retired `google-generativeai` package - see README for the migration
    note)."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
    except Exception:
        return None
    mdl = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    logger.info(f"[LLM] Gemini call model={mdl} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
    try:
        client = genai.Client(api_key=key)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            response_mime_type="application/json",
            http_options=types.HttpOptions(timeout=int(LLM_TIMEOUT_SECONDS * 1000)),
        )
        response = client.models.generate_content(model=mdl, contents=user_prompt, config=config)
        text = response.text
        if not text:
            return None
        logger.info(f"[LLM] Gemini response chars={len(text)}")
        return try_parse_json(text)
    except Exception as e:
        logger.warning(f"[LLM] Gemini call failed: {e}")
        return None


def _normalize_provider_name(name: str) -> Optional[str]:
    name = (name or "").lower().strip()
    if name in {"gemini", "google"}:
        return "gemini"
    if name == "openai":
        return "openai"
    if name in {"bedrock", "aws"}:
        return "bedrock"
    return None


def _has_credentials(provider: str) -> bool:
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    if provider == "bedrock":
        return bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"))
    return False


def call_llm_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Try each configured provider in turn, falling back to the next one if
    a call fails, errors, or exceeds LLM_TIMEOUT_SECONDS (default 20s).

    LLM_PROVIDER, if set, is tried first but is no longer a hard lock - it
    just picks the starting point; any other provider with credentials
    present is tried next, in the fixed order gemini -> openai -> bedrock.
    LLM_PROVIDER=offline (or "none") still disables model calls entirely,
    regardless of which keys are configured.
    """
    raw_provider = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    if raw_provider in {"none", "offline"}:
        return None

    order: List[str] = []
    preferred = _normalize_provider_name(raw_provider)
    if preferred:
        order.append(preferred)
    for name in ("gemini", "openai", "bedrock"):
        if name not in order and _has_credentials(name):
            order.append(name)

    if not order:
        logger.warning("[LLM] No provider available; returning None")
        return None

    funcs: Dict[str, Callable[..., Optional[Dict[str, Any]]]] = {
        "openai": _call_openai_json,
        "gemini": _call_gemini_json,
        "bedrock": _call_bedrock_json,
    }

    for idx, name in enumerate(order, start=1):
        logger.info(f"[LLM] Trying provider {idx}/{len(order)}: {name}")
        result = _run_with_timeout(funcs[name], (system_prompt, user_prompt, model), LLM_TIMEOUT_SECONDS)
        if result is not None:
            if idx > 1:
                logger.info(f"[LLM] Recovered via {name} after {idx - 1} earlier provider(s) failed")
            return result
        logger.warning(f"[LLM] Provider {name} failed, timed out, or returned nothing")

    logger.warning(f"[LLM] All {len(order)} configured provider(s) failed; using heuristic fallback")
    return None


# Backward compatibility for existing imports
def call_openai_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return call_llm_json(system_prompt, user_prompt, model=model)


def _call_bedrock_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Call AWS Bedrock (Anthropic Claude) and return parsed JSON.

    Tries a sequence of candidate model IDs to handle throttling or unavailability.
    Requires AWS credentials (env, profile, or instance role) and region.
    """
    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import ClientError
    except Exception:
        logger.warning("[LLM] boto3 not installed for Bedrock")
        return None

    region = (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or "us-east-1"
    )

    # Build list of candidate models: env override > passed model > defaults
    env_primary = os.getenv("BEDROCK_MODEL_ID")
    env_candidates = [m.strip() for m in (os.getenv("BEDROCK_MODEL_CANDIDATES") or "").split(",") if m.strip()]
    defaults = [
        # Claude 3.5 Sonnet
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        # Claude 3.5 Haiku (example; adjust if your region uses a different suffix)
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        # Claude 3 Haiku
        "anthropic.claude-3-haiku-20240307-v1:0",
    ]
    candidates = []
    for m in [model, env_primary, *env_candidates, *defaults]:
        if m and m not in candidates:
            candidates.append(m)

    anthropic_version = os.getenv("ANTHROPIC_VERSION", "bedrock-2023-05-31")

    # Per-attempt timeout, kept below LLM_TIMEOUT_SECONDS so a stuck candidate
    # doesn't consume the whole cross-provider fallback budget by itself.
    boto_config = Config(connect_timeout=5, read_timeout=min(10, LLM_TIMEOUT_SECONDS))
    client = boto3.client("bedrock-runtime", region_name=region, config=boto_config)

    last_err = None
    for idx, model_id in enumerate(candidates, start=1):
        logger.info(f"[LLM] Bedrock attempt {idx}/{len(candidates)} model={model_id} region={region} sys_chars={len(system_prompt)} user_chars={len(user_prompt)}")
        try:
            body = {
                "anthropic_version": anthropic_version,
                "system": system_prompt + "\nReturn ONLY valid JSON.",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt}
                        ],
                    }
                ],
                "max_tokens": 1024,
                "temperature": 0.2,
            }
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            raw = response.get("body")
            text_content = None
            if raw is not None:
                data = json.loads(raw.read().decode("utf-8"))
                parts = []
                for item in data.get("content", []) or []:
                    t = item.get("text")
                    if t:
                        parts.append(t)
                text_content = "\n".join(parts)
            if not text_content:
                logger.warning("[LLM] Bedrock empty response content; trying next model")
                last_err = "empty_response"
                continue
            logger.info(f"[LLM] Bedrock response chars={len(text_content)}")
            parsed = try_parse_json(text_content)
            if parsed is not None:
                return parsed
            logger.warning("[LLM] Bedrock JSON parse failed; trying next model")
            last_err = "json_parse_failed"
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            msg = e.response.get("Error", {}).get("Message")
            logger.warning(f"[LLM] Bedrock ClientError code={code} msg={msg}; trying next model")
            last_err = code or str(e)
            # On throttling or other errors, just try next candidate
            continue
        except Exception as e:
            logger.warning(f"[LLM] Bedrock call failed: {e}; trying next model")
            last_err = str(e)
            continue

    logger.warning(f"[LLM] Bedrock exhausted candidates; last_err={last_err}")
    return None
