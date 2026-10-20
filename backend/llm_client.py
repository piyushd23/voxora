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


def sanitize_api_key(raw_key: Optional[str]) -> str:
    """Extract and sanitize a valid API key token from input that might contain pasted chat text, timestamps, or quotes."""
    if not raw_key:
        return ""
    raw = str(raw_key).strip()
    # Try regex matching known prefixes
    patterns = [
        r"(sk-proj-[a-zA-Z0-9_\-]+)",
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
    max_tokens: int = 600
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
        "max_tokens": max_tokens
    }
    if "openai.com" in base_url or "x.ai" in base_url:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(3):
            try:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    content = msg.get("content") or ""
                    if not content.strip() and msg.get("reasoning"):
                        content = msg.get("reasoning")
                    return content.strip()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < 2:
                    wait_s = 6.0
                    m = re.search(r"try again in ([\d\.]+)s", exc.response.text)
                    if m:
                        try:
                            wait_s = min(float(m.group(1)) + 1.0, 25.0)
                        except Exception:
                            wait_s = 6.0
                    logger.warning(f"Rate limited by {url}, waiting {wait_s:.1f}s before retry (attempt {attempt + 1}/3)...")
                    await asyncio.sleep(wait_s)
                    continue
                logger.error(f"HTTP {exc.response.status_code} from {url}: {exc.response.text}")
                raise ValueError(f"Provider API returned HTTP {exc.response.status_code}: {exc.response.text}")
    return None


async def call_gemini(api_key: str, prompt: str) -> Optional[str]:
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
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
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
            # For authentication or quota errors, re-raise immediately
            raise e

    if last_err:
        raise ValueError(f"Gemini generation failed on all models {candidate_models}: {str(last_err)}")
    return None


async def generate_ai_completion(
    prompt: str,
    system_prompt: str = "You are an expert product analyst. Return valid JSON only.",
    max_tokens: int = 600
) -> Tuple[str, str]:
    """
    Generate completion using the active provider:
    1. Groq if configured
    2. Grok (xAI) if configured
    3. OpenAI if configured
    4. Gemini if configured

    Raises ValueError if no API key is configured (API key is mandatory).
    """
    info = get_active_provider_info()
    provider = info["active_provider"]

    if provider == "none":
        raise ValueError(
            "API key is mandatory. Please configure your OpenAI, Grok (xAI), or Google Gemini API key to proceed."
        )

    if provider == "groq":
        groq_key = sanitize_api_key(os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"))
        model = info["active_model"]
        logger.info(f"Dispatching prompt to Groq with model {model}...")
        try:
            result = await call_openai_compatible(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            if result:
                return result, "groq"
            raise ValueError("Empty response received from Groq API.")
        except Exception as e:
            logger.error(f"Groq API invocation failed: {e}")
            raise ValueError(f"Groq API error: {str(e)}")

    elif provider == "grok":
        grok_key = sanitize_api_key(os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY"))
        model = info["active_model"]
        logger.info(f"Dispatching prompt to Grok (xAI) with model {model}...")
        try:
            result = await call_openai_compatible(
                base_url="https://api.x.ai/v1",
                api_key=grok_key,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            if result:
                return result, "grok"
            raise ValueError("Empty response received from Grok API.")
        except Exception as e:
            logger.error(f"Grok API invocation failed: {e}")
            raise ValueError(f"Grok API error: {str(e)}")

    elif provider == "openai":
        openai_key = sanitize_api_key(os.getenv("OPENAI_API_KEY"))
        model = info["active_model"]
        logger.info(f"Dispatching prompt to OpenAI with model {model}...")
        try:
            result = await call_openai_compatible(
                base_url="https://api.openai.com/v1",
                api_key=openai_key,
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens
            )
            if result:
                return result, "openai"
            raise ValueError("Empty response received from OpenAI API.")
        except Exception as e:
            logger.error(f"OpenAI API invocation failed: {e}")
            raise ValueError(f"OpenAI API error: {str(e)}")

    elif provider == "gemini":
        gemini_key = sanitize_api_key(os.getenv("GEMINI_API_KEY"))
        logger.info(f"Dispatching prompt to Google Gemini ({info['active_model']})...")
        try:
            result = await call_gemini(gemini_key, prompt)
            if result:
                return result, "gemini"
            raise ValueError("Empty response received from Gemini API.")
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            raise ValueError(f"Gemini API error: {str(e)}")

    raise ValueError("No active AI provider configured. API key is mandatory.")
