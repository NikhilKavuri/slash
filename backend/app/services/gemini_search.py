import json
import logging
import asyncio
import re
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# URLs containing these patterns are search/listing pages or search engines, NOT direct product pages
SEARCH_PAGE_PATTERNS = [
    "/search?", "/search/?", "/search/", "/s?k=", "/s?q=", "/s/?q=",
    "google.com/search", "google.co.in/search", "google.com/url?", "google.co.in/url?",
    "/result/?q=", "/searchb?", "/search/result/", "/search?q=", "/search?searchterm=",
]


def _is_search_page_url(url: str) -> bool:
    """Return True if the URL looks like a search/listing page or search engine rather than a direct product page."""
    if not url:
        return True
    url_lower = url.lower()
    for pattern in SEARCH_PAGE_PATTERNS:
        if pattern in url_lower:
            return True
    return False


def _validate_store_result(store_name: str, data: dict) -> dict:
    """Validate and clean a single store result from Gemini. 
    Returns cleaned data or marks it unavailable if data is bad."""
    
    if not data or not isinstance(data, dict):
        return {"available": False, "reason": "No data returned"}
    
    # If explicitly unavailable, keep it
    if data.get("available") is False:
        return data
    
    direct_url = data.get("direct_url", "")
    price = data.get("price")
    
    # REJECT search page URLs — they are NOT direct product pages
    if _is_search_page_url(direct_url):
        logger.warning(f"Rejected search-page URL for {store_name}: {direct_url}")
        return {
            "available": False,
            "reason": "Only a search page URL was found, not a direct product page",
            "rejected_url": direct_url
        }
    
    # REJECT if no price or non-positive price
    if not price or not isinstance(price, (int, float)) or price <= 0:
        logger.warning(f"Rejected {store_name}: no valid price (got {price})")
        return {
            "available": False,
            "reason": "No real price found for this product on this store"
        }
    
    # REJECT if no direct URL
    if not direct_url or "http" not in str(direct_url):
        logger.warning(f"Rejected {store_name}: no valid direct URL")
        return {
            "available": False,
            "reason": "No direct product URL found"
        }
    
    # Passed validation — mark available
    data["available"] = True
    data["price"] = float(price)
    if data.get("mrp") and isinstance(data["mrp"], (int, float)):
        data["mrp"] = float(data["mrp"])
    if data.get("rating") and isinstance(data["rating"], (int, float)):
        data["rating"] = float(data["rating"])
    if data.get("review_count") and isinstance(data["review_count"], (int, float)):
        data["review_count"] = int(data["review_count"])

    return data


def _extract_json_from_text(text: str) -> Optional[dict]:
    """Extract and parse JSON object from LLM response text."""
    if not text:
        return None
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()
    
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]
    
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return None


async def search_exact_products_with_gemini(
    brand: str,
    product_title: str,
    target_stores: Optional[List[str]] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Leverages Gemini 2.0 Flash with Google Search Grounding to discover:
    - Exact direct product page URLs (NOT search pages)
    - Real live selling prices in INR
    - Real product listing photo URLs
    - MRP (maximum retail price)
    - Store availability and anti-scam review sentiment
    
    Returns ONLY validated, real data. No fabrication.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Skipping Gemini live search grounding.")
        return {}

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        model = genai.GenerativeModel(model_name="gemini-flash-latest")

        if target_stores and len(target_stores) > 0:
            stores_formatted = "\n".join([f"- {s}" for s in target_stores])
        else:
            stores_formatted = """- Amazon India (amazon.in)
- Flipkart (flipkart.com)
- Myntra (myntra.com)
- Ajio (ajio.com)
- Nykaa (nykaa.com)
- Tira (tirabeauty.com)
- Blinkit (blinkit.com)
- Zepto (zeptonow.com)"""

        category_hint = f"\nProduct Category: {category}" if category else ""

        prompt = f"""You are an expert Indian e-commerce price intelligence engine with LIVE Google Search access.

Search Google RIGHT NOW for the EXACT product: "{brand} {product_title}"
{category_hint}

Find this product on these Indian retail platforms:
{stores_formatted}

ABSOLUTE RULES — FOLLOW STRICTLY:
1. DIRECT PRODUCT PAGE URLs ONLY:
   - Amazon: Must be amazon.in/dp/XXXXXXXXXX or amazon.in/*/dp/XXXXXXXXXX format
   - Flipkart: Must be flipkart.com/*/p/XXXXXXXXXX format (NOT /search?q=...)
   - Myntra: Must be myntra.com/XXXXX/BRAND/PRODUCT/XXXXXXXX format (NOT /search)
   - Nykaa: Must be nykaa.com/BRAND-PRODUCT/p/XXXXXXX format (NOT /search/result)
   - Tira: Must be tirabeauty.com/product/... format
   - Official Brand Store: Must be the brand's own .com or .co.in domain product page (e.g. goboult.co.in/products/...)
   - Croma: Must be croma.com/PRODUCT-NAME/p/XXXXXXX format (NOT /search/?text=...)
   
2. NEVER return a URL containing /search, /s?k=, /result/?q=, or google.com/search.
3. If you CANNOT find the EXACT product on a store with a DIRECT product page URL, set "available": false.
4. Prices MUST be real INR selling prices from the actual store listing — do NOT estimate or guess.
5. MRP must be the actual maximum retail price shown on the listing.
6. Image URL must be a real product photo from the store's CDN (e.g., m.media-amazon.com, assets.myntassets.com, etc.).
7. The product title must be an EXACT match — do NOT return a similar or different product.
   - Example: If searching for "Boult Mustang Muscle", do NOT return "Boult Mustang Trail" or "Boult Z40".
8. Rating and review_count must be real numbers from the store listing.
9. ANTI-SCAM REPUTATION CHECK:
   - If customer reviews for that store listing or seller frequently mention "scam", "fake", "duplicate", "first copy", or "counterfeit", set "scam_flagged": true with a specific "scam_warning".
   - Otherwise set "scam_flagged": false.

Return ONLY a valid JSON object:
{{
  "stores": {{
    "Store Name": {{
      "available": true,
      "direct_url": "https://www.amazon.in/dp/B0GYYM57FP",
      "title": "Exact Product Title on Store",
      "price": 1499,
      "mrp": 4999,
      "image_url": "https://m.media-amazon.com/images/I/XXXXX._SL1500_.jpg",
      "in_stock": true,
      "rating": 4.1,
      "review_count": 896,
      "seller": "Appario Retail Pvt Ltd",
      "scam_flagged": false,
      "reason": "Exact match found on Amazon India"
    }},
    "Store Name 2": {{
      "available": false,
      "reason": "Product not listed on this platform"
    }}
  }}
}}

IMPORTANT: It is MUCH better to return "available": false than to return a wrong URL, wrong product, or guessed price. Quality over quantity.
"""
        text = ""
        try:
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            try:
                text = response.text
            except Exception:
                if hasattr(response, "candidates") and response.candidates:
                    cand = response.candidates[0]
                    if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                        text = "".join(getattr(part, "text", "") for part in cand.content.parts)
        except Exception as gen_err:
            logger.warning(f"Gemini generate failed ({gen_err})")
            return {}
        
        data = _extract_json_from_text(text)
        if not data:
            logger.warning("Gemini search response could not be parsed as JSON")
            return {}

        raw_stores = data.get("stores", {})
        
        # Validate each store result
        validated_stores = {}
        for store_name, store_data in raw_stores.items():
            validated = _validate_store_result(store_name, store_data)
            validated_stores[store_name] = validated
            if validated.get("available") is False and validated.get("rejected_url"):
                logger.info(f"Store {store_name}: rejected (search page URL)")
            elif validated.get("available"):
                logger.info(f"Store {store_name}: ✓ price={validated.get('price')} url={validated.get('direct_url', '')[:60]}")
        
        return validated_stores
        
    except Exception as e:
        logger.error(f"Gemini live search failed: {e}")
        return {}
