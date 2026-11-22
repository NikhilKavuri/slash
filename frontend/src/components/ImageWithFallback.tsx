"use client";

import { useState } from "react";
import { Package } from "lucide-react";

interface ImageWithFallbackProps {
  src?: string;
  alt: string;
  className?: string;
  category?: string;
  brand?: string;
}

export function ImageWithFallback({
  src,
  alt,
  className = "",
  category,
  brand,
}: ImageWithFallbackProps) {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const sanitizedSrc = src ? src.replace("rukmini2.flixcart.com", "rukminim2.flixcart.com") : undefined;

  if (!sanitizedSrc || error) {
    return (
      <div
        className={`w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-zinc-100 via-zinc-200/70 to-zinc-100 p-4 text-center select-none ${className}`}
      >
        <div className="w-10 h-10 rounded-xl bg-white shadow-xs border border-zinc-200/80 flex items-center justify-center text-zinc-700 mb-1.5">
          <Package className="w-5 h-5 text-emerald-600" />
        </div>
        {brand && (
          <span className="font-cursive text-emerald-700 text-sm font-bold leading-none">
            {brand}
          </span>
        )}
        <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider line-clamp-1 mt-0.5">
          {category || "Verified Deal"}
        </span>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden">
      {!loaded && (
        <div className="absolute inset-0 bg-zinc-100/90 animate-pulse flex items-center justify-center z-10">
          <span className="w-5 h-5 rounded-full border-2 border-emerald-500/20 border-t-emerald-500 animate-spin" />
        </div>
      )}
      <img
        src={sanitizedSrc}
        alt={alt}
        loading="eager"
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
        className={`${className} ${
          loaded ? "opacity-100" : "opacity-0"
        } transition-opacity duration-300`}
      />
    </div>
  );
}
