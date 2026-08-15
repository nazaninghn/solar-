"""
AI Service — connects SolarFlow to Groq (free tier) for intelligent energy recommendations.

Setup:
1. Go to https://console.groq.com
2. Sign up (free, no credit card needed)
3. Create API key from dashboard
4. Set GROQ_API_KEY in .env

Groq free tier: 30 RPM, no token charges, all models available.
Uses Llama 3.3 70B for high-quality recommendations.
Falls back to rule-based if no API key or API fails.
"""

import json
import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Groq (primary - free tier, no credit card)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# xAI Grok (secondary - requires credits)
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-3-mini-fast"


def _get_api_config() -> tuple[str, str, str] | None:
    """Return (api_url, api_key, model) for the first available provider."""
    if GROQ_API_KEY:
        return GROQ_API_URL, GROQ_API_KEY, GROQ_MODEL
    if XAI_API_KEY:
        return XAI_API_URL, XAI_API_KEY, XAI_MODEL
    return None


async def get_ai_recommendation(
    solar_kwh: float,
    consumption_kwh: float,
    battery_soc: float,
    grid_price: float,
    weather_cloud_pct: float,
    temperature_c: float,
) -> dict:
    """
    Ask AI for energy optimization recommendation.
    Priority: Groq (free) → xAI Grok → rule-based fallback.
    """
    config = _get_api_config()
    if not config:
        logger.info("AI: No API key configured — using rule-based fallback")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)

    api_url, api_key, model = config

    prompt = f"""You are an AI energy advisor for an industrial solar factory in Istanbul, Turkey.

Current status:
- Solar production: {solar_kwh:.1f} kW
- Factory consumption: {consumption_kwh:.1f} kW
- Battery SOC: {battery_soc:.1f}%
- Grid electricity price: €{grid_price:.3f}/kWh
- Cloud cover: {weather_cloud_pct:.0f}%
- Temperature: {temperature_c:.1f}°C

Based on this data, provide ONE specific actionable recommendation.
Respond ONLY with valid JSON (no markdown, no explanation outside JSON):
{{
  "action": "CHARGE_BATTERY" or "DISCHARGE_BATTERY" or "SELL_SURPLUS" or "BUY_GRID" or "REDUCE_LOAD" or "NO_ACTION",
  "title": "Short title (max 10 words)",
  "description": "Brief explanation why (max 30 words)",
  "expected_savings_eur": <number>,
  "confidence_pct": <number 0-100>
}}"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an energy optimization AI assistant. Always respond with valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 250,
                },
            )

            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                # Strip markdown code fences if present
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                recommendation = json.loads(content)
                provider = "groq" if "groq" in api_url else "grok_ai"
                logger.info(f"AI [{provider}] recommendation: {recommendation.get('title')}")
                return {
                    "source": provider,
                    "model": model,
                    **recommendation,
                }
            else:
                logger.warning(f"AI API error ({api_url}): {res.status_code} — {res.text[:200]}")
                return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)

    except json.JSONDecodeError as e:
        logger.warning(f"AI response not valid JSON: {e}")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)
    except Exception as e:
        logger.error(f"AI service error: {e}")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)


def _rule_based_fallback(
    solar_kwh: float, consumption_kwh: float, battery_soc: float, grid_price: float
) -> dict:
    """Deterministic fallback when AI API is not available."""
    surplus = solar_kwh - consumption_kwh

    if surplus > 0 and battery_soc > 80:
        return {
            "source": "rule_engine",
            "action": "SELL_SURPLUS",
            "title": "Sell surplus solar energy",
            "description": "Solar surplus available and battery full. Export to grid for revenue.",
            "expected_savings_eur": round(surplus * grid_price * 0.6, 2),
            "confidence_pct": 78,
        }
    elif surplus > 0 and battery_soc < 80:
        return {
            "source": "rule_engine",
            "action": "CHARGE_BATTERY",
            "title": "Store excess solar in battery",
            "description": "Solar surplus available. Charge battery for peak-hour use later.",
            "expected_savings_eur": round(surplus * grid_price * 0.4, 2),
            "confidence_pct": 82,
        }
    elif battery_soc > 60 and grid_price > 0.25:
        return {
            "source": "rule_engine",
            "action": "DISCHARGE_BATTERY",
            "title": "Use battery during peak pricing",
            "description": "Grid price is peak. Discharge battery to avoid expensive import.",
            "expected_savings_eur": round(battery_soc * 0.5 * grid_price * 0.01, 2),
            "confidence_pct": 85,
        }
    elif solar_kwh < consumption_kwh * 0.3 and grid_price < 0.15:
        return {
            "source": "rule_engine",
            "action": "BUY_GRID",
            "title": "Buy cheap off-peak electricity",
            "description": "Low solar and grid price is cheap. Good time to charge from grid.",
            "expected_savings_eur": round((consumption_kwh - solar_kwh) * 0.05, 2),
            "confidence_pct": 75,
        }
    else:
        return {
            "source": "rule_engine",
            "action": "NO_ACTION",
            "title": "System operating optimally",
            "description": "Current configuration is efficient. No changes needed.",
            "expected_savings_eur": 0,
            "confidence_pct": 90,
        }
