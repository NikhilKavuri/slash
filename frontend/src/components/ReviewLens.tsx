"use client";

import { ReviewLensSummary } from "@/lib/api";
import { Star, ThumbsUp, AlertCircle, Sparkles, ShieldCheck, CheckCircle2, MessageSquareText } from "lucide-react";

interface ReviewLensProps {
  summary: ReviewLensSummary;
}

export function ReviewLens({ summary }: ReviewLensProps) {
  const reviews = summary.customer_reviews || [];

  return (
    <div className="bg-white rounded-2xl border border-zinc-200/90 p-4 sm:p-5 shadow-xs space-y-4 w-full min-w-0">
      {/* Header: The Real Tea */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-base">
              🍵
            </span>
            <div>
              <h3 className="font-black text-zinc-950 text-base sm:text-lg tracking-tight flex items-center gap-2">
                <span>The Real Tea</span>
                <span className="text-[10px] font-black uppercase tracking-wider bg-zinc-950 text-white px-2 py-0.5 rounded-full">
                  Unbiased AI Verdict
                </span>
              </h3>
            </div>
          </div>
          <p className="text-xs text-zinc-500 mt-1 font-normal">
            Synthesized from {summary.total_reviews_count.toLocaleString("en-IN")}+ verified buyers across Amazon, Nykaa & Tira
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200/80">
          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
          <span className="font-black text-zinc-950 text-sm">{summary.overall_rating}</span>
          <span className="text-xs text-zinc-400 font-medium">/ 5.0</span>
          <span className="text-[10px] font-bold text-amber-800 ml-1">
            {summary.overall_rating >= 4.5 ? "Viral Hype 🔥" : "Solid Pick ✨"}
          </span>
        </div>
      </div>

      {/* The Verdict: Is it worth the hype? */}
      <div className="p-3.5 rounded-2xl bg-zinc-950 text-white border border-zinc-800 space-y-1">
        <div className="text-[10px] font-black uppercase tracking-widest text-emerald-400 flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-emerald-400" />
          <span>Is It Actually Worth The Hype?</span>
        </div>
        <p className="text-xs sm:text-sm leading-relaxed text-zinc-200 font-medium">
          {summary.verdict}
        </p>
      </div>

      {/* The Hype (Pros) & The Icks (Cons) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* The Hype (Pros) */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-black text-emerald-700 uppercase tracking-wider">
            <span>😍 The Hype (Why people obsess)</span>
          </div>
          <ul className="space-y-1.5">
            {summary.pros.map((pro, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-xs text-zinc-800 bg-emerald-50/60 border border-emerald-200/60 p-2.5 rounded-xl font-medium"
              >
                <span className="text-emerald-600 font-black shrink-0 text-xs">✓</span>
                <span>{pro}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* The Icks (Cons) */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-black text-amber-800 uppercase tracking-wider">
            <span>🚩 The Icks & Red Flags</span>
          </div>
          <ul className="space-y-1.5">
            {summary.cons.map((con, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-xs text-zinc-800 bg-amber-50/60 border border-amber-200/60 p-2.5 rounded-xl font-medium"
              >
                <span className="text-amber-600 font-black shrink-0 text-xs">!</span>
                <span>{con}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* UNFILTERED BUYER TAKES FROM STORE APPS */}
      {reviews.length > 0 && (
        <div className="pt-3 border-t border-zinc-100 space-y-2.5">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h4 className="text-xs font-black uppercase tracking-wider text-zinc-950 flex items-center gap-1.5">
              <MessageSquareText className="w-3.5 h-3.5 text-zinc-700" />
              <span>Unfiltered Buyer Takes from Store Apps</span>
            </h4>
            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>100% Verified Purchases Only</span>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
            {reviews.map((rev, i) => (
              <div
                key={i}
                className="p-3 rounded-2xl bg-zinc-50 border border-zinc-200/80 space-y-2 flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-white border border-zinc-200 text-zinc-800">
                      {rev.store} Reviewer
                    </span>
                    <div className="flex items-center gap-0.5 text-amber-400">
                      {[...Array(5)].map((_, starIdx) => (
                        <Star
                          key={starIdx}
                          className={`w-2.5 h-2.5 ${
                            starIdx < Math.round(rev.rating)
                              ? "fill-amber-400 text-amber-400"
                              : "text-zinc-200 fill-zinc-200"
                          }`}
                        />
                      ))}
                    </div>
                  </div>

                  <div>
                    {rev.headline && (
                      <div className="text-xs font-bold text-zinc-900 mb-0.5">
                        "{rev.headline}"
                      </div>
                    )}
                    <p className="text-xs text-zinc-600 italic leading-snug line-clamp-3">
                      {(rev as any).comment || (rev as any).review_text || rev.headline}
                    </p>
                  </div>
                </div>

                <div className="pt-1.5 border-t border-zinc-200/60 flex items-center justify-between text-[10px] text-zinc-400">
                  <span className="font-semibold text-zinc-700 truncate max-w-[120px]">
                    {(rev as any).buyer_name || (rev as any).user_name || "Verified Buyer"}
                  </span>
                  <span className="text-emerald-700 font-bold flex items-center gap-0.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    Verified Buyer
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
