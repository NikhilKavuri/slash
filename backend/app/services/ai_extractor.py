import re
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

class NormalizedProduct(BaseModel):
    brand: str = Field(description="Brand of the product, e.g. Minimalist, Maybelline, Laneige")
    product_name: str = Field(description="Product name without brand, e.g. Niacinamide 10% Face Serum")
    variant: Optional[str] = Field(default=None, description="Size, volume, or shade, e.g. 30ml, Shade 128 Warm Nude")
    category: str = Field(description="Category: Skincare, Makeup, Haircare, Fragrance, Body Care, or Fashion")
    normalized_title: str = Field(description="Clean, official product title e.g. Minimalist Niacinamide 10% Face Serum 30ml")
    search_query: str = Field(description="Optimized query string to find this exact SKU across other Indian stores")
    source_store: Optional[str] = Field(default=None, description="Store identified from URL e.g. Tira, Nykaa, Blinkit, Zepto, Amazon")
    thumbnail_url: Optional[str] = Field(default=None, description="Image URL extracted from the page")
    original_url: Optional[str] = Field(default=None, description="Input URL")
    is_found: bool = Field(default=True, description="Whether the authentic product was successfully identified")
    not_found_reason: Optional[str] = Field(default=None, description="Explanation if product could not be identified")

def detect_store_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "amzn." in domain or "amazon" in domain:
        return "Amazon"
    elif "tira" in domain:
        return "Tira"
    elif "nykaa" in domain:
        return "Nykaa"
    elif "bkt.co" in domain or "blinkit" in domain:
        return "Blinkit"
    elif "zepto" in domain:
        return "Zepto"
    elif "fkrt.it" in domain or "flipkart" in domain:
        return "Flipkart"
    elif "myntr." in domain or "myntra" in domain:
        return "Myntra"
    elif "ajio" in domain:
        return "Ajio"
    elif "newme" in domain:
        return "NEWME"
    elif "urbanic" in domain:
        return "Urbanic"
    elif "savana" in domain:
        return "Savana"
    elif "purplle" in domain:
        return "Purplle"
    elif "boultaudio" in domain or "boult" in domain:
        return "Boult"
    elif "boat-lifestyle" in domain:
        return "boAt"
    elif "croma" in domain:
        return "Croma"
    elif "healthkart" in domain:
        return "HealthKart"
    return "Online Store"

KNOWN_ASINS = {
    "B0GYYM57FP": {
        "brand": "Boult",
        "product_name": "Mustang Muscle Smart Watch (2.01\" Curved HD Display)",
        "category": "Electronics & Wearables",
        "variant": "2.01\" Curved Display",
        "normalized_title": "GOBOULT Mustang Muscle Smart Watch (2.01\" Curved HD Display)",
        "search_query": "Boult Mustang Muscle Smart Watch",
        "image": "https://m.media-amazon.com/images/I/71u9-pD3DYL._SL1500_.jpg"
    },
    "B09GLV56C3": {
        "brand": "Minimalist",
        "product_name": "10% Niacinamide Face Serum with Zinc",
        "category": "Skincare",
        "variant": "30ml",
        "normalized_title": "Minimalist 10% Niacinamide Face Serum with Zinc (30ml)",
        "search_query": "Minimalist Niacinamide 10% Face Serum 30ml",
        "image": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop&q=60"
    },
    "B08HRZ1W5P": {
        "brand": "Philips",
        "product_name": "Series 1000 Cordless Beard Trimmer (BT1232/15)",
        "category": "Grooming",
        "variant": "BT1232/15",
        "normalized_title": "Philips Series 1000 Cordless Beard Trimmer (BT1232/15)",
        "search_query": "Philips BT1232 15 Cordless Beard Trimmer",
        "image": "https://images.unsplash.com/photo-1621607512214-68297480165e?w=500&auto=format&fit=crop&q=60"
    },
    "B084D87R44": {
        "brand": "MuscleBlaze",
        "product_name": "Biozyme Performance Whey (Rich Chocolate)",
        "category": "Fitness & Nutrition",
        "variant": "1kg",
        "normalized_title": "MuscleBlaze Biozyme Performance Whey (1kg Rich Chocolate)",
        "search_query": "MuscleBlaze Biozyme Performance Whey Protein 1kg",
        "image": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?w=500&auto=format&fit=crop&q=60"
    },
    "B08H4V4W4P": {
        "brand": "Maybelline",
        "product_name": "Lash Sensational Sky High Waterproof Mascara",
        "category": "Makeup",
        "variant": "Waterproof Very Black",
        "normalized_title": "Maybelline New York Lash Sensational Sky High Mascara",
        "search_query": "Maybelline Lash Sensational Sky High Mascara",
        "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop&q=60"
    }
}

async def extract_url_metadata(url: str) -> Dict[str, Any]:
    """Fetch OpenGraph tags, title, and schema microdata from the URL following all redirects."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    metadata = {
        "title": "",
        "description": "",
        "image": "",
        "url": url,
        "final_url": url,
        "store": detect_store_from_url(url),
        "asin": None
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            final_url = str(resp.url)
            metadata["final_url"] = final_url
            metadata["store"] = detect_store_from_url(final_url)

            # Detect ASIN from final URL or original URL
            asin_match = re.search(r'/(?:dp|gp/product|d)/([A-Z0-9]{10})', final_url, re.I) or re.search(r'/(?:dp|gp/product|d)/([A-Z0-9]{10})', url, re.I)
            if asin_match:
                metadata["asin"] = asin_match.group(1).upper()

            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Check OpenGraph
                og_title = soup.find("meta", property="og:title")
                og_desc = soup.find("meta", property="og:description")
                og_image = soup.find("meta", property="og:image")
                
                if og_title and og_title.get("content"):
                    metadata["title"] = og_title["content"].strip()
                elif soup.title and soup.title.string:
                    metadata["title"] = soup.title.string.strip()

                if og_desc and og_desc.get("content"):
                    metadata["description"] = og_desc["content"].strip()
                
                if og_image and og_image.get("content"):
                    metadata["image"] = og_image["content"].strip()
    except Exception as e:
        logger.warning(f"Could not scrape URL directly: {e}. Falling back to URL path parsing.")
    
    # Clean junk titles from bot interstitials or block pages
    junk_patterns = [
        r'\bamazon\.in\b', r'\brobot check\b', r'\bpage not found\b',
        r'\bsorry! something went wrong\b', r'\bonline shopping site in india\b'
    ]
    if any(re.search(p, metadata["title"], re.I) for p in junk_patterns):
        metadata["title"] = ""

    # Check for meaningful descriptive slug in final_url (especially for Amazon, Myntra, Nykaa, Blinkit)
    target_url = metadata.get("final_url") or url
    path = urlparse(target_url).path
    amazon_slug = re.search(r'/(?:[^/]+/)?([A-Za-z0-9\-]{4,})/(?:dp|gp/product|d)/[A-Z0-9]{10}', path, re.I)
    if amazon_slug and not metadata["title"]:
        slug_raw = amazon_slug.group(1).replace("-", " ")
        if not any(k in slug_raw.lower() for k in ["dp", "gp", "product", "item", "html", "buy", "ref"]):
            metadata["title"] = slug_raw

    # Fallback if title still empty: extract clean text from URL path
    if not metadata["title"]:
        cleaned_path = re.sub(r'[/_\-\?=&]', ' ', path)
        cleaned_path = re.sub(r'\b(p|dp|product|item|buy|online|in|html)\b', '', cleaned_path, flags=re.I)
        words = cleaned_path.split()
        if len(words) == 1 and re.match(r'^[A-Z0-9]{8,12}$', words[0]):
            metadata["title"] = ""
        else:
            metadata["title"] = " ".join(words)

    return metadata

async def normalize_product_with_gemini(raw_text_or_url: str) -> NormalizedProduct:
    """Use Gemini Flash with Google Search Grounding to parse raw URL metadata into a standardized, exact product entity."""
    is_url = bool(re.match(r'^https?://', raw_text_or_url.strip()))
    asin = None
    
    if is_url:
        meta = await extract_url_metadata(raw_text_or_url)
        final_url = meta.get("final_url") or raw_text_or_url
        asin = meta.get("asin")
        store = meta.get("store") or detect_store_from_url(final_url)
        
        # Check instant verified lookup if known ASIN
        if asin and asin in KNOWN_ASINS:
            item = KNOWN_ASINS[asin]
            return NormalizedProduct(
                brand=item["brand"],
                product_name=item["product_name"],
                variant=item["variant"],
                category=item["category"],
                normalized_title=item["normalized_title"],
                search_query=item["search_query"],
                source_store=store,
                thumbnail_url=meta.get("image") or item["image"],
                original_url=raw_text_or_url,
                is_found=True
            )

        raw_info = f"URL: {raw_text_or_url}\nResolved Final URL: {final_url}\nStore: {store}\nExtracted Title: {meta.get('title')}\nDescription: {meta.get('description')}"
        if asin:
            raw_info += f"\nProduct ASIN: {asin}\nCRITICAL INSTRUCTION: The user provided an Amazon India link or shortlink. Use Google Search to look up: `Amazon India {asin}` or `site:amazon.in {asin}` to identify the real Brand, Product Name, and Variant. Do NOT return '{asin}' or 'Amazon.in' as the product title."
        elif not meta.get('title') or len(meta.get('title')) < 4:
            raw_info += f"\nCRITICAL INSTRUCTION: The page title could not be read directly from the URL (likely a mobile app shortened link or ID from Blinkit, Flipkart, Myntra, etc.). Use Google Search to search for this URL or product path: `{final_url}` to identify the real Brand, Product Name, and Variant."
        thumbnail = meta.get("image")
    else:
        # Check if raw text is directly an ASIN
        raw_clean = raw_text_or_url.strip().upper()
        if re.match(r'^[A-Z0-9]{10}$', raw_clean) and raw_clean in KNOWN_ASINS:
            item = KNOWN_ASINS[raw_clean]
            return NormalizedProduct(
                brand=item["brand"],
                product_name=item["product_name"],
                variant=item["variant"],
                category=item["category"],
                normalized_title=item["normalized_title"],
                search_query=item["search_query"],
                source_store="Amazon",
                thumbnail_url=item["image"],
                original_url=None,
                is_found=True
            )
        raw_info = f"Product Search Query: {raw_text_or_url}"
        store = "Direct Search"
        thumbnail = None

    prompt = f"""
You are an expert Indian e-commerce product extraction engine equipped with Google Search.
Analyze the following shopping link or query:
---
{raw_info}
---
TASK:
Use Google Search if needed to identify the exact, authentic product identity without any marketing fluff.
Rules:
1. Identify the exact Brand (e.g. Minimalist, Maybelline, Dot & Key, Cetaphil, L'Oreal, Laneige, Philips, MuscleBlaze, NEWME, The Ordinary). NEVER output "Amazon" or "Generic" if the product is sold on Amazon!
2. Extract the core Product Name (e.g. Niacinamide 10% Face Serum with Zinc).
3. Extract the Variant/Volume/Shade if present (e.g. 30ml, 50ml, Shade 128 Warm Nude, 20g, 1kg).
4. Assign the appropriate category: Skincare, Makeup, Haircare, Fragrance, Fashion & Apparel, Grooming, or Fitness & Nutrition.
5. Generate the normalized_title combining Brand + Product Name + Variant.
6. Generate an optimized search_query for searching this exact SKU across other Indian stores.
7. If this is an invalid link, 404, or the product CANNOT be identified, set "found": false with an explanation.

Return ONLY a valid JSON object matching this schema:
{{
  "found": true,
  "brand": "...",
  "product_name": "...",
  "variant": "...",
  "category": "...",
  "normalized_title": "...",
  "search_query": "...",
  "image_url": "https://..."
}}
If not found:
{{
  "found": false,
  "not_found_reason": "Could not identify product from this link or ID"
}}
"""

    # Call Gemini API with Google Search Grounding
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            from google.generativeai import protos
            genai.configure(api_key=settings.GEMINI_API_KEY)

            resp_text = ""
            try:
                search_tool = protos.Tool(google_search=protos.Tool.GoogleSearch())
                model = genai.GenerativeModel("gemini-2.0-flash", tools=[search_tool])
                response = await model.generate_content_async(prompt)
                resp_text = response.text
            except Exception as tool_err:
                logger.warning(f"Gemini tools=GoogleSearch fallback ({tool_err}), calling standard model...")
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = await model.generate_content_async(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                resp_text = response.text

            clean_json_str = resp_text.strip()
            if "```json" in clean_json_str:
                clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json_str:
                clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()
            elif "{" in clean_json_str and "}" in clean_json_str:
                clean_json_str = clean_json_str[clean_json_str.find("{"):clean_json_str.rfind("}")+1]

            data = json.loads(clean_json_str)
            
            # If Gemini reports not found
            if data.get("found") is False:
                return NormalizedProduct(
                    brand="Unknown",
                    product_name="Product Not Found",
                    variant=None,
                    category="General",
                    normalized_title="Product Not Found",
                    search_query=raw_text_or_url,
                    source_store=store,
                    thumbnail_url=thumbnail,
                    original_url=raw_text_or_url if is_url else None,
                    is_found=False,
                    not_found_reason=data.get("not_found_reason") or "Sorry, we couldn't recognize this product from the link or ID provided."
                )

            brand = data.get("brand", "Unknown Brand").strip()
            product_name = data.get("product_name", raw_text_or_url).strip()

            # Guard against raw ASIN being returned as title
            if asin and (product_name == asin or brand.lower() in ["amazon", "generic", "unknown"]):
                if not data.get("found"):
                    return NormalizedProduct(
                        brand="Unknown",
                        product_name="Product Not Found",
                        variant=None,
                        category="General",
                        normalized_title="Product Not Found",
                        search_query=raw_text_or_url,
                        source_store=store,
                        thumbnail_url=thumbnail,
                        original_url=raw_text_or_url if is_url else None,
                        is_found=False,
                        not_found_reason=f"Sorry, we couldn't identify the product for Amazon ASIN {asin}. Please try pasting the product title directly."
                    )

            img_url = data.get("image_url") if (data.get("image_url") and "http" in str(data.get("image_url"))) else thumbnail

            return NormalizedProduct(
                brand=brand,
                product_name=product_name,
                variant=data.get("variant"),
                category=data.get("category", "Beauty & Personal Care"),
                normalized_title=data.get("normalized_title", f"{brand} {product_name}"),
                search_query=data.get("search_query", f"{brand} {product_name}"),
                source_store=store,
                thumbnail_url=img_url,
                original_url=raw_text_or_url if is_url else None,
                is_found=True
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Using rule-based fallback.")

    # Rule-based fallback if no Gemini API Key or API error
    title = meta.get("title") if is_url else raw_text_or_url
    
    # If title is empty, or contains the ASIN, or store is Amazon and title is generic/unrecognized
    if asin or store == "Amazon":
        if not title or (asin and asin in title) or title.lower() in ["amazon", "amazon.in", "product", "item"]:
            return NormalizedProduct(
                brand="Unknown",
                product_name="Product Not Found",
                variant=None,
                category="General",
                normalized_title="Product Not Found",
                search_query=raw_text_or_url,
                source_store=store,
                thumbnail_url=thumbnail,
                original_url=raw_text_or_url if is_url else None,
                is_found=False,
                not_found_reason=f"Sorry, we couldn't resolve the product details for this Amazon link. Please try searching with the product name directly."
            )

    # Clean brand suffixes like " - NEWME", " | Nykaa", " - Myntra"
    brand_guess = "Generic"
    clean_title = title
    if store and store != "Online Store":
        brand_guess = store
    
    for sep in [" - ", " | ", " – ", " — "]:
        if sep in clean_title:
            parts = clean_title.split(sep)
            if len(parts) >= 2:
                last_part = parts[-1].strip()
                if last_part.upper() in ["NEWME", "NYKAA", "MYNTRA", "AJIO", "TIRA", "AMAZON", "URBANIC"]:
                    brand_guess = last_part.upper()
                    clean_title = " ".join(parts[:-1]).strip()

    fashion_keywords = ["top", "dress", "jeans", "shirt", "skirt", "kurta", "pant", "hoodie", "tshirt", "t-shirt", "corset", "tube", "blazer", "trouser", "sweatshirt"]
    is_fashion = any(kw in clean_title.lower() for kw in fashion_keywords) or store in ["NEWME", "Myntra", "Ajio", "Urbanic"]
    category = "Fashion & Apparel" if is_fashion else "Beauty & Personal Care"

    if brand_guess in ["Generic", "Amazon", "Online Store", "Flipkart"]:
        words = clean_title.split()
        if words:
            brand_guess = words[0]
            clean_title = " ".join(words[1:]) if len(words) > 1 else clean_title
    
    normalized_title = f"{brand_guess} {clean_title}" if brand_guess.lower() not in clean_title.lower() else clean_title

    return NormalizedProduct(
        brand=brand_guess,
        product_name=clean_title,
        variant=None,
        category=category,
        normalized_title=normalized_title,
        search_query=normalized_title,
        source_store=store,
        thumbnail_url=thumbnail,
        original_url=raw_text_or_url if is_url else None,
        is_found=True
    )
