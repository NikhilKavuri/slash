"use client";

import { useState, useEffect } from "react";
import { compareProduct, CompareResult, getTrendingProducts, TrendingItem } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { SearchBar } from "@/components/SearchBar";
import { PriceTable } from "@/components/PriceTable";
import { ReviewLens } from "@/components/ReviewLens";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { SlashLogo } from "@/components/SlashLogo";
import { ScannerLoader } from "@/components/ScannerLoader";
import { ImageWithFallback } from "@/components/ImageWithFallback";
import { Marquee } from "@/components/magicui/marquee";
import { AnimatedList } from "@/components/magicui/animated-list";
import { useSnackbar } from "@/components/Snackbar";
import confetti from "canvas-confetti";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  ShieldCheck,
  Share2,
  RotateCcw,
  Tag,
  Flame,
  LayoutGrid,
  ListFilter,
  ArrowRight,
  TrendingUp,
  Zap,
} from "lucide-react";

const UNISEX_TRENDING_ITEMS: TrendingItem[] = [
  {
    title: "NEWME White Polka Dot Tube Top",
    brand: "NEWME",
    category: "Fashion & Apparel",
    culture_tag: "VIRAL AESTHETIC 🎀",
    best_price: 799,
    mrp: 999,
    best_store: "NEWME",
    fastest_store: "NEWME Direct",
    savings: 200,
    sample_query: "https://newme.asia/product/white-polka-dot-tube-top-4",
    image: "https://assets.newme.asia/wp-content/uploads/2026/07/17121641c5cf1266/NM-PRC-445-BLS-26-JUL-35660-WHITE(1).webp",
  },
  {
    title: "GOBOULT Mustang Muscle Smart Watch (2.01\" Curved HD Display)",
    brand: "Boult",
    category: "Electronics & Wearables",
    culture_tag: "TECH GRAIL ⚡",
    best_price: 1499,
    mrp: 4999,
    best_store: "Amazon",
    fastest_store: "Amazon Prime",
    savings: 3500,
    sample_query: "https://www.amazon.in/dp/B0GYYM57FP",
    image: "https://m.media-amazon.com/images/I/61SSVxTSs3L._SL1500_.jpg",
  },
  {
    title: "Minimalist 10% Niacinamide Face Serum with Zinc (30ml)",
    brand: "Minimalist",
    category: "Skincare",
    culture_tag: "SKINCARE SAVIOR 🧴",
    best_price: 489,
    mrp: 599,
    best_store: "Tira",
    fastest_store: "Zepto (10 mins)",
    savings: 110,
    sample_query: "Minimalist Niacinamide 10% Face Serum 30ml",
    image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=500&q=80",
  },
  {
    title: "Philips Series 1000 Cordless Beard Trimmer (BT1232/15)",
    brand: "Philips",
    category: "Grooming",
    culture_tag: "CLEAN FADE ⚡",
    best_price: 799,
    mrp: 1195,
    best_store: "Amazon",
    fastest_store: "Flipkart Assured",
    savings: 396,
    sample_query: "Philips BT1232 15 Cordless Beard Trimmer",
    image: "https://images.unsplash.com/photo-1621607512214-68297480165e?auto=format&fit=crop&w=500&q=80",
  },
  {
    title: "MuscleBlaze Biozyme Performance Whey (1kg Rich Chocolate)",
    brand: "MuscleBlaze",
    category: "Fitness & Nutrition",
    culture_tag: "GYM RAT GRAIL 🏋️",
    best_price: 1899,
    mrp: 2499,
    best_store: "Amazon",
    fastest_store: "Blinkit (12 mins)",
    savings: 600,
    sample_query: "MuscleBlaze Biozyme Performance Whey Protein 1kg",
    image: "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?auto=format&fit=crop&w=500&q=80",
  },
  {
    title: "Maybelline New York Lash Sensational Sky High Mascara",
    brand: "Maybelline",
    category: "Makeup",
    culture_tag: "BADDIE VIBES 💅",
    best_price: 629,
    mrp: 799,
    best_store: "Amazon",
    fastest_store: "Tira Express",
    savings: 170,
    sample_query: "Maybelline Lash Sensational Sky High Mascara",
    image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=500&q=80",
  },
  {
    title: "The Ordinary Niacinamide 10% + Zinc 1% (30ml)",
    brand: "The Ordinary",
    category: "Skincare",
    culture_tag: "CULT CLASSIC 🧪",
    best_price: 560,
    mrp: 700,
    best_store: "Nykaa",
    fastest_store: "Tira Express",
    savings: 140,
    sample_query: "The Ordinary Niacinamide 10% Zinc 1% 30ml",
    image: "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=500&q=80",
  },
  {
    title: "Cetaphil Gentle Skin Cleanser (125ml)",
    brand: "Cetaphil",
    category: "Skincare",
    culture_tag: "DERM CHOICE 🩺",
    best_price: 349,
    mrp: 425,
    best_store: "Tira",
    fastest_store: "Amazon Prime",
    savings: 76,
    sample_query: "Cetaphil Gentle Skin Cleanser 125ml",
    image: "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=500&q=80",
  },
];

export default function HomePage() {
  const [result, setResult] = useState<CompareResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [trendingViewMode, setTrendingViewMode] = useState<"columns" | "list">("columns");
  const [trendingItems, setTrendingItems] = useState<TrendingItem[]>(UNISEX_TRENDING_ITEMS);

  useEffect(() => {
    getTrendingProducts().then((items) => {
      if (items && items.length > 0) {
        setTrendingItems(items);
      }
    });
  }, []);

  const { showSuccessToast, showErrorToast } = useSnackbar();

  const handleSearch = async (query: string) => {
    setCurrentQuery(query);
    setIsLoading(true);

    try {
      const data = await compareProduct(query);
      setResult(data);

      if (data.not_found || !data.offers || data.offers.length === 0) {
        showErrorToast(
          "No verified matches found",
          data.message || "We only show exact verified deals and never guess or display unrelated items."
        );
      } else if (data.best_offer) {
        // Trigger celebratory confetti
        confetti({
          particleCount: 75,
          spread: 65,
          origin: { y: 0.65 },
          colors: ["#10b981", "#09090b", "#00ff66", "#f59e0b"],
        });

        showSuccessToast(
          "Price Slashed! 🎯",
          `Bagged ${formatINR(data.best_offer.price)} on ${data.best_offer.store_name} (Saved ${formatINR(data.best_offer.savings_vs_mrp)})`
        );
      }
    } catch (err: any) {
      showErrorToast(
        "Could not find deals",
        err.message || "Please check your search term or try another product."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleShareWhatsApp = () => {
    if (!result || !result.best_offer) return;
    const text = `Yo! Slashed ${result.product.normalized_title} down to ${formatINR(
      result.best_offer.price
    )} on ${result.best_offer.store_name} (Saved ${formatINR(
      result.best_offer.savings_vs_mrp
    )})! Check it before prices go back up: ${window.location.href}`;
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, "_blank");
    showSuccessToast("Deal Shared! 🚀", "WhatsApp link opened with the lowest price!");
  };

  const stores = [
    { name: "Amazon", perk: "Prime Next-Day" },
    { name: "Tira Beauty", perk: "Secret 20% Codes" },
    { name: "Nykaa", perk: "Official Brand Mall" },
    { name: "NEWME", perk: "Viral Y2K Drip" },
    { name: "Myntra", perk: "100% Original Mall" },
    { name: "Zepto", perk: "10-Min Drops" },
    { name: "Ajio", perk: "Reliance Trends" },
    { name: "Blinkit", perk: "Instant Essentials" },
  ];

  return (
    <div className="min-h-screen bg-[#FAFAFA] bg-[radial-gradient(#e4e4e7_1px,transparent_1px)] [background-size:24px_24px] text-zinc-900 selection:bg-emerald-500 selection:text-white">
      {/* Multi-Store Laser Scanner Loader with Mobile List View */}
      <AnimatePresence>
        {isLoading && <ScannerLoader query={currentQuery} />}
      </AnimatePresence>

      {/* 1. Header with Slashed Rupee Logo */}
      <header className="sticky top-0 z-40 bg-[#FAFAFA]/95 backdrop-blur-md border-b border-zinc-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <motion.div
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex items-center gap-2.5 cursor-pointer"
            onClick={() => setResult(null)}
          >
            <SlashLogo className="w-8 h-8 sm:w-9 sm:h-9" />
            <div className="flex items-baseline">
              <span className="font-black text-2xl tracking-tight text-zinc-950">Slash</span>
              <span className="font-cursive text-emerald-500 font-bold text-2xl ml-0.5">/</span>
            </div>
          </motion.div>

          <div className="flex items-center gap-2.5">
            {result && (
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleShareWhatsApp}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-zinc-950 text-white hover:bg-zinc-800 text-xs font-black transition-colors shadow-xs"
              >
                <Share2 className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Flex Deal</span>
              </motion.button>
            )}
            <div className="hidden sm:flex items-center gap-2 text-xs font-bold text-zinc-700 bg-white px-3 py-1.5 rounded-xl border border-zinc-200 shadow-xs">
              <span className="text-emerald-500">🛡️</span>
              <span>100% Legit Stores Only</span>
            </div>
          </div>
        </div>
      </header>

      {/* 2. Hero Section (Full on home, Slim when result is active) */}
      {!result ? (
        <section className="pt-8 sm:pt-14 pb-4 px-4 sm:px-6">
          <div className="max-w-3xl mx-auto text-center space-y-3.5">
            {/* Gen-Z Pill Badge */}
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-black bg-zinc-950 text-white border border-zinc-800 shadow-xs"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Retail is a scam</span>
              <span className="font-cursive text-emerald-400 font-bold text-base">~ zero cap</span>
            </motion.div>

            {/* Gen-Z Punchy Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08 }}
              className="text-3xl sm:text-6xl font-black tracking-tight text-zinc-950 leading-tight"
            >
              Stop paying full price.{" "}
              <span className="font-cursive text-emerald-600 text-4xl sm:text-6xl font-bold inline-block px-1 -rotate-1">
                literally, why would you?
              </span>
            </motion.h1>

            <p className="text-sm sm:text-base text-zinc-600 max-w-xl mx-auto font-medium leading-relaxed">
              Drop any product link or search term. Slash hunts Amazon, Nykaa, Tira, Blinkit & Zepto, sniffs out secret checkout codes, and bags you the absolute lowest price in seconds.
            </p>

            <div className="pt-2">
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </div>

            {/* Real-Time Gen-Z Flex Counter */}
            <div className="pt-2 flex items-center justify-center gap-2 text-xs font-bold text-zinc-500">
              <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200/80 px-2.5 py-0.5 rounded-full font-black">
                <Flame className="w-3.5 h-3.5 text-emerald-600 fill-emerald-600" />
                <span>₹14,82,490+</span>
              </span>
              <span>saved by smart shoppers this week</span>
            </div>
          </div>
        </section>
      ) : (
        /* Slim search strip when result is active so content is immediately visible */
        <section className="py-3 px-4 sm:px-6 border-b border-zinc-200/70 bg-white/70">
          <div className="max-w-2xl mx-auto">
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
          </div>
        </section>
      )}

      {/* 3. Infinite Store Marquee (Home Screen only) */}
      {!result && (
        <section className="py-2.5 border-y border-zinc-200/80 bg-white/90 overflow-hidden my-4">
          <Marquee pauseOnHover className="[--duration:26s]">
            {stores.map((s) => (
              <div
                key={s.name}
                className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white border border-zinc-200 shadow-2xs mx-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-black text-zinc-900">{s.name}</span>
                <span className="text-[11px] font-semibold text-emerald-700">({s.perk})</span>
              </div>
            ))}
          </Marquee>
        </section>
      )}

      {/* 4. Active Comparison Result */}
      <AnimatePresence>
        {result && (
          <main className="max-w-7xl mx-auto px-4 sm:px-6 py-5 sm:py-6 space-y-6 w-full min-w-0">
            {/* Product Header Card with Cool Cursive Brand Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.98, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              className="p-4 sm:p-6 rounded-2xl bg-white border border-zinc-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 w-full min-w-0"
            >
              <div className="space-y-1.5 min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-cursive text-emerald-600 font-bold text-2xl tracking-wide">
                    {result.product.brand}
                  </span>
                  <span className="text-zinc-300">•</span>
                  <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">{result.product.category}</span>
                  {result.product.variant && (
                    <span className="text-xs font-black bg-zinc-950 text-white px-2.5 py-0.5 rounded-lg">
                      {result.product.variant}
                    </span>
                  )}
                </div>
                <h2 className="text-lg sm:text-2xl font-black text-zinc-950 tracking-tight leading-snug break-words">
                  {result.product.normalized_title}
                </h2>
                <p className="text-xs text-zinc-400 font-medium">
                  Slashed across 5 stores in {result.processing_time_ms}ms {result.cached ? "(Instant Cache)" : ""}
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setResult(null)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-black text-zinc-800 hover:text-zinc-950 bg-zinc-100 hover:bg-zinc-200 transition-colors shrink-0 shadow-xs self-start sm:self-auto"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Search another</span>
              </motion.button>
            </motion.div>

            {/* If No Verified Offers Found: Show Honest, Friendly "Sorry" Card */}
            {(result.not_found || !result.offers || result.offers.length === 0) ? (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-8 sm:p-12 rounded-3xl bg-white border-2 border-dashed border-zinc-200 shadow-xs text-center max-w-2xl mx-auto space-y-5"
              >
                <div className="w-16 h-16 bg-amber-50 rounded-2xl flex items-center justify-center mx-auto text-3xl border border-amber-200 shadow-2xs">
                  🔍
                </div>
                <div className="space-y-2">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-amber-100 text-amber-900 border border-amber-300">
                    <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span>Zero False Matches</span>
                    <span className="font-cursive text-amber-800 font-bold">~ 100% real</span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-black text-zinc-950 tracking-tight">
                    Sorry, we couldn&apos;t find verified matches
                  </h3>
                  <p className="text-sm text-zinc-600 max-w-lg mx-auto leading-relaxed">
                    {result.message || "We couldn't find exact, verified prices for this product across other trusted stores right now. Rather than showing you unrelated items or guessing prices, Slash only shows genuine, verified deals."}
                  </p>
                </div>

                <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button
                    onClick={() => setResult(null)}
                    className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-zinc-950 hover:bg-zinc-800 text-white font-black text-xs transition-colors shadow-xs"
                  >
                    Try Another Search
                  </button>
                </div>
              </motion.div>
            ) : (
              <>
                {/* Side-by-Side Store Pricing Grid & List View */}
                <PriceTable
                  offers={result.offers}
                  bestOffer={result.best_offer!}
                  fastestOffer={result.fastest_offer || undefined}
                  product={result.product}
                />

                {/* 30-Day Price Trend Graph & The Real Tea Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full min-w-0">
                  {result.best_offer && (
                    <PriceHistoryChart
                      history={result.price_history || []}
                      currentPrice={result.best_offer.price}
                    />
                  )}
                  {result.review_lens && (
                    <ReviewLens summary={result.review_lens} />
                  )}
                </div>
              </>
            )}
          </main>
        )}
      </AnimatePresence>

      {/* 5. Rich Side-by-Side Laptop Layout: Trending Deals + Magic UI AnimatedList Activity */}
      {!result && (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-10 w-full min-w-0">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start w-full min-w-0">
            {/* Left 7 Columns: Trending Verified Slashes */}
            <div className="lg:col-span-7 space-y-4 w-full min-w-0">
              <div className="flex items-center justify-between pb-1 flex-wrap gap-2">
                <div>
                  <h2 className="text-lg sm:text-xl font-black text-zinc-950 flex items-center gap-2">
                    <Flame className="w-5 h-5 text-emerald-600 fill-emerald-600" />
                    <span>Viral Steals & Price Drops</span>
                  </h2>
                  <p className="text-xs text-zinc-500 mt-0.5 font-normal">
                    Biggest price drops right now • Tap any card to compare live
                  </p>
                </div>

                {/* MOBILE-ONLY COLUMN OR LIST TOGGLE */}
                <div className="flex sm:hidden items-center p-0.5 rounded-xl bg-zinc-100 border border-zinc-200">
                  <button
                    onClick={() => setTrendingViewMode("columns")}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                      trendingViewMode === "columns"
                        ? "bg-zinc-950 text-white shadow-xs"
                        : "text-zinc-500 hover:text-zinc-900"
                    }`}
                  >
                    <LayoutGrid className="w-3.5 h-3.5" />
                    <span>Grid</span>
                  </button>
                  <button
                    onClick={() => setTrendingViewMode("list")}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                      trendingViewMode === "list"
                        ? "bg-zinc-950 text-white shadow-xs"
                        : "text-zinc-500 hover:text-zinc-900"
                    }`}
                  >
                    <ListFilter className="w-3.5 h-3.5" />
                    <span>List</span>
                  </button>
                </div>
              </div>

              {/* MOBILE LIST VIEW for Trending Products */}
              {trendingViewMode === "list" && (
                <div className="flex flex-col gap-2.5 sm:hidden w-full min-w-0">
                  {trendingItems.map((item, idx) => (
                    <motion.div
                      key={item.title}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleSearch(item.sample_query)}
                      className="p-3 rounded-2xl bg-white border border-zinc-200 hover:border-zinc-300 shadow-xs flex items-center gap-3 cursor-pointer w-full min-w-0"
                    >
                      <div className="w-16 h-16 rounded-xl bg-zinc-100 overflow-hidden relative shrink-0">
                        <ImageWithFallback
                          src={item.image}
                          alt={item.title}
                          category={item.category}
                          brand={item.brand}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute bottom-0 inset-x-0 bg-emerald-600 text-white text-[9px] font-black text-center py-0.5">
                          -₹{item.savings} W
                        </div>
                      </div>

                      <div className="min-w-0 flex-1 space-y-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-cursive text-emerald-600 text-base font-bold leading-none">
                            {item.brand}
                          </span>
                          <span className="text-[9px] font-black uppercase tracking-wider bg-zinc-100 text-zinc-700 px-1.5 py-0.2 rounded">
                            {item.culture_tag || (item as any).cultureTag || "VIRAL DEAL 🔥"}
                          </span>
                        </div>
                        <h3 className="font-bold text-xs text-zinc-950 line-clamp-1 leading-snug">
                          {item.title}
                        </h3>
                        <div className="flex items-baseline gap-2 pt-0.5">
                          <span className="text-sm font-black text-zinc-950">
                            {formatINR(item.best_price)}
                          </span>
                          <span className="text-[10px] text-zinc-400 line-through">
                            {formatINR(item.mrp)}
                          </span>
                          <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-1.5 py-0.2 rounded ml-auto">
                            on {item.best_store}
                          </span>
                        </div>
                      </div>

                      <div className="shrink-0 text-zinc-400 pl-1">
                        <ArrowRight className="w-4 h-4" />
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* DESKTOP (Always Grid) / MOBILE GRID (When "columns" selected) */}
              <div
                className={`gap-3.5 w-full min-w-0 ${
                  trendingViewMode === "list"
                    ? "hidden sm:grid sm:grid-cols-2"
                    : "grid grid-cols-1 sm:grid-cols-2"
                }`}
              >
                {trendingItems.map((item, idx) => (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.06 }}
                    whileHover={{ y: -4, scale: 1.01 }}
                    onClick={() => handleSearch(item.sample_query)}
                    className="group p-3.5 rounded-2xl bg-white border border-zinc-200 hover:border-zinc-400 hover:shadow-xl transition-all duration-200 cursor-pointer flex flex-col justify-between min-w-0 overflow-hidden"
                  >
                    <div className="aspect-[4/3] w-full rounded-xl bg-zinc-100 overflow-hidden mb-3 relative">
                      <ImageWithFallback
                        src={item.image}
                        alt={item.title}
                        category={item.category}
                        brand={item.brand}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full text-[10px] font-black bg-zinc-950 text-white shadow-md flex items-center gap-1">
                        <span className="text-emerald-400 font-bold">Save ₹{item.savings}</span>
                        <span>(W)</span>
                      </div>
                      <div className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-wider bg-white/95 text-zinc-900 backdrop-blur-xs shadow-xs">
                        {item.culture_tag || (item as any).cultureTag || "VIRAL DEAL 🔥"}
                      </div>
                    </div>

                    <div className="min-w-0">
                      {/* COOL CURSIVE BRAND BADGE */}
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="font-cursive text-emerald-600 text-xl font-bold tracking-wide">
                          {item.brand}
                        </span>
                      </div>

                      {/* High-Readability Product Title */}
                      <h3 className="font-bold text-xs sm:text-sm text-zinc-950 line-clamp-2 leading-snug group-hover:text-emerald-600 transition-colors">
                        {item.title}
                      </h3>

                      <div className="mt-3 pt-2.5 border-t border-zinc-100 flex items-baseline justify-between">
                        <div>
                          <span className="text-lg font-black text-zinc-950">
                            {formatINR(item.best_price)}
                          </span>
                          <span className="text-xs text-zinc-400 line-through ml-1.5 font-normal">
                            {formatINR(item.mrp)}
                          </span>
                        </div>
                        <span className="text-[11px] font-black text-emerald-800 bg-emerald-50 border border-emerald-200/80 px-2 py-0.5 rounded-lg">
                          on {item.best_store}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Right 5 Columns: Magic UI AnimatedList Activity Feed */}
            <div className="lg:col-span-5 p-5 rounded-2xl bg-white border border-zinc-200 shadow-xs space-y-3.5 w-full min-w-0">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-100">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  <h3 className="font-black text-zinc-950 text-sm">
                    Live Drops Happening Right Now
                  </h3>
                </div>
                <span className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Live Feed</span>
              </div>

              <AnimatedList delay={1400} className="w-full">
                {trendingItems.map((item, idx) => {
                  const times = ["Just now", "2m ago", "4m ago", "6m ago", "9m ago", "12m ago", "15m ago", "18m ago"];
                  const icons = ["🎀", "⚡", "🧴", "✂️", "🏋️", "💅", "🧪", "🩺"];
                  const colors = ["#EC4899", "#F59E0B", "#3B82F6", "#F59E0B", "#10B981", "#EC4899", "#8B5CF6", "#10B981"];
                  const icon = icons[idx % icons.length];
                  const color = colors[idx % colors.length];
                  const time = times[idx % times.length];

                  return (
                    <figure
                      key={item.title}
                      onClick={() => handleSearch(item.sample_query)}
                      className="relative w-full cursor-pointer overflow-hidden rounded-xl p-3 transition-all duration-200 hover:bg-emerald-50/50 hover:border-emerald-300 hover:shadow-md bg-zinc-50 border border-zinc-200/80 shadow-xs flex items-center gap-3 active:scale-[0.98] group"
                    >
                      <div
                        className="flex size-9 items-center justify-center rounded-xl font-bold text-base shrink-0 group-hover:scale-110 transition-transform"
                        style={{ backgroundColor: `${color}15`, color }}
                      >
                        {icon}
                      </div>
                      <div className="flex flex-col overflow-hidden text-left w-full min-w-0">
                        <figcaption className="flex flex-row items-center justify-between text-xs font-black text-zinc-900">
                          <span className="truncate group-hover:text-emerald-700 transition-colors">
                            {item.title}
                          </span>
                          <span className="text-[10px] text-zinc-400 font-normal shrink-0 ml-1">
                            {time}
                          </span>
                        </figcaption>
                        <div className="flex items-center justify-between gap-1 mt-0.5">
                          <p className="text-[11px] font-semibold text-emerald-700 truncate">
                            Slashed from ₹{item.mrp} to ₹{item.best_price} on {item.best_store} (Saved ₹{item.savings}! 🔥)
                          </p>
                          <span className="text-[9px] font-black text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded shrink-0 opacity-80 group-hover:opacity-100 flex items-center gap-0.5">
                            View Deal ↗
                          </span>
                        </div>
                      </div>
                    </figure>
                  );
                })}
              </AnimatedList>
            </div>
          </div>

          {/* 3 Core Gen-Z Value Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 border-t border-zinc-200 w-full min-w-0">
            <div className="p-5 rounded-2xl bg-white border border-zinc-200 space-y-2 shadow-xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-950 text-white flex items-center justify-center text-lg">
                💅
              </div>
              <h4 className="font-black text-zinc-950 text-base">Zero Gatekeeping</h4>
              <p className="text-xs text-zinc-500 leading-relaxed font-medium">
                We track the exact barcode across official stores. No knockoffs, no dupes, no random third-party sellers. Only 100% authentic drip.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-zinc-200 space-y-2 shadow-xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-950 text-white flex items-center justify-center text-lg">
                🔑
              </div>
              <h4 className="font-black text-zinc-950 text-base">Cheat Codes Unlocked</h4>
              <p className="text-xs text-zinc-500 leading-relaxed font-medium">
                Stores hide discounts behind secret checkout coupons. Slash sniffs them out and auto-applies them directly so you never pay retail.
              </p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-zinc-200 space-y-2 shadow-xs">
              <div className="w-10 h-10 rounded-xl bg-zinc-950 text-white flex items-center justify-center text-lg">
                🍵
              </div>
              <h4 className="font-black text-zinc-950 text-base">The Real Tea</h4>
              <p className="text-xs text-zinc-500 leading-relaxed font-medium">
                We digest thousands of real buyer reviews from store apps so you know if it's actually worth the hype or straight-up mid before spending a single rupee.
              </p>
            </div>
          </div>
        </main>
      )}

      {/* 6. Footer */}
      <footer className="mt-16 py-8 border-t border-zinc-200 text-center text-xs text-zinc-400 space-y-2">
        <p>© 2026 Slash. Fast, unbiased price comparison across Amazon, Nykaa, Tira, Blinkit & Zepto.</p>
        <p className="text-[11px] text-zinc-400/80">
          All product names, logos, and brands are property of their respective owners. Zero sponsored bias.
        </p>
      </footer>
    </div>
  );
}
