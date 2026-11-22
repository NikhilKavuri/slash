import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus, urlparse
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings
from app.services.affiliate_router import affiliate_router

logger = logging.getLogger(__name__)

# Category to candidate store mapping (5-10 stores per category)
CATEGORY_STORES = {
    "Electronics & Gadgets": [
        "Amazon", "Flipkart", "Croma", "Reliance Digital", "Tata CLiQ", "Vijay Sales"
    ],
    "Fashion & Apparel": [
        "Myntra", "Ajio", "Flipkart", "Amazon", "Nykaa Fashion", "Meesho", "NEWME"
    ],
    "Beauty & Personal Care": [
        "Nykaa", "Tira", "Amazon", "Flipkart", "Purplle", "Blinkit", "Zepto"
    ],
    "Fitness & Nutrition": [
        "Amazon", "Flipkart", "HealthKart", "Blinkit", "Zepto"
    ],
    "Grooming": [
        "Amazon", "Flipkart", "Nykaa", "Croma", "Blinkit"
    ],
    "General": [
        "Amazon", "Flipkart", "Croma", "Myntra", "Blinkit"
    ]
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}


class PlaywrightScraper:
    _playwright = None
    _browser = None

    @classmethod
    async def get_browser(cls):
        """Initialise or retrieve shared headless Chromium instance."""
        if cls._browser is None or not cls._browser.is_connected():
            try:
                from playwright.async_api import async_playwright
                cls._playwright = await async_playwright().start()
                cls._browser = await cls._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-zygote"
                    ]
                )
                logger.info("Playwright Chromium browser launched successfully.")
            except Exception as e:
                logger.warning(f"Could not launch Playwright browser ({e}). Falling back to HTTP client.")
                cls._browser = None
        return cls._browser

    @classmethod
    async def close(cls):
        """Clean up browser instance."""
        if cls._browser:
            try:
                await cls._browser.close()
            except Exception:
                pass
            cls._browser = None
        if cls._playwright:
            try:
                await cls._playwright.stop()
            except Exception:
                pass
            cls._playwright = None


async def render_page_with_browser(url: str, wait_selector: Optional[str] = None, timeout_ms: int = 15000) -> Optional[str]:
    """Render dynamic JavaScript page with Playwright and return full HTML."""
    try:
        browser = await PlaywrightScraper.get_browser()
        if not browser:
            return None

        context = await browser.new_context(
            user_agent=BROWSER_HEADERS["User-Agent"],
            viewport={"width": 1280, "height": 800},
            locale="en-IN",
            timezone_id="Asia/Kolkata"
        )
        
        # Apply anti-bot stealth scripts
        try:
            from playwright_stealth import stealth_async
            page = await context.new_page()
            await stealth_async(page)
        except Exception:
            page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=4000)
                except Exception:
                    pass
            else:
                await asyncio.sleep(1.0)
            content = await page.content()
            return content
        finally:
            await page.close()
            await context.close()
    except Exception as e:
        logger.warning(f"Playwright render error for {url}: {e}")
        return None


async def fetch_page_html(url: str, wait_selector: Optional[str] = None) -> str:
    """Fetch page HTML using Playwright first, falling back to HTTPX with browser headers."""
    # Try Playwright real browser first
    html = await render_page_with_browser(url, wait_selector=wait_selector)
    if html and len(html) > 500:
        return html

    # Fallback to HTTPX
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=BROWSER_HEADERS) as client:
        resp = await client.get(url)
        return resp.text


def parse_amazon_search(html: str) -> List[Dict[str, Any]]:
    """Parse real Amazon India search results from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    cards = soup.select('div[data-component-type="s-search-result"]')
    for card in cards[:5]:
        try:
            title_el = card.select_one('h2 a span, h2 span')
            if not title_el:
                continue
            title = title_el.text.strip()
            
            link_el = card.select_one('h2 a')
            if not link_el or not link_el.get('href'):
                continue
            href = link_el['href']
            asin = card.get('data-asin') or re.search(r'/dp/([A-Z0-9]{10})', href)
            asin_str = asin.group(1) if hasattr(asin, 'group') else (asin if isinstance(asin, str) else "")
            
            if asin_str:
                direct_url = f"https://www.amazon.in/dp/{asin_str}"
            elif href.startswith("http"):
                direct_url = href.split("?")[0]
            else:
                direct_url = f"https://www.amazon.in{href}".split("?")[0]

            price_el = card.select_one('.a-price .a-offscreen') or card.select_one('.a-price-whole')
            if not price_el:
                continue
            price_match = re.search(r'([0-9,]+(?:\.\d+)?)', price_el.text.replace('₹', ''))
            if not price_match:
                continue
            price = float(price_match.group(1).replace(',', ''))
            
            mrp_el = card.select_one('.a-text-price .a-offscreen')
            mrp = price
            if mrp_el:
                mrp_match = re.search(r'([0-9,]+(?:\.\d+)?)', mrp_el.text.replace('₹', ''))
                if mrp_match:
                    mrp = float(mrp_match.group(1).replace(',', ''))
            if mrp < price:
                mrp = round(price * 1.25, 2)

            img_el = card.select_one('img.s-image')
            img_url = img_el.get('src') if img_el else None

            rating_el = card.select_one('.a-icon-alt')
            rating = 4.5
            if rating_el:
                r_match = re.search(r'([0-9.]+)\s*out', rating_el.text)
                if r_match:
                    try:
                        rating = float(r_match.group(1))
                    except ValueError:
                        pass

            results.append({
                "store": "Amazon",
                "title": title,
                "price": price,
                "mrp": mrp,
                "direct_url": direct_url,
                "image_url": img_url,
                "rating": rating,
                "seller": "Amazon Verified Brand Retailer"
            })
        except Exception as e:
            logger.debug(f"Error parsing Amazon card: {e}")
            continue

    return results


def parse_flipkart_search(html: str) -> List[Dict[str, Any]]:
    """Parse real Flipkart search results from HTML with robust fallback on link slugs and price symbols."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    items = soup.select('div._75nlfW, div[data-id], div._1AtVbE, div.cPHDOP')
    for item in items[:8]:
        try:
            # Direct product link
            link_el = item.select_one('a[href*="/p/"]') or item.select_one('a._9PwA5C, a.CGtC5Q')
            if not link_el or not link_el.get('href'):
                continue
            href = link_el['href']
            clean_href = href.split('?')[0]
            direct_url = f"https://www.flipkart.com{clean_href}" if clean_href.startswith('/') else clean_href

            # Title
            title = None
            title_el = item.select_one('div.KzDlHZ, a.wjcEIp, a.IRpwTa, div._4rR01T, a[title]')
            if title_el:
                title = title_el.get('title') or title_el.text.strip()
            if not title and '/p/' in href:
                slug = href.split('/p/')[0].lstrip('/')
                title = slug.replace('-', ' ').title()
            if not title:
                continue

            # Price
            price = None
            price_el = item.select_one('div.Nx9bqj, div._30jeq3, [class*="Nx9bqj"], [class*="_30jeq3"]')
            if price_el:
                p_match = re.search(r'([0-9,]+)', price_el.text.replace('₹', ''))
                if p_match:
                    try:
                        price = float(p_match.group(1).replace(',', ''))
                    except ValueError:
                        pass

            if not price:
                prices_in_text = re.findall(r'₹\s*([0-9,]+)', item.text)
                if prices_in_text:
                    try:
                        price = float(prices_in_text[0].replace(',', ''))
                    except ValueError:
                        pass

            if not price or price <= 0:
                continue

            # MRP
            mrp = round(price * 1.25, 2)
            prices_all = re.findall(r'₹\s*([0-9,]+)', item.text)
            if len(prices_all) > 1:
                try:
                    second_p = float(prices_all[1].replace(',', ''))
                    if second_p > price:
                        mrp = second_p
                except ValueError:
                    pass

            # Image
            img_el = item.select_one('img.DByuf4, img._53G40d, img._396cs4, img')
            img_url = img_el.get('src') if img_el else None
            if img_url and "rukmini2." in img_url:
                img_url = img_url.replace("rukmini2.", "rukminim2.")

            # Rating
            rating = 4.4
            r_el = item.select_one('div.XQDdHH, div._3LWZlK')
            if r_el:
                try:
                    rating = float(r_el.text.strip())
                except ValueError:
                    pass

            results.append({
                "store": "Flipkart",
                "title": title,
                "price": price,
                "mrp": mrp,
                "direct_url": direct_url,
                "image_url": img_url,
                "rating": rating,
                "seller": "Flipkart Official Verified Retailer"
            })
        except Exception as e:
            logger.debug(f"Error parsing Flipkart card: {e}")
            continue

    return results


def parse_croma_search(html: str) -> List[Dict[str, Any]]:
    """Parse real Croma search results from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results = []

    cards = soup.select('li.product-item, div.cp-product, div.product-info, li[class*="product"]')
    for card in cards[:6]:
        try:
            link_el = card.select_one('a[href*="/p/"]')
            if not link_el or not link_el.get('href'):
                continue
            href = link_el['href']
            clean_href = href.split('?')[0]
            direct_url = f"https://www.croma.com{clean_href}" if clean_href.startswith('/') else clean_href

            title_el = card.select_one('h3.product-title, a.product-title, [class*="product-title"]')
            title = None
            if title_el:
                title = title_el.text.strip()
            if not title and '/p/' in href:
                slug = href.split('/p/')[0].lstrip('/')
                title = slug.replace('-', ' ').title()
            if not title:
                continue

            price_el = card.select_one('span.amount, [class*="amount"], [class*="price"]')
            price = None
            if price_el:
                p_match = re.search(r'([0-9,]+)', price_el.text)
                if p_match:
                    try:
                        price = float(p_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            if not price:
                prices_in_text = re.findall(r'₹\s*([0-9,]+)', card.text)
                if prices_in_text:
                    try:
                        price = float(prices_in_text[0].replace(',', ''))
                    except ValueError:
                        pass

            if not price or price <= 0:
                continue

            mrp = round(price * 1.25, 2)
            img_el = card.select_one('img.product-img, img[src*="croma"], img')
            img_url = img_el.get('src') if img_el else None

            results.append({
                "store": "Croma",
                "title": title,
                "price": price,
                "mrp": mrp,
                "direct_url": direct_url,
                "image_url": img_url,
                "rating": 4.5,
                "seller": "Croma Official Verified Retailer"
            })
        except Exception:
            continue

    return results


async def search_single_store(store_name: str, query: str) -> List[Dict[str, Any]]:
    """Query an Indian store with real browser rendering and parse top results."""
    clean_q = quote_plus(query.strip())
    store_lower = store_name.lower()

    try:
        if "amazon" in store_lower:
            url = f"https://www.amazon.in/s?k={clean_q}"
            html = await fetch_page_html(url, wait_selector='div[data-component-type="s-search-result"]')
            return parse_amazon_search(html)

        elif "flipkart" in store_lower:
            url = f"https://www.flipkart.com/search?q={clean_q}"
            html = await fetch_page_html(url, wait_selector='div._75nlfW, div[data-id]')
            return parse_flipkart_search(html)

        elif "croma" in store_lower:
            url = f"https://www.croma.com/searchB?q={clean_q}%3Arelevance&text={clean_q}"
            html = await fetch_page_html(url, wait_selector='li.product-item')
            return parse_croma_search(html)

    except Exception as e:
        logger.warning(f"Error scraping {store_name} for '{query}': {e}")

    return []


async def verify_exact_match_with_gemini(target_title: str, target_brand: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Use Gemini Flash to verify if any candidate matches the target model, storage/size, and specs exactly."""
    if not candidates:
        return None

    if not settings.GEMINI_API_KEY:
        # Fallback simple title token match if no Gemini key
        target_tokens = set(re.findall(r'[a-zA-Z0-9]+', f"{target_brand} {target_title}".lower()))
        for cand in candidates:
            cand_tokens = set(re.findall(r'[a-zA-Z0-9]+', cand["title"].lower()))
            if target_tokens.issubset(cand_tokens) or (len(target_tokens.intersection(cand_tokens)) / len(target_tokens) >= 0.8):
                return cand
        return None

    try:
        import google.generativeai as genai
        import json

        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        model = genai.GenerativeModel("gemini-flash-latest")

        candidates_formatted = "\n".join([
            f"Candidate [{i}]: Title: {c['title']} | Price: ₹{c['price']} | URL: {c['direct_url']}"
            for i, c in enumerate(candidates)
        ])

        prompt = f"""You are an expert e-commerce SKU matching engine.
Target Product:
- Brand: {target_brand}
- Title: {target_title}

Candidate Listings found on store:
{candidates_formatted}

Task:
Determine if ANY candidate is an EXACT MATCH for the target product.
- Must match the exact model, generation, and primary variant (e.g. storage size, capacity).
- Reject accessories, cases, covers, chargers, or different generations (e.g. iPhone 15 vs iPhone 16).
- Return JSON:
{{
  "match_found": true,
  "matched_index": 0,
  "confidence": 98,
  "reason": "Exact matching SKU found"
}}
If no candidate is an exact match:
{{
  "match_found": false,
  "matched_index": -1,
  "confidence": 0,
  "reason": "No exact matching product found"
}}
"""
        resp = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={"response_mime_type": "application/json"},
            request_options={"timeout": 5.0, "retry": None}
        )
        data = json.loads(resp.text)
        if data.get("match_found") is True and data.get("matched_index") is not None:
            idx = int(data["matched_index"])
            if 0 <= idx < len(candidates):
                matched = candidates[idx]
                logger.info(f"✓ Gemini verified exact match for '{target_title}' on {matched['store']}: {matched['title']}")
                return matched

    except Exception as e:
        logger.warning(f"Gemini candidate match verification error: {e}")
        # Deterministic title token fallback
        target_tokens = set(re.findall(r'[a-zA-Z0-9]+', f"{target_brand} {target_title}".lower()))
        for cand in candidates:
            cand_tokens = set(re.findall(r'[a-zA-Z0-9]+', cand["title"].lower()))
            overlap = len(target_tokens.intersection(cand_tokens)) / max(1, len(target_tokens))
            if overlap >= 0.8:
                return cand

    return None


async def live_scrape_store_competitors(brand: str, product_title: str, category: str, exclude_store: Optional[str] = None) -> List[Dict[str, Any]]:
    """Concurrently search and scrape 5-6 target stores for an exact matching SKU."""
    stores_to_check = CATEGORY_STORES.get(category, CATEGORY_STORES["General"])
    if exclude_store:
        stores_to_check = [s for s in stores_to_check if s.lower() != exclude_store.lower()]

    search_query = f"{brand} {product_title}".strip()
    logger.info(f"Starting live multi-store scraping for: '{search_query}' across {stores_to_check}")

    tasks = [
        search_single_store(store_name, search_query)
        for store_name in stores_to_check
    ]
    all_store_candidates = await asyncio.gather(*tasks, return_exceptions=True)

    verified_offers = []
    for store_name, candidates in zip(stores_to_check, all_store_candidates):
        if isinstance(candidates, Exception) or not candidates:
            continue
        
        # Verify exact match using LLM
        matched_candidate = await verify_exact_match_with_gemini(product_title, brand, candidates)
        if matched_candidate:
            verified_offers.append(matched_candidate)

    return verified_offers
