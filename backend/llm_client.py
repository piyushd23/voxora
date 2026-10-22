"""
Unified LLM Client — Supports OpenAI, Grok (xAI), and Google Gemini.
API key is mandatory. Offline mode is disabled.
"""

import json
import logging
import os
import re
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv
import httpx

load_dotenv()
logger = logging.getLogger("llm_client")

PROVIDER_LABELS = {
    "groq": "Groq", "openai": "OpenAI", "grok": "Grok (xAI)",
    "claude": "Anthropic Claude", "gemini": "Google Gemini"
}


class LLMError(ValueError):
    """Provider failure carrying a stable code and a user-safe message (no raw provider payloads)."""

    def __init__(self, code: str, user_message: str, provider: str = "", retryable: bool = True, detail: str = ""):
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message
        self.provider = provider
        self.retryable = retryable
        self.detail = detail


def _http_error(provider: str, status: int, body: str) -> LLMError:
    """Map an HTTP failure to a user-safe LLMError."""
    label = PROVIDER_LABELS.get(provider, provider)
    lowered = body.lower()
    if status == 429 and ("insufficient_quota" in lowered or "no credits" in lowered or "billing" in lowered and "quota" in lowered):
        return LLMError("quota", f"{label} account has no remaining credits/quota. Add billing or use a different provider key.", provider, False, body[:500])
    if status == 400 and "json_validate_failed" in lowered:
        return LLMError("invalid_output", f"{label} produced malformed JSON.", provider, True, body[:500])
    if status == 429:
        return LLMError("rate_limited", f"{label} rate limit reached. Please wait about a minute and retry, or add another provider key.", provider, True, body[:500])
    if status in (401, 403):
        return LLMError("auth", f"{label} rejected the API key. Please check the key in settings.", provider, False, body[:500])
    if status == 400 and ("model" in body.lower() and ("not" in body.lower() or "decommission" in body.lower())):
        return LLMError("bad_model", f"The configured {label} model is unavailable. Please change the model in settings.", provider, False, body[:500])
    if status >= 500:
        return LLMError("provider_down", f"{label} is temporarily unavailable (HTTP {status}). Please retry shortly.", provider, True, body[:500])
    return LLMError("provider_error", f"{label} returned an error (HTTP {status}).", provider, True, body[:500])


def sanitize_api_key(raw_key: Optional[str]) -> str:
    """Extract and sanitize a valid API key token from input that might contain pasted chat text, timestamps, or quotes."""
    if not raw_key:
        return ""
    raw = str(raw_key).strip()
    # Try regex matching known prefixes
    patterns = [
        r"(sk-proj-[a-zA-Z0-9_\-]+)",
        r"(sk-ant-[a-zA-Z0-9_\-]+)",
        r"(sk-[a-zA-Z0-9_\-]+)",
        r"(xai-[a-zA-Z0-9_\-]+)",
        r"(gsk_[a-zA-Z0-9_\-]+)",
        r"(AIzaSy[a-zA-Z0-9_\-]+)"
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            return m.group(1).strip()
    # Fallback: strip any non-ASCII characters (e.g. \u202f narrow no-break space) and quotes
    clean = re.sub(r"[^\x20-\x7E]", "", raw).strip().strip("\"'").strip()
    return clean


def get_active_provider_info() -> Dict:
    """Detect which provider is active based on environment variables."""
    load_dotenv(override=True)
    openai_key = sanitize_api_key(os.getenv("OPENAI_API_KEY", ""))
    grok_key = sanitize_api_key(os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", ""))
    groq_key = sanitize_api_key(os.getenv("GROQ_API_KEY", ""))
    if not groq_key and grok_key.startswith("gsk_"):
        groq_key = grok_key
    claude_key = sanitize_api_key(os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", ""))
    gemini_key = sanitize_api_key(os.getenv("GEMINI_API_KEY", ""))
    preferred = os.getenv("PREFERRED_LLM_PROVIDER", "").strip().lower()

    # Masking helper
    def mask(k):
        if not k or len(k) <= 8:
            return "Configured" if k else "Not configured"
        return f"{k[:4]}...{k[-4:]}"

    has_openai = bool(openai_key and len(openai_key) > 10 and openai_key != "your-api-key-here")
    has_groq = bool(groq_key and len(groq_key) > 10 and groq_key.startswith("gsk_"))
    has_grok = bool(grok_key and len(grok_key) > 10 and grok_key.startswith("xai-"))
    has_claude = bool(claude_key and len(claude_key) > 10 and claude_key != "your-api-key-here")
    has_gemini = bool(gemini_key and len(gemini_key) > 10 and gemini_key != "your-api-key-here")

    # Determine active provider — offline mode is disabled
    active_provider = "none"
    active_model = "none"

    if preferred == "groq" and has_groq:
        active_provider = "groq"
        active_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    elif preferred == "openai" and has_openai:
        active_provider = "openai"
        active_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif preferred == "grok" and has_grok:
        active_provider = "grok"
        active_model = os.getenv("GROK_MODEL", "grok-2-latest")
    elif preferred == "claude" and has_claude:
        active_provider = "claude"
        active_model = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
    elif preferred == "gemini" and has_gemini:
        active_provider = "gemini"
        active_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    elif has_groq:
        active_provider = "groq"
        active_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    elif has_openai:
        active_provider = "openai"
        active_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif has_grok:
        active_provider = "grok"
        active_model = os.getenv("GROK_MODEL", "grok-2-latest")
    elif has_claude:
        active_provider = "claude"
        active_model = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-20241022")
    elif has_gemini:
        active_provider = "gemini"
        active_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    is_configured = active_provider != "none"

    return {
        "active_provider": active_provider,
        "active_model": active_model,
        "has_openai": has_openai,
        "openai_masked": mask(openai_key),
        "has_groq": has_groq,
        "groq_masked": mask(groq_key),
        "has_grok": has_grok,
        "grok_masked": mask(grok_key),
        "has_claude": has_claude,
        "claude_masked": mask(claude_key),
        "has_gemini": has_gemini,
        "gemini_masked": mask(gemini_key),
        "is_online": is_configured,
        "is_configured": is_configured
    }


async def call_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: str = "You are an expert product intelligence AI. Return strictly valid JSON.",
    max_tokens: int = 600,
    provider: str = "openai"
) -> Optional[str]:
    """Call OpenAI, Groq, or Grok via OpenAI-compatible chat completions API."""
    import asyncio
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }
    # Reasoning models (gpt-oss) spend hidden tokens from max_tokens; keep reasoning short so the JSON isn't cut off
    if "gpt-oss" in model:
        payload["reasoning_effort"] = "low"

    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
        for attempt in range(3):
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return None
                choice = choices[0]
                content = (choice.get("message", {}).get("content") or "").strip()
                if choice.get("finish_reason") == "length":
                    raise LLMError("truncated", "The AI response was cut off before completing.", provider, True)
                return content
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429 and attempt < 2 and _http_error(provider, status, exc.response.text).code != "quota":
                    wait_s = 6.0
                    m = re.search(r"try again in (?:(\d+)m)?([\d\.]+)s", exc.response.text)
                    if m:
                        try:
                            wait_s = float(m.group(1) or 0) * 60 + float(m.group(2)) + 1.0
                        except Exception:
                            wait_s = 6.0
                    if wait_s > 30.0:
                        # Long cooldown: let the caller fall back to another provider instead of hanging the UI
                        raise _http_error(provider, status, exc.response.text)
                    logger.warning(f"Rate limited by {url}, waiting {wait_s:.1f}s before retry (attempt {attempt + 1}/3)...")
                    await asyncio.sleep(wait_s)
                    continue
                if (status >= 500 or "json_validate_failed" in exc.response.text) and attempt < 2:
                    logger.warning(f"HTTP {status} from {url}, retrying (attempt {attempt + 1}/3)...")
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                logger.error(f"HTTP {status} from {url}: {exc.response.text}")
                raise _http_error(provider, status, exc.response.text)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt < 2:
                    logger.warning(f"Network error calling {url} ({type(exc).__name__}), retrying (attempt {attempt + 1}/3)...")
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                label = PROVIDER_LABELS.get(provider, provider)
                raise LLMError("network", f"Could not reach {label} (network timeout). Check your connection and retry.", provider, True, repr(exc))
    return None


async def call_gemini(api_key: str, prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> Optional[str]:
    """Call Google Gemini API with automatic fallback across standard models."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    preferred_model = os.getenv("GEMINI_MODEL")
    candidate_models = []
    if preferred_model and preferred_model.strip():
        candidate_models.append(preferred_model.strip())
    for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
        if m not in candidate_models:
            candidate_models.append(m)

    last_err = None
    for model_name in candidate_models:
        try:
            logger.info(f"Attempting Google Gemini generation with model '{model_name}'...")
            import asyncio
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt or None,
                    temperature=0.2,
                    max_output_tokens=max(max_tokens, 4096),
                    response_mime_type="application/json"
                )
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err_str = str(e)
            last_err = e
            # Catch 404, NOT_FOUND, or deprecated model error
            is_404 = (
                "404" in err_str or
                "NOT_FOUND" in err_str or
                "not found" in err_str.lower() or
                "no longer available" in err_str.lower() or
                getattr(e, "code", None) == 404 or
                getattr(e, "status_code", None) == 404
            )
            if is_404:
                logger.warning(f"Gemini model '{model_name}' not available ({err_str[:120]}), trying next candidate model...")
                continue
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                raise _http_error("gemini", 429, err_str)
            if "API_KEY_INVALID" in err_str or "PERMISSION_DENIED" in err_str or "401" in err_str or "403" in err_str:
                raise _http_error("gemini", 401, err_str)
            raise LLMError("provider_error", "Google Gemini returned an error.", "gemini", True, err_str[:500])

    if last_err:
        raise LLMError("bad_model", "No Google Gemini model is available for this key.", "gemini", False, str(last_err)[:500])
    return None


async def call_claude(
    api_key: str,
    prompt: str,
    model: str = "claude-3-5-haiku-20241022",
    system_prompt: str = "You are an expert product analyst. Return valid JSON only.",
    max_tokens: int = 1500
) -> Optional[str]:
    """Call Anthropic Claude API via Messages endpoint with automatic model fallback."""
    import asyncio
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    candidate_models = []
    preferred = os.getenv("CLAUDE_MODEL")
    if preferred and preferred.strip():
        candidate_models.append(preferred.strip())
    for m in ["claude-3-5-haiku-20241022", "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]:
        if m not in candidate_models:
            candidate_models.append(m)

    last_err = None
    for model_name in candidate_models:
        payload = {
            "model": model_name,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(2):
                try:
                    logger.info(f"Attempting Anthropic Claude generation with model '{model_name}'...")
                    resp = await client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("stop_reason") == "max_tokens":
                        raise LLMError("truncated", "The AI response was cut off before completing.", "claude", True)
                    content_blocks = data.get("content", [])
                    if content_blocks and content_blocks[0].get("text"):
                        return content_blocks[0]["text"].strip()
                except httpx.HTTPStatusError as exc:
                    err_text = exc.response.text
                    last_err = exc
                    if exc.response.status_code == 429 and attempt < 1:
                        await asyncio.sleep(4.0)
                        continue
                    if exc.response.status_code == 404 or "not_found_error" in err_text:
                        logger.warning(f"Claude model '{model_name}' not found, falling back...")
                        break
                    logger.error(f"HTTP {exc.response.status_code} from Anthropic: {err_text}")
                    raise _http_error("claude", exc.response.status_code, err_text)
                except LLMError:
                    raise
                except (httpx.TimeoutException, httpx.TransportError) as e:
                    raise LLMError("network", "Could not reach Anthropic Claude (network timeout). Check your connection and retry.", "claude", True, repr(e))
                except Exception as e:
                    last_err = e
                    break

    if last_err:
        raise LLMError("bad_model", "No Anthropic Claude model is available for this key.", "claude", False, str(last_err)[:500])
    return None


def _provider_chain(info: Dict) -> list:
    """Active provider first, then every other configured provider as automatic fallback."""
    order = ["groq", "openai", "grok", "claude", "gemini"]
    configured = [p for p in order if info.get(f"has_{p}")]
    active = info["active_provider"]
    return ([active] if active in configured else []) + [p for p in configured if p != active]


async def _call_provider(provider: str, prompt: str, system_prompt: str, max_tokens: int, model: Optional[str] = None) -> Optional[str]:
    defaults = {
        "groq": ("GROQ_MODEL", "openai/gpt-oss-120b"),
        "openai": ("OPENAI_MODEL", "gpt-4o-mini"),
        "grok": ("GROK_MODEL", "grok-2-latest"),
        "claude": ("CLAUDE_MODEL", "claude-3-5-haiku-20241022"),
        "gemini": ("GEMINI_MODEL", "gemini-2.0-flash"),
    }
    env_name, fallback_model = defaults[provider]
    model = model or os.getenv(env_name, fallback_model)

    if provider == "groq":
        key = sanitize_api_key(os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"))
        return await call_openai_compatible("https://api.groq.com/openai/v1", key, model, prompt, system_prompt, max_tokens, provider)
    if provider == "grok":
        key = sanitize_api_key(os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"))
        return await call_openai_compatible("https://api.x.ai/v1", key, model, prompt, system_prompt, max_tokens, provider)
    if provider == "openai":
        key = sanitize_api_key(os.getenv("OPENAI_API_KEY"))
        return await call_openai_compatible("https://api.openai.com/v1", key, model, prompt, system_prompt, max_tokens, provider)
    if provider == "claude":
        key = sanitize_api_key(os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        return await call_claude(key, prompt, model, system_prompt, max_tokens)
    if provider == "gemini":
        key = sanitize_api_key(os.getenv("GEMINI_API_KEY"))
        return await call_gemini(key, prompt, system_prompt, max_tokens)
    raise LLMError("no_provider", f"Unknown provider '{provider}'.", provider, False)


async def generate_ai_completion(
    prompt: str,
    system_prompt: str = "You are an expert product analyst. Return valid JSON only.",
    max_tokens: int = 600
) -> Tuple[str, str]:
    """
    Generate a completion with the active provider, automatically falling back to
    every other configured provider (Groq → OpenAI → Grok → Claude → Gemini) on failure.

    Raises LLMError if no API key is configured or every provider fails.
    """
    info = get_active_provider_info()
    chain = _provider_chain(info)

    if not chain:
        raise LLMError(
            "no_api_key",
            "API key is mandatory. Please configure your OpenAI, Groq, Grok (xAI), Claude, or Google Gemini API key to proceed.",
            retryable=False
        )

    failures = []
    for provider in chain:
        model = info["active_model"] if provider == info["active_provider"] else None
        logger.info(f"Dispatching prompt to {PROVIDER_LABELS[provider]}...")
        try:
            result = await _call_provider(provider, prompt, system_prompt, max_tokens, model)
            if result and result.strip():
                return result, provider
            failures.append(LLMError("empty", f"{PROVIDER_LABELS[provider]} returned an empty response.", provider))
        except LLMError as e:
            failures.append(e)
        except Exception as e:
            failures.append(LLMError("provider_error", f"{PROVIDER_LABELS[provider]} call failed.", provider, True, repr(e)[:500]))
        last = failures[-1]
        logger.warning(f"{PROVIDER_LABELS[provider]} failed [{last.code}]: {last.user_message} {last.detail[:300]}")

    # Every provider failed — surface the most actionable reason
    primary = next((f for f in failures if f.retryable), failures[0])
    tried = ", ".join(PROVIDER_LABELS[p] for p in chain)
    raise LLMError(
        primary.code,
        primary.user_message if len(chain) == 1 else f"{primary.user_message} (Tried: {tried}.)",
        primary.provider,
        any(f.retryable for f in failures),
        " | ".join(f"{f.provider}:{f.code}:{f.detail[:200]}" for f in failures)
    )
