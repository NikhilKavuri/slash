from urllib.parse import quote_plus, urlparse, urlencode, parse_qs, urlunparse
from typing import Optional
from app.core.config import settings

# Active high-converting store perks and verified coupons
STORE_PERKS = {
    "Tira": {
        "coupon_code": "TIRA20",
        "coupon_desc": "Flat 20% OFF on First Order (Min ₹999)",
        "delivery_badge": "Standard 2–3 Days Delivery",
        "delivery_type": "standard",
        "logo_color": "#D4426F" # Tira signature berry/pink
    },
    "Nykaa": {
        "coupon_code": "BEAUTY10",
        "coupon_desc": "Extra 10% OFF on ₹1299+",
        "delivery_badge": "Express 1–2 Days Delivery",
        "delivery_type": "standard",
        "logo_color": "#FC2779" # Nykaa signature hot pink
    },
    "Zepto": {
        "coupon_code": "ZEPTOFREE",
        "coupon_desc": "Free Delivery on orders above ₹199",
        "delivery_badge": "⚡ 10 Minutes Delivery",
        "delivery_type": "instant",
        "logo_color": "#800080" # Zepto purple
    },
    "Blinkit": {
        "coupon_code": None,
        "coupon_desc": "Best Price + Instant Delivery",
        "delivery_badge": "⚡ 12 Minutes Delivery",
        "delivery_type": "instant",
        "logo_color": "#F8CB46" # Blinkit yellow
    },
    "Amazon": {
        "coupon_code": "AMZPAY5",
        "coupon_desc": "5% Unlimited Cashback with Amazon Pay Card",
        "delivery_badge": "Prime Next-Day Delivery",
        "delivery_type": "standard",
        "logo_color": "#FF9900" # Amazon orange
    },
    "Purplle": {
        "coupon_code": "APPNEXT",
        "coupon_desc": "Flat ₹100 OFF on ₹699+",
        "delivery_badge": "Standard 3 Days Delivery",
        "delivery_type": "standard",
        "logo_color": "#7B1FA2" # Purplle violet
    },
    "NEWME": {
        "coupon_code": "NEWME15",
        "coupon_desc": "Extra 15% OFF on First App Order",
        "delivery_badge": "⚡ 2-Day Priority Shipping",
        "delivery_type": "standard",
        "logo_color": "#FF2A6D"
    },
    "Myntra": {
        "coupon_code": "MYNTRA200",
        "coupon_desc": "Flat ₹200 OFF on First Purchase",
        "delivery_badge": "M-Express Next-Day Delivery",
        "delivery_type": "standard",
        "logo_color": "#FF3E6C"
    },
    "Ajio": {
        "coupon_code": "TRENDS500",
        "coupon_desc": "Up to 50% OFF + Extra ₹500 OFF",
        "delivery_badge": "Ajio Express Delivery",
        "delivery_type": "standard",
        "logo_color": "#2C4152"
    },
    "Nykaa Fashion": {
        "coupon_code": "FIRSTFASHION",
        "coupon_desc": "10% OFF on ₹1500+",
        "delivery_badge": "Express 2-Day Delivery",
        "delivery_type": "standard",
        "logo_color": "#FC2779"
    },
    "Flipkart": {
        "coupon_code": "FKFIRST",
        "coupon_desc": "Extra ₹100 OFF with SuperCoins",
        "delivery_badge": "Flipkart Assured Delivery",
        "delivery_type": "standard",
        "logo_color": "#2874F0"
    },
    "Boult Audio": {
        "coupon_code": "BOULT10",
        "coupon_desc": "Extra 10% OFF on Official Store",
        "delivery_badge": "Official Direct Brand Shipping",
        "delivery_type": "standard",
        "logo_color": "#111827"
    },
    "HealthKart": {
        "coupon_code": "HKFIRST",
        "coupon_desc": "Flat 10% OFF + Authenticity Certificate",
        "delivery_badge": "Direct Brand Distributor",
        "delivery_type": "standard",
        "logo_color": "#00A699"
    },
    "Croma": {
        "coupon_code": "TATA200",
        "coupon_desc": "Instant ₹200 OFF on Electronic Drops",
        "delivery_badge": "Tata Express Store Delivery",
        "delivery_type": "standard",
        "logo_color": "#00E9BF"
    }
}

class AffiliateRouter:
    @staticmethod
    def wrap_affiliate_url(store_name: str, original_url: str) -> str:
        """Transform a standard store URL into an affiliate revenue-generating redirect URL."""
        if not original_url:
            return ""

        store_key = store_name.capitalize()
        
        # 1. Amazon.in Direct Associates Tag
        if "Amazon" in store_key or "amazon.in" in original_url:
            parsed = urlparse(original_url)
            query_params = parse_qs(parsed.query)
            query_params["tag"] = [settings.AMAZON_AFFILIATE_TAG]
            new_query = urlencode(query_params, doseq=True)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

        # 2. Cuelinks Universal Aggregator for Tira, Nykaa, Purplle, etc.
        if settings.CUELINKS_PUB_ID:
            encoded_target = quote_plus(original_url)
            return f"https://linksredirect.com/?cid={settings.CUELINKS_PUB_ID}&url={encoded_target}"

        # 3. Fallback tracking parameters
        parsed = urlparse(original_url)
        query_params = parse_qs(parsed.query)
        query_params["utm_source"] = ["slash"]
        query_params["utm_medium"] = ["price_comparison"]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    @staticmethod
    def get_store_perks(store_name: str) -> dict:
        """Get active coupon and delivery perks for the store."""
        for key in STORE_PERKS:
            if key.lower() in store_name.lower():
                return STORE_PERKS[key]
        return {
            "coupon_code": None,
            "coupon_desc": "Verified Genuine Product",
            "delivery_badge": "Standard Delivery",
            "delivery_type": "standard",
            "logo_color": "#2563EB"
        }

affiliate_router = AffiliateRouter()
