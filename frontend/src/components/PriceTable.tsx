"use client";

import { useState } from "react";
import { StoreOffer } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import {
  ExternalLink,
  Zap,
  CheckCircle2,
  Copy,
  Check,
  ShieldCheck,
  Tag,
  LayoutGrid,
  ListFilter,
  Clock,
  Star,
  Sparkles,
  Flame,
} from "lucide-react";
import { BorderBeam } from "./magicui/border-beam";
import { motion } from "framer-motion";
import { useSnackbar } from "./Snackbar";

interface PriceTableProps {
  offers: StoreOffer[];
  bestOffer: StoreOffer;
  fastestOffer?: StoreOffer;
}

export function PriceTable({ offers, bestOffer, fastestOffer }: PriceTableProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"side-by-side" | "list">("side-by-side");
  const { showCouponToast } = useSnackbar();

  const handleCopyCoupon = (code: string, store: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    showCouponToast(code, store);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const getStoreTheme = (store: string) => {
    const s = store.toLowerCase();
    if (s.includes("tira"))
      return { bg: "bg-rose-50", border: "border-rose-200", text: "text-rose-700" };
    if (s.includes("nykaa"))
      return { bg: "bg-pink-50", border: "border-pink-200", text: "text-pink-700" };
    if (s.includes("zepto"))
      return { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700" };
    if (s.includes("blinkit"))
      return { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700" };
    return { bg: "bg-zinc-100", border: "border-zinc-300", text: "text-zinc-800" };
  };

  return (
    <div className="space-y-3.5 w-full min-w-0">
      {/* 1. Header with Controls */}
      <div className="flex items-center justify-between gap-2 pb-1 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-base sm:text-lg font-black text-zinc-950 tracking-tight flex items-center gap-1.5">
            <span>Compare Store Drops</span>
            <span className="text-xs font-cursive text-emerald-600 font-bold">~ ranked by price</span>
          </h3>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-2xs">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live Stock Checked
          </span>
        </div>

        {/* View Toggle */}
        <div className="flex items-center p-0.5 rounded-xl bg-zinc-100 border border-zinc-200">
          <button
            onClick={() => setViewMode("side-by-side")}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold transition-all ${
              viewMode === "side-by-side"
                ? "bg-zinc-950 text-white shadow-xs"
                : "text-zinc-500 hover:text-zinc-900"
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>Columns</span>
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold transition-all ${
              viewMode === "list"
                ? "bg-zinc-950 text-white shadow-xs"
                : "text-zinc-500 hover:text-zinc-900"
            }`}
          >
            <ListFilter className="w-3.5 h-3.5" />
            <span>List</span>
          </button>
        </div>
      </div>

      {/* 2. COMPACT 5-COLUMN SIDE-BY-SIDE GRID */}
      {viewMode === "side-by-side" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 w-full min-w-0">
          {offers.map((offer, index) => {
            const theme = getStoreTheme(offer.store_name);
            const isInstant = offer.delivery_type === "instant";

            return (
              <motion.div
                key={offer.store_name}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.25 }}
                className={`relative flex flex-col justify-between p-3.5 rounded-2xl bg-white border transition-all duration-200 shadow-xs hover:shadow-md min-w-0 overflow-hidden ${
                  offer.is_best_price
                    ? "border-emerald-500 ring-2 ring-emerald-500/30 bg-gradient-to-b from-emerald-50/40 via-white to-white"
                    : "border-zinc-200/90 hover:border-zinc-400"
                }`}
              >
                {/* BorderBeam on lowest price card */}
                {offer.is_best_price && (
                  <BorderBeam size={160} duration={6} colorFrom="#10b981" colorTo="#09090b" borderWidth={2} />
                )}

                <div className="space-y-2.5 min-w-0">
                  {/* Top Store Header */}
                  <div className="flex items-center justify-between gap-1 min-w-0">
                    <div className="flex items-center gap-2 min-w-0">
                      <div
                        className={`w-7 h-7 rounded-xl flex items-center justify-center font-black text-[11px] ${theme.bg} ${theme.text} ${theme.border} border shrink-0`}
                      >
                        {offer.store_name.substring(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <h4 className="font-extrabold text-zinc-950 text-xs sm:text-sm leading-tight truncate">
                          {offer.store_name}
                        </h4>
                        <div className="flex items-center gap-1 text-[10px] text-zinc-400">
                          <Star className="w-2.5 h-2.5 fill-amber-400 text-amber-400" />
                          <span className="font-semibold text-zinc-600">{offer.rating}</span>
                        </div>
                      </div>
                    </div>

                    {offer.is_best_price ? (
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-600 text-white shrink-0 shadow-xs flex items-center gap-1">
                        <span>MASSIVE W</span>
                        <span>🏆</span>
                      </span>
                    ) : isInstant ? (
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-black bg-zinc-950 text-white shrink-0 flex items-center gap-1">
                        <Zap className="w-2.5 h-2.5 fill-amber-400 text-amber-400" /> 10m Drop
                      </span>
                    ) : null}
                  </div>

                  {/* Price Breakdown with Final Checkout Steal */}
                  <div className="pt-2 border-t border-zinc-100 space-y-1">
                    <div className="flex items-baseline gap-1.5 flex-wrap">
                      <span className="text-2xl font-black text-zinc-950 tracking-tight">
                        {formatINR(offer.final_price || offer.price)}
                      </span>
                      {offer.coupon_discount && offer.coupon_discount > 0 ? (
                        <span className="text-xs text-zinc-400 line-through font-normal">
                          {formatINR(offer.price)}
                        </span>
                      ) : (
                        <span className="text-xs text-zinc-400 line-through font-normal">
                          {formatINR(offer.mrp)}
                        </span>
                      )}
                    </div>

                    {offer.coupon_discount && offer.coupon_discount > 0 ? (
                      <div className="text-[10px] font-black text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded-md inline-flex items-center gap-1">
                        <Tag className="w-2.5 h-2.5 text-emerald-700" />
                        <span>Code saves {formatINR(offer.coupon_discount)} extra</span>
                      </div>
                    ) : null}

                    <div className="text-[11px] font-black text-emerald-700 flex items-center gap-1 flex-wrap">
                      <span>Total Save {formatINR(offer.savings_vs_mrp)}</span>
                      <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1 rounded font-bold">
                        -{offer.total_discount_percent || offer.discount_percent}% Total
                      </span>
                    </div>
                  </div>

                  {/* SELLER VERIFICATION */}
                  <div className="px-2.5 py-1.5 rounded-xl bg-zinc-50 border border-zinc-200/80 space-y-0.5 min-w-0">
                    <div className="flex items-center gap-1 text-[10px] font-black text-emerald-700 min-w-0">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span className="truncate">{offer.authenticity_badge || "Official Brand Mall"}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 truncate" title={offer.seller_name}>
                      Seller: {offer.seller_name}
                    </p>
                  </div>

                  {/* Shipping Speed */}
                  <div className="px-2.5 py-1 rounded-xl bg-zinc-50 border border-zinc-200/60 flex items-center gap-1.5 text-[11px] font-semibold text-zinc-700 min-w-0">
                    {isInstant ? (
                      <Zap className="w-3 h-3 text-amber-500 shrink-0 fill-amber-500" />
                    ) : (
                      <Clock className="w-3 h-3 text-zinc-400 shrink-0" />
                    )}
                    <span className="truncate">{offer.delivery_badge}</span>
                  </div>

                  {/* Coupon Pill */}
                  {offer.coupon_code ? (
                    <div className="px-2.5 py-1.5 rounded-xl bg-emerald-50 border border-emerald-300 flex items-center justify-between text-[11px] min-w-0">
                      <div className="flex items-center gap-1 truncate min-w-0">
                        <Tag className="w-3 h-3 text-emerald-600 shrink-0" />
                        <span className="font-mono font-black text-emerald-900 tracking-wide truncate">
                          {offer.coupon_code}
                        </span>
                      </div>
                      <button
                        onClick={() => handleCopyCoupon(offer.coupon_code!, offer.store_name)}
                        className="text-[10px] font-black text-emerald-700 hover:text-emerald-950 transition-colors shrink-0 ml-1.5 underline decoration-emerald-400"
                      >
                        {copiedCode === offer.coupon_code ? "✓ Copied!" : "Copy"}
                      </button>
                    </div>
                  ) : (
                    <div className="px-2 py-1 rounded-xl bg-zinc-50 border border-dashed border-zinc-200 text-center text-[10px] text-zinc-400 font-medium">
                      Store Discount Auto-Applied
                    </div>
                  )}
                </div>

                {/* Buy Button */}
                <div className="pt-3 mt-1">
                  <motion.a
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    href={offer.affiliate_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`w-full py-2.5 px-3 rounded-xl font-black text-xs flex items-center justify-center gap-1.5 shadow-xs transition-all text-center ${
                      offer.is_best_price
                        ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30"
                        : "bg-zinc-950 hover:bg-zinc-800 text-white"
                    }`}
                  >
                    <span>Secure on {offer.store_name}</span>
                    <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                  </motion.a>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 3. DENSE RESPONSIVE LIST VIEW */}
      {viewMode === "list" && (
        <div className="bg-white rounded-2xl border border-zinc-200/90 overflow-hidden shadow-xs divide-y divide-zinc-100 w-full min-w-0">
          {offers.map((offer) => {
            const theme = getStoreTheme(offer.store_name);
            const isInstant = offer.delivery_type === "instant";

            return (
              <div
                key={offer.store_name}
                className={`p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-zinc-50/80 transition-colors w-full min-w-0 ${
                  offer.is_best_price ? "bg-emerald-50/30" : ""
                }`}
              >
                {/* Left/Middle: Store info & badges */}
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-xs ${theme.bg} ${theme.text} ${theme.border} border shrink-0 mt-0.5`}
                  >
                    {offer.store_name.substring(0, 2).toUpperCase()}
                  </div>

                  <div className="min-w-0 flex-1 space-y-1">
                    {/* Store Title & Best Price Badge */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-extrabold text-zinc-950 text-sm">{offer.store_name}</span>
                      {offer.is_best_price && (
                        <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-emerald-600 text-white flex items-center gap-1">
                          <span>MASSIVE W</span>
                          <span>🏆</span>
                        </span>
                      )}
                      {isInstant && (
                        <span className="text-[10px] font-black text-white bg-zinc-950 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                          <Zap className="w-2.5 h-2.5 fill-amber-400 text-amber-400" /> 10m Drop
                        </span>
                      )}
                    </div>

                    {/* Authenticity Badge + Seller (Safe truncation on mobile) */}
                    <div className="flex items-center gap-1.5 text-[11px] text-zinc-600 min-w-0 flex-wrap">
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-700 shrink-0">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span>Verified Legit</span>
                      </span>
                      <span className="text-zinc-300">•</span>
                      <span className="text-zinc-500 truncate max-w-[200px] sm:max-w-xs text-[11px] font-medium">
                        {offer.seller_name}
                      </span>
                    </div>

                    {/* Delivery & Active Coupon */}
                    <div className="flex items-center gap-2 text-xs text-zinc-500 flex-wrap pt-0.5">
                      <span className="text-[11px] text-zinc-600 font-semibold">
                        {offer.delivery_badge}
                      </span>
                      {offer.coupon_code && (
                        <button
                          onClick={() => handleCopyCoupon(offer.coupon_code!, offer.store_name)}
                          className="inline-flex items-center gap-1 font-mono font-black text-[11px] text-emerald-900 bg-emerald-100/70 hover:bg-emerald-200/70 border border-emerald-300 px-2 py-0.5 rounded-lg transition-colors"
                          title="Click to copy code"
                        >
                          <Tag className="w-2.5 h-2.5 text-emerald-700" />
                          <span>Code: {offer.coupon_code}</span>
                          <span className="text-[9px] text-emerald-800 font-sans ml-0.5">
                            {copiedCode === offer.coupon_code ? "(✓ Copied)" : "(Tap to Copy)"}
                          </span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right: Price & View Deal CTA */}
                <div className="flex items-center justify-between sm:justify-end gap-3.5 pt-2 sm:pt-0 border-t sm:border-t-0 border-zinc-100 shrink-0">
                  <div className="text-left sm:text-right">
                    <div className="text-xl font-black text-zinc-950 tracking-tight">
                      {formatINR(offer.final_price || offer.price)}
                    </div>
                    <div className="text-[11px] text-zinc-400 line-through">
                      MRP {formatINR(offer.mrp)}
                    </div>
                    {offer.coupon_discount && offer.coupon_discount > 0 ? (
                      <div className="text-[10px] font-bold text-emerald-700">
                        Code saved {formatINR(offer.coupon_discount)}
                      </div>
                    ) : null}
                  </div>

                  <a
                    href={offer.affiliate_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-black transition-all shadow-xs shrink-0 ${
                      offer.is_best_price
                        ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30"
                        : "bg-zinc-950 hover:bg-zinc-800 text-white"
                    }`}
                  >
                    <span>Secure Deal</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Trust Guarantee Note */}
      <div className="flex items-center justify-center gap-2 text-[11px] text-zinc-500 py-1 font-semibold text-center px-2">
        <span className="text-emerald-600">🛡️</span>
        <span>100% Legit Retailers • Zero Knockoffs • Exact Barcode Match Only</span>
      </div>
    </div>
  );
}
