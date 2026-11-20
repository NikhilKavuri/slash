import hashlib
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
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
    allow_origins=["*"],  # Allows all origins for easy development and deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Generate 30-day realistic price history points for the trend chart."""
    points = []
    days_ago = [30, 21, 14, 7, 3, 0]
    for d in days_ago:
        # Realistic slight fluctuations
        factor = 1.0 if d == 0 else (1.05 if d in [14, 21] else 0.98)
        p = round(best_price * factor)
        points.append(PriceHistoryPoint(
            date=f"{d}d ago" if d > 0 else "Today",
            price=float(min(p, mrp)),
            store="Tira" if p <= best_price else "Nykaa"
        ))
    return points

@app.get("/")
@app.get("/health")
@app.get("/v1/health")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "timestamp": time.time()
    }

@app.post("/compare", response_model=CompareResponse)
@app.post("/v1/compare", response_model=CompareResponse)
@app.post("/api/v1/compare", response_model=CompareResponse)
async def compare_product(req: CompareRequest):
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

    # 5. Price History Points
    price_history = generate_mock_price_history(best_offer.price, best_offer.mrp)

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
