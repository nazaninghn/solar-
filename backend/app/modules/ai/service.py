"""
AI Service — connects SolarFlow to Grok (xAI) for intelligent energy recommendations.

Setup:
1. Go to https://console.x.ai
2. Sign up (uses X/Twitter account)
3. Get API key from dashboard
4. Set XAI_API_KEY in .env

Free promotional credits are given to new accounts.
If no API key is set, falls back to rule-based recommendations.
"""

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-3-mini"  # Fast, cheap model


async def get_ai_recommendation(
    solar_kwh: float,
    consumption_kwh: float,
    battery_soc: float,
    grid_price: float,
    weather_cloud_pct: float,
    temperature_c: float,
) -> dict:
    """
    Ask Grok AI for energy optimization recommendation.
    Falls back to rule-based if no API key or API fails.
    """
    if not XAI_API_KEY:
        logger.info("AI: No XAI_API_KEY — using rule-based fallback")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)

    prompt = f"""You are an AI energy advisor for an industrial solar factory in Istanbul.

Current status:
- Solar production: {solar_kwh:.0f} kW
- Factory consumption: {consumption_kwh:.0f} kW
- Battery SOC: {battery_soc:.0f}%
- Grid electricity price: €{grid_price:.3f}/kWh
- Cloud cover: {weather_cloud_pct:.0f}%
- Temperature: {temperature_c:.0f}°C

Based on this data, provide ONE specific actionable recommendation.
Response format (JSON only):
{{
  "action": "CHARGE_BATTERY" or "DISCHARGE_BATTERY" or "SELL_SURPLUS" or "BUY_GRID" or "NO_ACTION",
  "title": "Short title (max 10 words)",
  "description": "Brief explanation why (max 30 words)",
  "expected_savings_eur": number,
  "confidence_pct": number (0-100)
}}"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                XAI_API_URL,
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": XAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an energy optimization AI. Respond only in valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
            )

            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                # Parse JSON from response
                recommendation = json.loads(content)
                logger.info(f"AI recommendation: {recommendation.get('title')}")
                return {
                    "source": "grok_ai",
                    "model": XAI_MODEL,
                    **recommendation,
                }
            else:
                logger.warning(f"AI API error: {res.status_code} {res.text[:200]}")
                return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)

    except json.JSONDecodeError:
        logger.warning("AI response not valid JSON — falling back")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)
    except Exception as e:
        logger.error(f"AI service error: {e}")
        return _rule_based_fallback(solar_kwh, consumption_kwh, battery_soc, grid_price)


def _rule_based_fallback(
    solar_kwh: float, consumption_kwh: float, battery_soc: float, grid_price: float
) -> dict:
    """Fallback when AI API is not available."""
    if solar_kwh < consumption_kwh * 0.5 and grid_price > 0.25 and battery_soc < 60:
        return {
            "source": "rule_engine",
            "action": "CHARGE_BATTERY",
            "title": "Charge battery before peak hours",
            "description": "Low solar + high grid price coming. Charge now to avoid expensive peak.",
            "expected_savings_eur": round((consumption_kwh - solar_kwh) * 0.1, 2),
            "confidence_pct": 82,
        }
    elif solar_kwh > consumption_kwh * 1.3 and battery_soc > 80:
        return {
            "source": "rule_engine",
            "action": "SELL_SURPLUS",
            "title": "Sell surplus solar energy",
            "description": "Solar surplus available and battery full. Export to grid for revenue.",
            "expected_savings_eur": round((solar_kwh - consumption_kwh) * grid_price * 0.6, 2),
            "confidence_pct": 78,
        }
    elif battery_soc > 60 and grid_price > 0.28:
        return {
            "source": "rule_engine",
            "action": "DISCHARGE_BATTERY",
            "title": "Use battery during peak pricing",
            "description": "Grid price is peak. Discharge battery to avoid expensive import.",
            "expected_savings_eur": round(battery_soc * 0.5 * grid_price, 2),
            "confidence_pct": 85,
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
