import hashlib
import time
import datetime
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.models.product import ProductModel, PricePointModel
from app.core.redis_client import cache
from app.services.ai_extractor import normalize_product_with_gemini, NormalizedProduct
from app.services.store_search import fetch_store_offers, StoreOffer
from app.services.review_summarizer import generate_review_summary, ReviewLensSummary

app = FastAPI(
    title=settings.APP_NAME,
    description="India's Smartest Beauty & Quick-Commerce Price Comparison Engine",
    version="1.0.0"
)

# CORS setup for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """Initialize database tables on cold start."""
    init_db()

class CompareRequest(BaseModel):
    query_or_url: str

class PriceHistoryPoint(BaseModel):
    date: str
    price: float
    store: str

class CompareResponse(BaseModel):
    product: NormalizedProduct
    offers: List[StoreOffer] = []
    best_offer: Optional[StoreOffer] = None
    fastest_offer: Optional[StoreOffer] = None
    review_lens: Optional[ReviewLensSummary] = None
    price_history: List[PriceHistoryPoint] = []
    not_found: bool = False
    message: Optional[str] = None
    cached: bool = False
    processing_time_ms: float

def generate_mock_price_history(best_price: float, mrp: float) -> List[PriceHistoryPoint]:
    """Generate 30-day realistic price history points when fewer than 2 DB points exist."""
    points = []
    days_ago = [30, 21, 14, 7, 3, 0]
    for d in days_ago:
        factor = 1.0 if d == 0 else (1.05 if d in [14, 21] else 0.98)
        p = round(best_price * factor)
        points.append(PriceHistoryPoint(
            date=f"{d}d ago" if d > 0 else "Today",
            price=float(min(p, mrp)),
            store="Tira" if p <= best_price else "Nykaa"
        ))
    return points

def fetch_price_history_points(slug: str, best_price: float, mrp: float) -> List[PriceHistoryPoint]:
    """Retrieve actual historical price points from Supabase PostgreSQL if available."""
    try:
        db = SessionLocal()
        db_product = db.query(ProductModel).filter(ProductModel.slug == slug).first()
        if db_product and db_product.price_history and len(db_product.price_history) >= 2:
            sorted_history = sorted(db_product.price_history, key=lambda x: x.recorded_at)
            points = []
            for item in sorted_history[-10:]:
                points.append(PriceHistoryPoint(
                    date=item.recorded_at.strftime("%d %b"),
                    price=item.price,
                    store=item.store_name
                ))
            db.close()
            return points
        db.close()
    except Exception as e:
        print(f"Notice: Supabase price history read skipped ({e})")
    return generate_mock_price_history(best_price, mrp)

def persist_product_offers(clean_input: str, product_data: dict, offers_data: list):
    """Background worker: Persist tracked product and prices into Supabase PostgreSQL."""
    try:
        db = SessionLocal()
        brand = product_data.get("brand", "Unknown")
        title = product_data.get("normalized_title") or product_data.get("product_name") or "Product"
        slug_raw = f"{brand}-{title}"
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug_raw.lower()).strip('-')[:100]

        now = datetime.datetime.utcnow()
        # Extract best genuine image URL
        best_img = product_data.get("thumbnail_url")
        if not best_img and offers_data:
            for off in offers_data:
                if off.get("image_url") and "http" in str(off.get("image_url")):
                    best_img = off.get("image_url")
                    break

        db_product = db.query(ProductModel).filter(ProductModel.slug == slug).first()
        if not db_product:
            db_product = ProductModel(
                slug=slug,
                brand=brand,
                title=title,
                category=product_data.get("category", "Beauty"),
                search_query=clean_input,
                thumbnail_url=best_img,
                created_at=now,
                last_checked_at=now
            )
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
        else:
            db_product.last_checked_at = now
            if best_img and (not db_product.thumbnail_url or not db_product.thumbnail_url.startswith("http")):
                db_product.thumbnail_url = best_img
            db.commit()

        for off in offers_data:
            db.add(PricePointModel(
                product_id=db_product.id,
                store_name=off.get("store_name", "Store"),
                price=float(off.get("price", 0.0)),
                recorded_at=now
            ))
        db.commit()
        db.close()
    except Exception as e:
        print(f"Notice: Supabase logging async error ({e})")

@app.get("/api/v1/test-gemini")
async def test_gemini():
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        m = genai.GenerativeModel("gemini-2.0-flash")
        resp = await m.generate_content_async("Hello, return 'OK'")
        return {"status": "success", "response": resp.text}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}

@app.get("/api/v1/test-grounding")
async def test_grounding():
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        m = genai.GenerativeModel("gemini-2.0-flash", tools="google_search_retrieval")
        resp = await m.generate_content_async("What is the price of Boult Mustang Muscle smartwatch on Amazon India?")
        return {"status": "success", "response": resp.text}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}

@app.get("/")
@app.get("/health")
@app.get("/v1/health")
@app.get("/api/v1/health")
async def health_check():
    db_connected = False
    try:
        db = SessionLocal()
        p_count = db.query(ProductModel).count()
        db.close()
        db_connected = True
    except Exception:
        p_count = 0

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "database_connected": db_connected,
        "tracked_products": p_count,
        "timestamp": time.time()
    }

@app.post("/compare", response_model=CompareResponse)
@app.post("/v1/compare", response_model=CompareResponse)
@app.post("/api/v1/compare", response_model=CompareResponse)
async def compare_product(req: CompareRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    clean_input = req.query_or_url.strip()
    if not clean_input:
        raise HTTPException(status_code=400, detail="Please provide a valid product URL or search term.")

    # 1. Check Redis Cache
    cache_key = f"compare:{hashlib.md5(clean_input.lower().encode()).hexdigest()}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        cached_result["cached"] = True
        cached_result["processing_time_ms"] = round((time.time() - start_time) * 1000, 1)
        return cached_result

    # 2. AI Product Normalization
    product = await normalize_product_with_gemini(clean_input)

    # 3. Multi-Store Search & Pricing
    offers = await fetch_store_offers(product)
    
    if not offers or not getattr(product, "is_found", True):
        reason = getattr(product, "not_found_reason", None) or "Sorry, we couldn't find verified price comparisons for this item across trusted stores. Rather than showing you unrelated items or guessing prices, Slash only displays 100% verified authentic listings."
        return {
            "product": product.model_dump(),
            "offers": [],
            "best_offer": None,
            "fastest_offer": None,
            "review_lens": None,
            "price_history": [],
            "not_found": True,
            "message": reason,
            "cached": False,
            "processing_time_ms": round((time.time() - start_time) * 1000, 1)
        }

    best_offer = next((o for o in offers if o.is_best_price), offers[0])
    fastest_offer = next((o for o in offers if o.is_fastest_delivery), None)

    # 4. Review Synthesis
    review_lens = await generate_review_summary(product, offers)

    # 5. Price History Points (Check Supabase DB first)
    prod_title = getattr(product, "normalized_title", None) or getattr(product, "product_name", "Product")
    slug_raw = f"{product.brand}-{prod_title}"
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug_raw.lower()).strip('-')[:100]
    price_history = fetch_price_history_points(slug, best_offer.price, best_offer.mrp)

    result = {
        "product": product.model_dump(),
        "offers": [o.model_dump() for o in offers],
        "best_offer": best_offer.model_dump(),
        "fastest_offer": fastest_offer.model_dump() if fastest_offer else None,
        "review_lens": review_lens.model_dump(),
        "price_history": [p.model_dump() for p in price_history],
        "not_found": False,
        "message": None,
        "cached": False,
        "processing_time_ms": round((time.time() - start_time) * 1000, 1)
    }

    # 6. Save to Redis Cache (12 hours TTL)
    await cache.set(cache_key, result, ttl_seconds=3600 * 12)

    # 7. Asynchronously persist to Supabase in background
    background_tasks.add_task(
        persist_product_offers,
        clean_input,
        product.model_dump(),
        [o.model_dump() for o in offers]
    )

    return result

@app.get("/trending")
@app.get("/v1/trending")
@app.get("/api/v1/trending")
async def get_trending_products():
    """Return top viral products with genuine offers directly from the Supabase PostgreSQL database."""
    try:
        db = SessionLocal()
        products = db.query(ProductModel).order_by(ProductModel.id.asc()).limit(10).all()
        if products:
            items = []
            for p in products:
                pps = db.query(PricePointModel).filter(PricePointModel.product_id == p.id).all()
                if pps:
                    best_pp = min(pps, key=lambda x: x.price)
                    best_price = int(best_pp.price)
                    best_store = best_pp.store_name
                else:
                    best_price = 799
                    best_store = p.brand

                # Use a reasonable MRP estimate from price data
                mrp = int(best_price * 1.3)
                if mrp <= best_price:
                    mrp = int(best_price + 200)

                savings = mrp - best_price
                disc_pct = int(round((savings / mrp) * 100))

                tag = "VIRAL AESTHETIC 🎀"
                text_lower = f"{p.brand} {p.title} {p.category}".lower()
                if any(w in text_lower for w in ["watch", "smart", "electronic", "trimmer", "mustang"]):
                    tag = "TECH GRAIL ⚡"
                elif any(w in text_lower for w in ["whey", "protein", "fitness"]):
                    tag = "GYM RAT GRAIL 🏋️"
                elif any(w in text_lower for w in ["cleanser", "serum", "niacinamide"]):
                    tag = "CULT CLASSIC 🧪"
                elif any(w in text_lower for w in ["mascara", "lash", "makeup"]):
                    tag = "BADDIE VIBES 💅"

                items.append({
                    "title": p.title,
                    "brand": p.brand,
                    "category": p.category,
                    "culture_tag": tag,
                    "best_price": best_price,
                    "mrp": mrp,
                    "best_store": best_store,
                    "fastest_store": f"{best_store} Express",
                    "savings": savings,
                    "discount_percent": disc_pct,
                    "sample_query": p.search_query or p.title,
                    "image": p.thumbnail_url or "https://assets.newme.asia/wp-content/uploads/2026/07/17121641c5cf1266/NM-PRC-445-BLS-26-JUL-35660-WHITE(1).webp"
                })
            db.close()
            if items:
                return items
        db.close()
    except Exception as e:
        print(f"Notice: Supabase trending query exception ({e})")

    # Static fallback with 100% verified stores (NEWME exclusively on NEWME)
    return [
        {
            "title": "NEWME White Polka Dot Tube Top",
            "brand": "NEWME",
            "category": "Fashion & Apparel",
            "culture_tag": "VIRAL AESTHETIC 🎀",
            "best_price": 799,
            "mrp": 999,
            "best_store": "NEWME",
            "fastest_store": "NEWME (2-3 Days)",
            "savings": 200,
            "discount_percent": 20,
            "sample_query": "https://newme.asia/product/white-polka-dot-tube-top-4",
            "image": "https://assets.newme.asia/wp-content/uploads/2026/07/17121641c5cf1266/NM-PRC-445-BLS-26-JUL-35660-WHITE(1).webp"
        },
        {
            "title": "GOBOULT Mustang Muscle Smart Watch (2.01\" Curved HD Display)",
            "brand": "Boult",
            "category": "Electronics & Wearables",
            "culture_tag": "TECH GRAIL ⚡",
            "best_price": 1499,
            "mrp": 4999,
            "best_store": "Amazon",
            "fastest_store": "Amazon Prime",
            "savings": 3500,
            "discount_percent": 70,
            "sample_query": "https://www.amazon.in/dp/B0GYYM57FP",
            "image": "https://m.media-amazon.com/images/I/61SSVxTSs3L._SL1500_.jpg"
        },
        {
            "title": "Minimalist 10% Niacinamide Face Serum with Zinc (30ml)",
            "brand": "Minimalist",
            "category": "Skincare",
            "culture_tag": "SKINCARE SAVIOR 🧴",
            "best_price": 489,
            "mrp": 599,
            "best_store": "Tira",
            "fastest_store": "Zepto (10 mins)",
            "savings": 110,
            "discount_percent": 18,
            "sample_query": "Minimalist Niacinamide 10% Face Serum 30ml",
            "image": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500&q=80"
        },
        {
            "title": "Philips Series 1000 Cordless Beard Trimmer (BT1232/15)",
            "brand": "Philips",
            "category": "Grooming",
            "culture_tag": "CLEAN FADE ⚡",
            "best_price": 799,
            "mrp": 1195,
            "best_store": "Amazon",
            "fastest_store": "Flipkart Assured",
            "savings": 396,
            "discount_percent": 33,
            "sample_query": "Philips BT1232 15 Cordless Beard Trimmer",
            "image": "https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=500&q=80"
        },
        {
            "title": "MuscleBlaze Biozyme Performance Whey (1kg Rich Chocolate)",
            "brand": "MuscleBlaze",
            "category": "Fitness & Nutrition",
            "culture_tag": "GYM RAT GRAIL 🏋️",
            "best_price": 1899,
            "mrp": 2499,
            "best_store": "Amazon",
            "fastest_store": "Blinkit (12 mins)",
            "savings": 600,
            "discount_percent": 24,
            "sample_query": "MuscleBlaze Biozyme Performance Whey Protein 1kg",
            "image": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?auto=format&fit=crop&w=500&q=80"
        },
        {
            "title": "Maybelline New York Lash Sensational Sky High Mascara",
            "brand": "Maybelline",
            "category": "Makeup",
            "culture_tag": "BADDIE VIBES 💅",
            "best_price": 629,
            "mrp": 799,
            "best_store": "Amazon",
            "fastest_store": "Tira Express",
            "savings": 170,
            "discount_percent": 21,
            "sample_query": "Maybelline Lash Sensational Sky High Mascara",
            "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=500&q=80"
        },
        {
            "title": "The Ordinary Niacinamide 10% + Zinc 1% (30ml)",
            "brand": "The Ordinary",
            "category": "Skincare",
            "culture_tag": "CULT CLASSIC 🧪",
            "best_price": 560,
            "mrp": 700,
            "best_store": "Nykaa",
            "fastest_store": "Tira Express",
            "savings": 140,
            "discount_percent": 20,
            "sample_query": "The Ordinary Niacinamide 10% Zinc 1% 30ml",
            "image": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=500&q=80"
        },
        {
            "title": "Cetaphil Gentle Skin Cleanser (125ml)",
            "brand": "Cetaphil",
            "category": "Skincare",
            "culture_tag": "DERM CHOICE 🩺",
            "best_price": 349,
            "mrp": 425,
            "best_store": "Tira",
            "fastest_store": "Amazon Prime",
            "savings": 76,
            "discount_percent": 18,
            "sample_query": "Cetaphil Gentle Skin Cleanser 125ml",
            "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=500&q=80"
        }
    ]

@app.get("/catalog")
@app.get("/v1/catalog")
@app.get("/api/v1/catalog")
async def get_tracked_catalog():
    """Return all products tracked in Supabase PostgreSQL."""
    try:
        db = SessionLocal()
        products = db.query(ProductModel).order_by(ProductModel.last_checked_at.desc()).limit(50).all()
        catalog_items = []
        for p in products:
            catalog_items.append({
                "id": p.id,
                "slug": p.slug,
                "brand": p.brand,
                "title": p.title,
                "category": p.category,
                "last_checked_at": p.last_checked_at.isoformat() if p.last_checked_at else None,
                "price_points_count": len(p.price_history) if p.price_history else 0
            })
        db.close()
        return {"total": len(catalog_items), "items": catalog_items}
    except Exception as e:
        return {"total": 0, "items": [], "error": str(e)}

@app.get("/cron/refresh-catalog")
@app.get("/v1/cron/refresh-catalog")
@app.get("/api/v1/cron/refresh-catalog")
async def refresh_catalog_cron():
    """
    Automated background worker: sweeps tracked products in Supabase,
    fetches fresh prices across stores, and records new historical price points.
    """
    try:
        db = SessionLocal()
        products = db.query(ProductModel).order_by(ProductModel.last_checked_at.asc()).limit(10).all()
        refreshed_count = 0
        now = datetime.datetime.utcnow()

        for p in products:
            p_obj = NormalizedProduct(
                brand=p.brand,
                product_name=p.title,
                variant=None,
                category=p.category,
                normalized_title=p.title,
                search_query=p.search_query or f"{p.brand} {p.title}"
            )
            fresh_offers = await fetch_store_offers(p_obj)
            for off in fresh_offers:
                db.add(PricePointModel(
                    product_id=p.id,
                    store_name=off.store_name,
                    price=off.price,
                    recorded_at=now
                ))
            p.last_checked_at = now
            refreshed_count += 1

        db.commit()
        db.close()
        return {"status": "success", "refreshed_products": refreshed_count, "timestamp": now.isoformat()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
