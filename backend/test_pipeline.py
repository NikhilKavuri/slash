import asyncio
import json
from app.services.ai_extractor import normalize_product_with_gemini
from app.services.store_search import fetch_store_offers
from app.services.review_summarizer import generate_review_summary

async def test_sample_products():
    print("=" * 60)
    print("Testing PriceLens Product Ingestion & Comparison Engine")
    print("=" * 60)

    test_samples = [
        "https://www.tirabeauty.com/product/minimalist-10-niacinamide-face-serum-for-blemishes-oil-control-with-zinc-30ml-123456",
        "https://www.nykaa.com/maybelline-new-york-lash-sensational-sky-high-mascara/p/568856",
        "Laneige Lip Sleeping Mask Berry 20g"
    ]

    for item in test_samples:
        print(f"\n[INPUT]: {item}")
        
        # 1. AI Extraction & Normalization
        product = await normalize_product_with_gemini(item)
        print(f"  [AI Extracted] -> Brand: {product.brand} | Name: {product.product_name} | Variant: {product.variant}")
        print(f"  [Optimized Query]: {product.search_query}")
        
        # 2. Store Pricing & Delivery Speed
        offers = await fetch_store_offers(product)
        print("  [Store Prices]:")
        for o in offers:
            badge = " [BEST PRICE]" if o.is_best_price else (" [10-MIN DELIVERY]" if o.is_fastest_delivery else "")
            coupon = f" (Coupon: {o.coupon_code})" if o.coupon_code else ""
            print(f"    - {o.store_name:<10}: ₹{int(o.price)} (MRP ₹{int(o.mrp)}, -{o.discount_percent}%){coupon} | {o.delivery_badge}{badge}")
        
        # 3. Review Consensus (ReviewLens)
        reviews = await generate_review_summary(product, offers)
        print(f"  [ReviewLens Verdict]: {reviews.verdict}")
        print(f"    * Pros: {', '.join(reviews.pros[:2])}")
        print(f"    * Cons: {', '.join(reviews.cons[:1])}")

    print("\n" + "=" * 60)
    print("Test Completed Successfully! All services are clean and modular.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sample_products())
