import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

async def search_exact_products_with_gemini(brand: str, product_title: str) -> Dict[str, Any]:
    """
    Leverages Gemini 2.0 Flash with Google Search to discover the exact direct product URLs,
    exact product titles, and live prices across Amazon India, Myntra, Nykaa, Tira, Ajio, and Newme.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Skipping Gemini live search grounding.")
        return {}

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            tools="google_search"
        )

        prompt = f"""
Find the EXACT direct product page URL and current listed price for "{brand} {product_title}" on these Indian stores:
- Amazon India (amazon.in/dp/...)
- Myntra (myntra.com/.../buy or exact product page)
- Nykaa (nykaa.com/.../p/...)
- Tira (tirabeauty.com/product/...)
- Ajio (ajio.com/.../p/...)
- NEWME (newme.asia/product/...)

CRITICAL ACCURACY RULES:
1. ONLY return direct product buy page URLs (do NOT return search pages or category pages).
2. If this product/brand is EXCLUSIVE to one store and NOT sold on another store (e.g. NEWME brand is exclusive to newme.asia and not sold on Myntra or Ajio), set "available": false for that store with the reason. DO NOT fabricate a URL or match an unrelated brand!
3. If an identical product exists on that store, return its EXACT direct product URL and exact title.
4. Return the listed price in INR if found.

Return ONLY a valid JSON object in this schema:
{{
  "stores": {{
    "Myntra": {{ "available": false, "direct_url": null, "title": null, "price": null, "reason": "Exclusive brand, not sold on Myntra" }},
    "NEWME": {{ "available": true, "direct_url": "https://newme.asia/product/...", "title": "...", "price": 799 }},
    "Amazon": {{ "available": true, "direct_url": "https://www.amazon.in/dp/...", "title": "...", "price": 849 }}
  }}
}}
"""
        response = await model.generate_content_async(prompt)
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        data = json.loads(text)
        return data.get("stores", {})
    except Exception as e:
        logger.error(f"Gemini live search failed: {e}")
        return {}
