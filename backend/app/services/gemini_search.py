import json
import logging
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

async def search_exact_products_with_gemini(
    brand: str,
    product_title: str,
    target_stores: Optional[List[str]] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Leverages Gemini 2.0 Flash with Google Search Grounding to discover the exact direct product URLs,
    live selling prices, real product listing photos, and store availability across Indian retail platforms.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Skipping Gemini live search grounding.")
        return {}

    try:
        from google.generativeai import protos
        genai.configure(api_key=settings.GEMINI_API_KEY)
        try:
            search_tool = protos.Tool(google_search=protos.Tool.GoogleSearch())
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                tools=[search_tool]
            )
        except Exception as tool_init_err:
            logger.warning(f"protos.Tool GoogleSearch init failed: {tool_init_err}. Using standard gemini-2.0-flash.")
            model = genai.GenerativeModel(model_name="gemini-2.0-flash")

        if target_stores and len(target_stores) > 0:
            stores_formatted = "\n".join([f"- {s}" for s in target_stores])
        else:
            stores_formatted = """- Amazon India (amazon.in)
- Flipkart (flipkart.com)
- Croma (croma.com)
- Official Brand Store
- Nykaa (nykaa.com)
- Tira (tirabeauty.com)
- Blinkit (blinkit.com)
- Myntra (myntra.com)
- Ajio (ajio.com)
- NEWME (newme.asia)"""

        prompt = f"""
You are an expert Indian e-commerce web intelligence engine powered by Google Search.
Search Google for the exact product: "{brand} {product_title}" across these specific retail platforms in India:
{stores_formatted}

CRITICAL ACCURACY RULES:
1. ONLY return direct product buy page URLs (e.g. https://www.amazon.in/dp/..., https://www.flipkart.com/.../p/..., https://www.croma.com/.../p/..., https://newme.asia/product/...). NEVER return broken search query URLs or internal category pages!
2. If this product/brand is NOT sold on that store (e.g. NEWME is exclusive to newme.asia and NOT on Myntra/Ajio/Amazon; or an item is not in stock / not listed on Croma), set "available": false with a clear reason. DO NOT fabricate a URL or match an unrelated product!
3. If the product exists on that store, return its EXACT direct product URL and exact listing title.
4. Extract the direct product image/photo thumbnail URL from that store's product listing if available.
5. Return the listed selling price in INR as a number.

Return ONLY a valid JSON object in this schema:
{{
  "stores": {{
    "Store Name": {{
      "available": true,
      "direct_url": "https://...",
      "title": "Exact Title on Store",
      "price": 1499,
      "image_url": "https://...",
      "in_stock": true,
      "reason": "Exact match found"
    }}
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
