export interface NormalizedProduct {
  brand: string;
  product_name: string;
  variant?: string;
  category: string;
  normalized_title: string;
  search_query: string;
  source_store?: string;
  thumbnail_url?: string;
  original_url?: string;
}

export interface StoreOffer {
  store_name: string;
  seller_name: string;
  authenticity_badge: string;
  price: number;
  mrp: number;
  discount_percent: number;
  in_stock: boolean;
  rating: number;
  review_count: number;
  store_url: string;
  affiliate_url: string;
  delivery_badge: string;
  delivery_type: "instant" | "standard";
  coupon_code?: string;
  coupon_desc?: string;
  coupon_discount?: number;
  final_price?: number;
  total_discount_percent?: number;
  is_best_price: boolean;
  is_fastest_delivery: boolean;
  savings_vs_mrp: number;
  is_scam_flagged?: boolean;
  scam_warning?: string;
  authenticity_score?: number;
  image_url?: string;
}

export interface StoreCustomerReview {
  store: string;
  buyer_name: string;
  verified_purchase: boolean;
  rating: number;
  headline: string;
  comment: string;
  verified_date: string;
  helpful_votes: number;
}

export interface ReviewLensSummary {
  overall_rating: number;
  total_reviews_count: number;
  verdict: string;
  pros: string[];
  cons: string[];
  skin_type_or_fit?: string;
  authenticity_confidence: string;
  seller_guarantee?: string;
  scam_filter_status?: string;
  customer_reviews?: StoreCustomerReview[];
}

export interface PriceHistoryPoint {
  date: string;
  price: number;
  store: string;
}

export interface CompareResult {
  product: NormalizedProduct;
  offers: StoreOffer[];
  best_offer?: StoreOffer | null;
  fastest_offer?: StoreOffer | null;
  review_lens?: ReviewLensSummary | null;
  price_history?: PriceHistoryPoint[];
  not_found?: boolean;
  message?: string;
  cached: boolean;
  processing_time_ms: number;
}

export interface TrendingItem {
  title: string;
  brand: string;
  category: string;
  culture_tag?: string;
  best_price: number;
  mrp: number;
  best_store: string;
  fastest_store: string;
  savings: number;
  discount_percent?: number;
  sample_query: string;
  image: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://slash-backend-jl9j.onrender.com/api/v1";

export async function compareProduct(queryOrUrl: string): Promise<CompareResult> {
  const res = await fetch(`${API_BASE}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_or_url: queryOrUrl }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to compare product prices");
  }

  return res.json();
}

export function compareProductStream(
  queryOrUrl: string,
  callbacks: {
    onStatus?: (status: { message: string; step?: string; store?: string }) => void;
    onProduct?: (product: NormalizedProduct) => void;
    onStoreOffer?: (offer: StoreOffer) => void;
    onComplete?: (data: { best_offer?: StoreOffer | null; fastest_offer?: StoreOffer | null; total_offers: number }) => void;
    onError?: (err: any) => void;
  }
): () => void {
  const url = `${API_BASE}/compare/stream?q=${encodeURIComponent(queryOrUrl)}`;
  const eventSource = new EventSource(url);

  eventSource.addEventListener("status", (e) => {
    try {
      if (callbacks.onStatus) callbacks.onStatus(JSON.parse(e.data));
    } catch {}
  });

  eventSource.addEventListener("product", (e) => {
    try {
      if (callbacks.onProduct) callbacks.onProduct(JSON.parse(e.data));
    } catch {}
  });

  eventSource.addEventListener("store_offer", (e) => {
    try {
      if (callbacks.onStoreOffer) callbacks.onStoreOffer(JSON.parse(e.data));
    } catch {}
  });

  eventSource.addEventListener("complete", (e) => {
    try {
      if (callbacks.onComplete) callbacks.onComplete(JSON.parse(e.data));
    } catch {}
    eventSource.close();
  });

  eventSource.addEventListener("not_found", (e) => {
    try {
      const data = JSON.parse(e.data);
      if (callbacks.onError) callbacks.onError(new Error(data.message || "Product not found"));
    } catch {}
    eventSource.close();
  });

  eventSource.onerror = (err) => {
    eventSource.close();
    if (callbacks.onError) callbacks.onError(err);
  };

  return () => {
    eventSource.close();
  };
}

export async function getTrendingProducts(): Promise<TrendingItem[]> {
  try {
    const res = await fetch(`${API_BASE}/trending`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}
