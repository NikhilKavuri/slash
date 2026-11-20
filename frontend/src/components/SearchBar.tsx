"use client";

import { useState } from "react";
import { Search, Clipboard, ArrowRight, Loader2, Sparkles } from "lucide-react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [inputVal, setInputVal] = useState("");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || isLoading) return;
    onSearch(inputVal.trim());
  };

  const handlePasteClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInputVal(text);
        onSearch(text);
      }
    } catch {
      // Clipboard permission denied or unsupported
    }
  };

  const quickSamples = [
    { label: "Minimalist Serum", query: "Minimalist Niacinamide 10% Face Serum 30ml" },
    { label: "MuscleBlaze Whey", query: "MuscleBlaze Biozyme Performance Whey 1kg" },
    { label: "Philips Trimmer", query: "Philips Series 3000 Beard Trimmer" },
    { label: "Laneige Lip Mask", query: "Laneige Lip Sleeping Mask Berry 20g" },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto px-2 sm:px-0">
      {/* Search Bar Container */}
      <form
        onSubmit={handleSubmit}
        className="relative flex items-center p-1.5 sm:p-2 rounded-2xl bg-white shadow-xl shadow-zinc-950/5 border border-zinc-200/90 focus-within:border-emerald-500 focus-within:ring-4 focus-within:ring-emerald-100 transition-all duration-200 gap-2"
      >
        <div className="pl-2 sm:pl-3 text-zinc-400 shrink-0">
          <Search className="w-4 h-4 sm:w-5 sm:h-5" />
        </div>

        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Paste product link (Amazon, Nykaa, Tira, Blinkit) or search..."
          className="w-full min-w-0 bg-transparent text-zinc-900 placeholder:text-zinc-400 text-xs sm:text-sm md:text-base font-normal focus:outline-none"
          disabled={isLoading}
        />

        {/* Quick Paste Button for Mobile/Desktop */}
        <button
          type="button"
          onClick={handlePasteClipboard}
          className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-zinc-600 bg-zinc-100 hover:bg-zinc-200 transition-colors shrink-0"
          title="Paste from clipboard"
        >
          <Clipboard className="w-3.5 h-3.5" />
          <span>Paste</span>
        </button>

        {/* High-Contrast Crystal-Clear Action Button */}
        <button
          type="submit"
          disabled={isLoading || !inputVal.trim()}
          className="inline-flex items-center justify-center gap-1.5 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-zinc-950 hover:bg-emerald-600 active:scale-98 text-white font-black text-xs sm:text-sm tracking-wide transition-all shadow-md shrink-0 disabled:opacity-40 disabled:hover:bg-zinc-950 cursor-pointer"
        >
          {isLoading ? (
            <span className="flex items-center gap-1.5">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
              <span className="hidden sm:inline">Scanning...</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5">
              <span>Slash Price</span>
              <ArrowRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-400" />
            </span>
          )}
        </button>
      </form>

      {/* Quick Pills */}
      <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 mt-3 text-xs text-zinc-500">
        <span className="flex items-center gap-1 font-bold text-zinc-400 text-[11px] uppercase tracking-wider">
          <Sparkles className="w-3 h-3 text-emerald-500" />
          <span>Try:</span>
        </span>
        {quickSamples.map((sample) => (
          <button
            key={sample.label}
            type="button"
            onClick={() => {
              setInputVal(sample.query);
              onSearch(sample.query);
            }}
            className="px-2.5 py-1 rounded-full bg-white hover:bg-zinc-100 text-zinc-700 hover:text-zinc-950 transition-colors font-medium border border-zinc-200 shadow-2xs text-[11px] sm:text-xs"
          >
            {sample.label}
          </button>
        ))}
      </div>
    </div>
  );
}
