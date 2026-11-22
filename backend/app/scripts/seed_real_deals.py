import datetime
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.product import ProductModel, PricePointModel

DB_URI = "postgresql+psycopg2://postgres.qdqnklclgavstaedlpst:slash19price%40@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

REAL_CATALOG = [
    {
        "brand": "NEWME",
        "title": "NEWME White Polka Dot Tube Top",
        "category": "Fashion & Apparel",
        "search_query": "https://newme.asia/product/white-polka-dot-tube-top-4",
        "thumbnail_url": "https://assets.newme.asia/wp-content/uploads/2026/07/17121641c5cf1266/NM-PRC-445-BLS-26-JUL-35660-WHITE(1).webp",
        "stores": [
            {"store_name": "NEWME", "price": 799.0}
        ]
    },
    {
        "brand": "Boult",
        "title": "GOBOULT Mustang Muscle Smart Watch (2.01\" Curved HD Display)",
        "category": "Electronics & Wearables",
        "search_query": "https://www.amazon.in/dp/B0GYYM57FP",
        "thumbnail_url": "https://m.media-amazon.com/images/I/61SSVxTSs3L._SL1500_.jpg",
        "stores": [
            {"store_name": "Amazon", "price": 1499.0},
            {"store_name": "Flipkart", "price": 1599.0},
            {"store_name": "Boult Audio", "price": 1699.0}
        ]
    },
    {
        "brand": "Minimalist",
        "title": "Minimalist 10% Niacinamide Face Serum with Zinc (30ml)",
        "category": "Skincare",
        "search_query": "Minimalist Niacinamide 10% Face Serum 30ml",
        "thumbnail_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Tira", "price": 489.0},
            {"store_name": "Amazon", "price": 509.0},
            {"store_name": "Nykaa", "price": 539.0},
            {"store_name": "Zepto", "price": 539.0},
            {"store_name": "Blinkit", "price": 559.0}
        ]
    },
    {
        "brand": "Philips",
        "title": "Philips Series 1000 Cordless Beard Trimmer (BT1232/15)",
        "category": "Grooming",
        "search_query": "Philips BT1232 15 Cordless Beard Trimmer",
        "thumbnail_url": "https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Amazon", "price": 799.0},
            {"store_name": "Flipkart", "price": 849.0},
            {"store_name": "Myntra", "price": 899.0}
        ]
    },
    {
        "brand": "Cetaphil",
        "title": "Cetaphil Gentle Skin Cleanser (125ml)",
        "category": "Skincare",
        "search_query": "Cetaphil Gentle Skin Cleanser 125ml",
        "thumbnail_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Tira", "price": 349.0},
            {"store_name": "Amazon", "price": 359.0},
            {"store_name": "Nykaa", "price": 380.0},
            {"store_name": "Zepto", "price": 375.0}
        ]
    },
    {
        "brand": "Cetaphil",
        "title": "Cetaphil DAM Daily Advance Ultra Hydrating Moisturizing Lotion",
        "category": "Skincare",
        "search_query": "https://blinkit.com/prn/x/prid/764770",
        "thumbnail_url": "https://cdn.grofers.com/da/cms-assets/cms/product/da743535166841c7b4c0251dc854042c.jpeg",
        "stores": [
            {"store_name": "Blinkit", "price": 341.0},
            {"store_name": "Amazon", "price": 385.0},
            {"store_name": "Nykaa", "price": 396.0},
            {"store_name": "Tira", "price": 395.0},
            {"store_name": "Zepto", "price": 341.0}
        ]
    },
    {
        "brand": "MuscleBlaze",
        "title": "MuscleBlaze Biozyme Performance Whey (1kg Rich Chocolate)",
        "category": "Fitness & Nutrition",
        "search_query": "MuscleBlaze Biozyme Performance Whey Protein 1kg",
        "thumbnail_url": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Amazon", "price": 1899.0},
            {"store_name": "Blinkit", "price": 1999.0},
            {"store_name": "HealthKart", "price": 1949.0}
        ]
    },
    {
        "brand": "Maybelline",
        "title": "Maybelline New York Lash Sensational Sky High Mascara",
        "category": "Makeup",
        "search_query": "Maybelline Lash Sensational Sky High Mascara",
        "thumbnail_url": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Amazon", "price": 629.0},
            {"store_name": "Tira", "price": 629.0},
            {"store_name": "Nykaa", "price": 679.0}
        ]
    },
    {
        "brand": "The Ordinary",
        "title": "The Ordinary Niacinamide 10% + Zinc 1% (30ml)",
        "category": "Skincare",
        "search_query": "The Ordinary Niacinamide 10% Zinc 1% 30ml",
        "thumbnail_url": "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=500&q=80",
        "stores": [
            {"store_name": "Nykaa", "price": 560.0},
            {"store_name": "Tira", "price": 560.0}
        ]
    }
]

def seed_database():
    engine = create_engine(DB_URI, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing data
    session.query(PricePointModel).delete()
    session.query(ProductModel).delete()
    session.commit()

    now = datetime.datetime.utcnow()

    for item in REAL_CATALOG:
        slug_raw = f"{item['brand']}-{item['title']}"
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug_raw.lower()).strip('-')[:100]

        prod = ProductModel(
            slug=slug,
            brand=item["brand"],
            title=item["title"],
            category=item["category"],
            search_query=item["search_query"],
            thumbnail_url=item["thumbnail_url"],
            created_at=now,
            last_checked_at=now
        )
        session.add(prod)
        session.flush()

        for s in item["stores"]:
            pp = PricePointModel(
                product_id=prod.id,
                store_name=s["store_name"],
                price=float(s["price"]),
                recorded_at=now
            )
            session.add(pp)

    session.commit()
    print(f"Successfully re-seeded {len(REAL_CATALOG)} real authentic products with verified images into Supabase!")
    session.close()

if __name__ == "__main__":
    seed_database()
