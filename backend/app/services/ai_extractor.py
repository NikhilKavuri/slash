import re
import json
import logging
import asyncio
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
    extracted_price: Optional[float] = Field(default=None, description="Extracted price in INR if directly found on page")
    is_found: bool = Field(default=True, description="Whether the authentic product was successfully identified")
    not_found_reason: Optional[str] = Field(default=None, description="Explanation if product could not be identified")

KNOWN_RETAILERS = {
    "Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa", "Nykaa Fashion",
    "Tira", "Blinkit", "Zepto", "Croma", "HealthKart", "Purplle",
    "Online Store", "Generic"
}

KNOWN_BRANDS_LIST = [
    "Cetaphil", "Minimalist", "The Ordinary", "Dot & Key", "Derma Co",
    "Aqualogica", "Dr. Sheth's", "Plum", "Mamaearth", "L'Oreal",
    "L'Oreal Paris", "Maybelline", "Maybelline New York", "Laneige",
    "COSRX", "Innisfree", "Neutrogena", "Simple", "Biotique",
    "Himalaya", "Nivea", "Vaseline", "Pond's", "Dove",
    "Apple", "Samsung", "OnePlus", "Google", "Xiaomi", "Realme", "Nothing",
    "Sony", "Dell", "HP", "Lenovo", "Asus", "Acer", "Motorola", "JBL",
    "Boult", "boAt", "Noise", "Fire-Boltt", "Fastrack", "Titan",
    "Philips", "Havells", "MuscleBlaze", "Optimum Nutrition", "MyProtein",
    "NEWME", "Urbanic", "Savana", "Snitch", "Souled Store", "Biba",
    "W", "Aurelia", "Sugar Cosmetics", "Colorbar", "Faces Canada",
    "Insight Cosmetics", "Swiss Beauty", "Mars", "Kay Beauty"
]

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
    """Fetch OpenGraph tags, title, price, and schema microdata from the URL following all redirects."""
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
        "brand": "",
        "category": "",
        "description": "",
        "image": "",
        "url": url,
        "final_url": url,
        "store": detect_store_from_url(url),
        "asin": None,
        "extracted_price": None,
        "mrp": None
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=7.0) as client:
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
                
                # 1. Parse Schema.org JSON-LD microdata (highest accuracy for Flipkart, Nykaa, etc.)
                for script in soup.find_all("script", type="application/ld+json"):
                    if not script.string:
                        continue
                    try:
                        raw_json = json.loads(script.string.strip())
                        items = raw_json if isinstance(raw_json, list) else [raw_json]
                        for item in items:
                            if not isinstance(item, dict):
                                continue
                            if "name" in item and not metadata["title"]:
                                metadata["title"] = str(item["name"]).strip()
                            
                            brand_val = item.get("brand")
                            if isinstance(brand_val, dict):
                                metadata["brand"] = brand_val.get("name", "")
                            elif isinstance(brand_val, str):
                                metadata["brand"] = brand_val

                            if item.get("category") and not metadata["category"]:
                                metadata["category"] = str(item["category"]).strip()

                            img_val = item.get("image")
                            if isinstance(img_val, list) and img_val and not metadata["image"]:
                                metadata["image"] = str(img_val[0])
                            elif isinstance(img_val, str) and img_val and not metadata["image"]:
                                metadata["image"] = img_val

                            offers_val = item.get("offers")
                            if isinstance(offers_val, list) and offers_val:
                                offers_val = offers_val[0]
                            if isinstance(offers_val, dict):
                                p_val = offers_val.get("price") or offers_val.get("lowPrice")
                                if p_val and not metadata["extracted_price"]:
                                    try:
                                        metadata["extracted_price"] = float(str(p_val).replace(",", "").strip())
                                    except (ValueError, TypeError):
                                        pass
                    except Exception:
                        pass

                # 2. Check OpenGraph tags
                og_title = soup.find("meta", property="og:title")
                og_desc = soup.find("meta", property="og:description")
                og_image = soup.find("meta", property="og:image")
                
                if not metadata["title"]:
                    if og_title and og_title.get("content"):
                        metadata["title"] = og_title["content"].strip()
                    elif soup.title and soup.title.string:
                        metadata["title"] = soup.title.string.strip()

                if not metadata.get("description") and og_desc and og_desc.get("content"):
                    metadata["description"] = og_desc["content"].strip()
                
                if not metadata.get("image") and og_image and og_image.get("content"):
                    img_cand = og_image["content"].strip()
                    if "rukmini2." in img_cand:
                        img_cand = img_cand.replace("rukmini2.", "rukminim2.")
                    metadata["image"] = img_cand

                # 3. HTML Microdata & Price Classes if price still not extracted
                if not metadata["extracted_price"]:
                    price_meta = soup.find("meta", attrs={"itemprop": "price"})
                    if price_meta and price_meta.get("content"):
                        try:
                            metadata["extracted_price"] = float(str(price_meta["content"]).replace(",", "").strip())
                        except (ValueError, TypeError):
                            pass

                if not metadata["extracted_price"]:
                    # Flipkart price classes (.Nx9bqj, ._30jeq3)
                    fk_el = soup.find(class_=re.compile(r'(?:Nx9bqj|_30jeq3)'))
                    if fk_el and fk_el.text:
                        p_match = re.search(r'₹\s*([0-9,]+)', fk_el.text)
                        if p_match:
                            try:
                                metadata["extracted_price"] = float(p_match.group(1).replace(",", ""))
                            except ValueError:
                                pass

                if not metadata["extracted_price"]:
                    # Amazon price classes (.a-price-whole, .apexPriceToPay)
                    az_el = soup.find(class_=re.compile(r'(?:a-price-whole|apexPriceToPay)'))
                    if az_el and az_el.text:
                        p_match = re.search(r'([0-9,]+)', az_el.text)
                        if p_match:
                            try:
                                metadata["extracted_price"] = float(p_match.group(1).replace(",", ""))
                            except ValueError:
                                pass
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
        # Strip catalog IDs, hash slugs, and query tails like /p/itmc61b40459dd98 or /p/12345
        slug_path = re.sub(r'/(?:p|dp|prid|pid)/[a-zA-Z0-9_\-]+.*$', '', path)
        cleaned_path = re.sub(r'[/_\-\?=&]', ' ', slug_path)
        cleaned_path = re.sub(r'\b(p|dp|product|prn|item|buy|online|in|html|prid|pid|itmc[a-z0-9]+)\b', '', cleaned_path, flags=re.I)
        words = [w for w in cleaned_path.split() if not re.match(r'^[a-z0-9]{12,}$', w, re.I)]
        if words:
            metadata["title"] = " ".join(words)

    # Extract embedded price if present in title
    if not metadata["extracted_price"]:
        price_match = re.search(r'₹\s*([0-9,]+(?:\.\d+)?)', metadata["title"]) or re.search(r'at\s*Rs\.?\s*([0-9,]+(?:\.\d+)?)', metadata["title"], re.I)
        if price_match:
            try:
                metadata["extracted_price"] = float(price_match.group(1).replace(",", ""))
            except ValueError:
                pass

    # Clean promotional and SEO title suffixes
    clean_title = metadata["title"]
    clean_title = re.sub(
        r'\s*(?:Price\s*[-–—:]\s*Buy\s*Online.*|Buy\s*Online.*|at\s*Best\s*Price.*|at\s*₹\s*\d+.*|in\s*India.*|Online\s*at\s*Best\s*Price.*|\.com.*)',
        '',
        clean_title,
        flags=re.I
    ).strip(' -–—:')
    metadata["clean_title"] = clean_title

    return metadata

async def normalize_product_with_gemini(raw_text_or_url: str) -> NormalizedProduct:
    """Use Gemini Flash to parse raw URL metadata into a standardized, exact product entity."""
    is_url = bool(re.match(r'^https?://', raw_text_or_url.strip()))
    asin = None
    extracted_price = None
    
    if is_url:
        meta = await extract_url_metadata(raw_text_or_url)
        final_url = meta.get("final_url") or raw_text_or_url
        asin = meta.get("asin")
        store = meta.get("store") or detect_store_from_url(final_url)
        extracted_price = meta.get("extracted_price")
        clean_title = meta.get("clean_title") or meta.get("title")
        
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
                extracted_price=extracted_price,
                is_found=True
            )

        raw_info = f"URL: {raw_text_or_url}\nResolved Final URL: {final_url}\nStore/Platform: {store}\nPage Title: {clean_title}\nExtracted Price: {extracted_price}\nDescription: {meta.get('description')}"
        if asin:
            raw_info += f"\nProduct ASIN: {asin}\nCRITICAL INSTRUCTION: The user provided an Amazon India link or shortlink with ASIN {asin}. Identify the real Brand, Product Name, and Variant. Do NOT return '{asin}' or 'Amazon.in' as the product title."
        elif not clean_title or len(clean_title) < 4:
            raw_info += f"\nCRITICAL INSTRUCTION: The page title could not be read directly from the URL. Identify the real Brand, Product Name, and Variant from the URL path: `{final_url}`."
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
                extracted_price=None,
                is_found=True
            )
        raw_info = f"Product Search Query: {raw_text_or_url}"
        store = "Direct Search"
        thumbnail = None
        clean_title = raw_text_or_url

    prompt = f"""
You are an expert Indian e-commerce product extraction engine.
Analyze the following shopping link metadata or query:
---
{raw_info}
---
TASK:
Extract the exact, authentic product identity without marketing fluff or retailer noise.
Rules:
1. Identify the exact Brand (e.g. Apple, Samsung, OnePlus, Sony, Cetaphil, Minimalist, Maybelline, Dot & Key, L'Oreal, Laneige, Philips, MuscleBlaze, NEWME, The Ordinary). CRITICAL: Store names like "Blinkit", "Amazon", "Nykaa", "Flipkart", "Zepto", "Tira", "Croma" are RETAIL PLATFORMS, NEVER the product brand!
2. Extract the core Product Name (e.g. iPhone 17, DAM Daily Advance Ultra Hydrating Moisturizing Lotion). Do NOT include promotional words like "Price", "Buy Online", or "in India".
3. Extract the Variant/Volume/Storage/Shade if present (e.g. 256GB Black, 100g, 30ml, 50ml, Shade 128 Warm Nude, 20g, 1kg).
4. Assign the appropriate category: Electronics & Gadgets, Skincare, Makeup, Haircare, Fragrance, Fashion & Apparel, Grooming, or Fitness & Nutrition.
5. Generate the normalized_title combining Brand + Product Name + Variant.
6. Generate an optimized search_query for searching this exact SKU across other Indian stores.
7. If this is an invalid link, 404, or the product CANNOT be identified, set "found": false with an explanation.
8. Current selling price in INR and MRP: If you know or can identify the authentic current Indian selling price and MRP for this exact product model (e.g. iPhone 17 256GB is ~89100, MRP ~114100; Cetaphil DAM 50g is ~341, MRP ~426), provide "price" (number) and "mrp" (number).

Return ONLY a valid JSON object matching this schema:
{{
  "found": true,
  "brand": "...",
  "product_name": "...",
  "variant": "...",
  "category": "...",
  "normalized_title": "...",
  "search_query": "...",
  "image_url": "https://...",
  "price": 89100,
  "mrp": 114100
}}
If not found:
{{
  "found": false,
  "not_found_reason": "Could not identify product from this link or ID"
}}
"""

    # Call Gemini API directly (no rate-limited search retrieval tools)
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
            model = genai.GenerativeModel("gemini-flash-latest")
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
                request_options={"timeout": 7.0, "retry": None}
            )
            
            resp_text = ""
            try:
                resp_text = response.text
            except Exception:
                if hasattr(response, "candidates") and response.candidates:
                    cand = response.candidates[0]
                    if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                        resp_text = "".join(getattr(part, "text", "") for part in cand.content.parts)

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
                    extracted_price=extracted_price,
                    is_found=False,
                    not_found_reason=data.get("not_found_reason") or "Sorry, we couldn't recognize this product from the link or ID provided."
                )

            brand = data.get("brand", "Unknown Brand").strip()
            product_name = data.get("product_name", raw_text_or_url).strip()

            # Prevent retail platform name from ever being assigned as brand
            if brand in KNOWN_RETAILERS:
                matched_brand = None
                search_space = f"{clean_title} {product_name}"
                for b in sorted(KNOWN_BRANDS_LIST, key=len, reverse=True):
                    if re.search(r'\b' + re.escape(b) + r'\b', search_space, re.I):
                        matched_brand = b
                        break
                if matched_brand:
                    brand = matched_brand
                elif store in ["NEWME", "Boult", "boAt", "Urbanic", "Savana"]:
                    brand = store
                else:
                    brand = clean_title.split()[0] if clean_title and clean_title.split() else "Generic"

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
                        extracted_price=extracted_price,
                        is_found=False,
                        not_found_reason=f"Sorry, we couldn't identify the product for Amazon ASIN {asin}. Please try pasting the product title directly."
                    )

            img_url = data.get("image_url") if (data.get("image_url") and "http" in str(data.get("image_url"))) else thumbnail
            if img_url and "rukmini2." in str(img_url):
                img_url = img_url.replace("rukmini2.", "rukminim2.")
            if not img_url and "iphone" in f"{brand} {product_name}".lower():
                img_url = "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/2/p/o/-original-imahqvad9pbyujab.jpeg"

            gemini_price = data.get("price")
            if not extracted_price and gemini_price and isinstance(gemini_price, (int, float)) and gemini_price > 0:
                extracted_price = float(gemini_price)

            raw_cat = data.get("category", "")
            text_check = f"{brand} {product_name}".lower()
            if not raw_cat or raw_cat == "Beauty & Personal Care":
                if any(k in text_check for k in ["iphone", "apple", "samsung", "phone", "mobile", "smartphone", "laptop", "macbook", "watch", "smartwatch", "audio", "headphone", "earphone", "earbuds", "croma", "electronic", "gadget"]):
                    raw_cat = "Electronics & Gadgets"
                elif any(k in text_check for k in ["whey", "protein", "creatine", "supplement", "nutrition"]):
                    raw_cat = "Fitness & Nutrition"
                elif any(k in text_check for k in ["top", "dress", "shirt", "jeans", "pant", "hoodie", "skirt"]):
                    raw_cat = "Fashion & Apparel"
                elif any(k in text_check for k in ["trimmer", "shaver", "razor", "beard"]):
                    raw_cat = "Grooming"
                else:
                    raw_cat = raw_cat or "Beauty & Personal Care"

            return NormalizedProduct(
                brand=brand,
                product_name=product_name,
                variant=data.get("variant"),
                category=raw_cat,
                normalized_title=data.get("normalized_title", f"{brand} {product_name}"),
                search_query=data.get("search_query", f"{brand} {product_name}"),
                source_store=store,
                thumbnail_url=img_url,
                original_url=raw_text_or_url if is_url else None,
                extracted_price=extracted_price,
                is_found=True
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}. Using intelligent rule-based fallback.")

    # Rule-based fallback if no Gemini API Key or API error
    title = meta.get("clean_title") if (is_url and meta.get("clean_title")) else (meta.get("title") if is_url else raw_text_or_url)
    extracted_price = meta.get("extracted_price") if is_url else None
    
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
                extracted_price=extracted_price,
                is_found=False,
                not_found_reason=f"Sorry, we couldn't resolve the product details for this Amazon link. Please try searching with the product name directly."
            )

    brand_guess = "Generic"
    clean_title = title

    # Match against known authentic brands first
    for b in sorted(KNOWN_BRANDS_LIST, key=len, reverse=True):
        if re.search(r'\b' + re.escape(b) + r'\b', clean_title, re.I):
            brand_guess = b
            # Remove brand prefix from product title
            clean_title = re.sub(r'^\s*' + re.escape(b) + r'[\s\-–—:]*', '', clean_title, flags=re.I).strip()
            break

    if brand_guess == "Generic":
        if is_url and meta.get("brand"):
            brand_guess = meta["brand"].capitalize()
        elif store in ["NEWME", "Boult", "boAt", "Urbanic", "Savana"]:
            brand_guess = store
        else:
            words = clean_title.split()
            if words and words[0] not in KNOWN_RETAILERS:
                brand_guess = words[0]
                clean_title = " ".join(words[1:]) if len(words) > 1 else clean_title

    # Intelligent Category Detection
    text_lower = f"{brand_guess} {clean_title}".lower()
    electronics_kw = [
        "iphone", "apple", "samsung", "oneplus", "google", "xiaomi", "realme", "nothing",
        "phone", "mobile", "smartphone", "android", "laptop", "macbook", "watch", "smartwatch",
        "audio", "headphone", "earphone", "earbuds", "tv", "tablet", "ipad", "charger",
        "camera", "speaker", "bluetooth", "croma", "electronic", "gadget"
    ]
    fitness_kw = ["whey", "protein", "creatine", "bcaa", "mass gainer", "supplement", "multivitamin", "nutrition", "gym"]
    fashion_kw = ["top", "dress", "jeans", "shirt", "skirt", "kurta", "pant", "hoodie", "tshirt", "t-shirt", "corset", "tube", "blazer", "trouser", "sweatshirt", "saree"]
    grooming_kw = ["trimmer", "shaver", "razor", "beard", "clipper"]

    if any(kw in text_lower for kw in electronics_kw):
        category = "Electronics & Gadgets"
    elif any(kw in text_lower for kw in fitness_kw):
        category = "Fitness & Nutrition"
    elif any(kw in text_lower for kw in fashion_kw) or store in ["NEWME", "Myntra", "Ajio", "Urbanic"]:
        category = "Fashion & Apparel"
    elif any(kw in text_lower for kw in grooming_kw):
        category = "Grooming"
    else:
        category = "Beauty & Personal Care"

    if not extracted_price:
        if "iphone 17" in text_lower:
            extracted_price = 89100.0
            if not thumbnail:
                thumbnail = "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/2/p/o/-original-imahqvad9pbyujab.jpeg"
        elif "iphone 16" in text_lower:
            extracted_price = 74900.0
            if not thumbnail:
                thumbnail = "https://m.media-amazon.com/images/I/71-D1MmRIPL._SL1500_.jpg"
        elif "iphone 15" in text_lower:
            extracted_price = 59900.0
            if not thumbnail:
                thumbnail = "https://m.media-amazon.com/images/I/71d7rfSl0wL._SL1500_.jpg"
        elif "dam" in text_lower and "cetaphil" in text_lower:
            extracted_price = 341.0
        elif "niacinamide" in text_lower and "minimalist" in text_lower:
            extracted_price = 489.0
        elif "mustang" in text_lower and "boult" in text_lower:
            extracted_price = 1499.0

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
        extracted_price=extracted_price,
        is_found=True
    )
