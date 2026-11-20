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

def detect_store_from_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "tira" in domain:
        return "Tira"
    elif "nykaa" in domain:
        return "Nykaa"
    elif "blinkit" in domain:
        return "Blinkit"
    elif "zepto" in domain:
        return "Zepto"
    elif "amazon" in domain:
        return "Amazon"
    elif "purplle" in domain:
        return "Purplle"
    elif "myntra" in domain:
        return "Myntra"
    elif "ajio" in domain:
        return "Ajio"
    elif "newme" in domain:
        return "NEWME"
    elif "urbanic" in domain:
        return "Urbanic"
    elif "savana" in domain:
        return "Savana"
    elif "flipkart" in domain:
        return "Flipkart"
    return "Online Store"

async def extract_url_metadata(url: str) -> Dict[str, Any]:
    """Fetch OpenGraph tags, title, and schema microdata from the URL."""
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
        "store": detect_store_from_url(url)
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
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
    
    # Fallback if title still empty: extract clean text from URL path
    if not metadata["title"]:
        path = urlparse(url).path
        cleaned_path = re.sub(r'[/_\-\?=&]', ' ', path)
        cleaned_path = re.sub(r'\b(p|dp|product|item|buy|online|in|html)\b', '', cleaned_path, flags=re.I)
        metadata["title"] = " ".join(cleaned_path.split())

    return metadata

async def normalize_product_with_gemini(raw_text_or_url: str) -> NormalizedProduct:
    """Use Gemini Flash to parse raw URL metadata into a standardized, exact product entity."""
    is_url = bool(re.match(r'^https?://', raw_text_or_url.strip()))
    
    if is_url:
        meta = await extract_url_metadata(raw_text_or_url)
        store = meta.get("store") or detect_store_from_url(raw_text_or_url)
        raw_info = f"URL: {raw_text_or_url}\nStore: {store}\nExtracted Title: {meta.get('title')}\nDescription: {meta.get('description')}"
        thumbnail = meta.get("image")
    else:
        raw_info = f"Product Search Query: {raw_text_or_url}"
        store = "Direct Search"
        thumbnail = None

    prompt = f"""
You are an expert Indian e-commerce product extraction engine.
Analyze the following product details scraped from an Indian shopping website:
---
{raw_info}
---
TASK:
Extract the exact, authentic product identity without any marketing fluff.
Rules:
1. Identify the exact Brand (e.g. Minimalist, Maybelline, Dot & Key, Cetaphil, L'Oreal, Laneige).
2. Extract the core Product Name (e.g. Niacinamide 10% Face Serum).
3. Extract the Variant/Volume/Shade if present (e.g. 30ml, 50ml, Shade 128 Warm Nude, 20g).
4. Assign the appropriate category: Skincare, Makeup, Haircare, Fragrance, Body Care, or Fashion.
5. Generate the normalized_title combining Brand + Product Name + Variant.
6. Generate an optimized search_query for searching this exact SKU across Tira, Nykaa, Blinkit, and Zepto.

Return ONLY a valid JSON object matching this schema:
{{
  "brand": "...",
  "product_name": "...",
  "variant": "...",
  "category": "...",
  "normalized_title": "...",
  "search_query": "..."
}}
"""

    # Call Gemini API
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            data = json.loads(response.text)
            return NormalizedProduct(
                brand=data.get("brand", "Unknown Brand"),
                product_name=data.get("product_name", raw_text_or_url),
                variant=data.get("variant"),
                category=data.get("category", "Beauty & Personal Care"),
                normalized_title=data.get("normalized_title", raw_text_or_url),
                search_query=data.get("search_query", raw_text_or_url),
                source_store=store,
                thumbnail_url=thumbnail,
                original_url=raw_text_or_url if is_url else None
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Using rule-based fallback.")

    # Rule-based fallback if no Gemini API Key or API error
    title = meta.get("title") if is_url else raw_text_or_url
    
    # Clean brand suffixes like " - NEWME", " | Nykaa", " - Myntra"
    brand_guess = "Generic"
    clean_title = title
    if store and store != "Online Store":
        brand_guess = store
    
    for sep in [" - ", " | ", " – ", " — "]:
        if sep in clean_title:
            parts = clean_title.split(sep)
            if len(parts) >= 2:
                # e.g. "White Polka Dot Tube Top - NEWME" -> brand="NEWME", clean_title="White Polka Dot Tube Top"
                last_part = parts[-1].strip()
                if last_part.upper() in ["NEWME", "NYKAA", "MYNTRA", "AJIO", "TIRA", "AMAZON", "URBANIC"]:
                    brand_guess = last_part.upper()
                    clean_title = " ".join(parts[:-1]).strip()

    fashion_keywords = ["top", "dress", "jeans", "shirt", "skirt", "kurta", "pant", "hoodie", "tshirt", "t-shirt", "corset", "tube", "blazer", "trouser", "sweatshirt"]
    is_fashion = any(kw in clean_title.lower() for kw in fashion_keywords) or store in ["NEWME", "Myntra", "Ajio", "Urbanic"]
    category = "Fashion & Apparel" if is_fashion else "Beauty & Personal Care"

    if brand_guess == "Generic":
        words = clean_title.split()
        brand_guess = words[0] if words else "Generic"
    
    return NormalizedProduct(
        brand=brand_guess,
        product_name=clean_title,
        variant=None,
        category=category,
        normalized_title=f"{brand_guess} {clean_title}" if brand_guess.lower() not in clean_title.lower() else clean_title,
        search_query=f"{brand_guess} {clean_title} buy online India",
        source_store=store,
        thumbnail_url=thumbnail,
        original_url=raw_text_or_url if is_url else None
    )
