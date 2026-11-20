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
    offers: List[StoreOffer]
    best_offer: StoreOffer
    fastest_offer: Optional[StoreOffer] = None
    review_lens: ReviewLensSummary
    price_history: List[PriceHistoryPoint]
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
        db_product = db.query(ProductModel).filter(ProductModel.slug == slug).first()
        if not db_product:
            db_product = ProductModel(
                slug=slug,
                brand=brand,
                title=title,
                category=product_data.get("category", "Beauty"),
                search_query=clean_input,
                thumbnail_url=offers_data[0].get("store_url") if offers_data else None,
                created_at=now,
                last_checked_at=now
            )
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
        else:
            db_product.last_checked_at = now
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
    if not offers:
        raise HTTPException(status_code=404, detail="No store offers found for this product.")

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
    """Return viral products for 1-click test comparison on the home screen."""
    return [
        {
            "title": "Minimalist Niacinamide 10% Face Serum (30ml)",
            "brand": "Minimalist",
            "category": "Skincare",
            "best_price": 539,
            "mrp": 599,
            "best_store": "Tira",
            "fastest_store": "Zepto (10 mins)",
            "savings": 60,
            "sample_query": "Minimalist Niacinamide 10% Face Serum 30ml",
            "image": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop&q=60"
        },
        {
            "title": "Laneige Lip Sleeping Mask Berry (20g)",
            "brand": "Laneige",
            "category": "Skincare",
            "best_price": 510,
            "mrp": 600,
            "best_store": "Tira",
            "fastest_store": "Blinkit (12 mins)",
            "savings": 90,
            "sample_query": "Laneige Lip Sleeping Mask Berry 20g",
            "image": "https://images.unsplash.com/photo-1599305090598-fe179d501227?w=500&auto=format&fit=crop&q=60"
        },
        {
            "title": "Maybelline Lash Sensational Sky High Mascara",
            "brand": "Maybelline",
            "category": "Makeup",
            "best_price": 629,
            "mrp": 799,
            "best_store": "Amazon",
            "fastest_store": "Zepto (10 mins)",
            "savings": 170,
            "sample_query": "Maybelline New York Lash Sensational Sky High Mascara Waterproof",
            "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop&q=60"
        },
        {
            "title": "Cetaphil Gentle Skin Cleanser (125ml)",
            "brand": "Cetaphil",
            "category": "Skincare",
            "best_price": 369,
            "mrp": 425,
            "best_store": "Tira",
            "fastest_store": "Blinkit (12 mins)",
            "savings": 56,
            "sample_query": "Cetaphil Gentle Skin Cleanser Dry to Normal Sensitive Skin 125ml",
            "image": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop&q=60"
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
