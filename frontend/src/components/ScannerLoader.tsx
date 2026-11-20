"use client";

import { useEffect, useState } from "react";
import { SlashLogo } from "./SlashLogo";
import { BorderBeam } from "./magicui/border-beam";
import { motion } from "framer-motion";
import { Sparkles, Check, Zap, Loader2 } from "lucide-react";

interface ScannerLoaderProps {
  query?: string;
}

const STORES = [
  { name: "Amazon", color: "#FF9900", perk: "Prime Next-Day", delay: 200 },
  { name: "Tira", color: "#D4426F", perk: "20% Off Code", delay: 500 },
  { name: "Nykaa", color: "#FC2779", perk: "Official Brand Mall", delay: 800 },
  { name: "Zepto", color: "#800080", isFast: true, perk: "10-Min Delivery", delay: 1100 },
  { name: "Blinkit", color: "#F8CB46", isFast: true, perk: "Instant Essentials", delay: 1400 },
];

const SCAN_STEPS = [
  "Locking onto exact barcode & bottle size...",
  "Querying real-time stock across 5 stores...",
  "Sniffing out secret checkout codes (TIRA20, AMZPAY5)...",
  "Locking in the biggest price slash...",
];

export function ScannerLoader({ query }: ScannerLoaderProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [completedStores, setCompletedStores] = useState<string[]>([]);

  useEffect(() => {
    // Cycle through steps
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev < SCAN_STEPS.length - 1 ? prev + 1 : prev));
    }, 450);

    // Light up stores sequentially
    STORES.forEach((s) => {
      setTimeout(() => {
        setCompletedStores((prev) => [...prev, s.name]);
      }, s.delay);
    });

    return () => clearInterval(stepInterval);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-md"
    >
      <div className="relative w-full max-w-lg p-5 sm:p-8 rounded-3xl bg-zinc-900 border border-zinc-800 shadow-2xl text-center space-y-5 overflow-hidden">
        {/* Animated Border Beam around modal */}
        <BorderBeam size={220} duration={5} colorFrom="#10b981" colorTo="#00ff66" borderWidth={2} />

        {/* Laser Scanner Effect line */}
        <motion.div
          animate={{ y: [-100, 220, -100] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-60 blur-xs pointer-events-none"
        />

        {/* Central Logo with Pulsing Ring */}
        <div className="relative flex justify-center">
          <div className="relative">
            <SlashLogo className="w-14 h-14" />
            <span className="absolute -top-1 -right-1 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
            </span>
          </div>
        </div>

        {/* Heading & Target */}
        <div className="space-y-1">
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center justify-center gap-2">
            <span>Slashing Prices Across Stores</span>
            <span className="text-xl">✂️</span>
          </h3>
          {query && (
            <p className="text-xs text-zinc-400 line-clamp-1 font-mono max-w-sm mx-auto">
              Hunting: <span className="text-emerald-400 font-bold">"{query}"</span>
            </p>
          )}
        </div>

        {/* Live Multi-Store Radar */}
        <div className="p-3.5 sm:p-4 rounded-2xl bg-zinc-950/95 border border-zinc-800/80 space-y-2.5">
          <div className="text-[11px] font-black uppercase tracking-wider text-zinc-400 text-left flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Scanning Store Inventories</span>
            </span>
            <span className="text-emerald-400 font-mono text-xs font-bold">
              {completedStores.length}/{STORES.length} Stores Checked
            </span>
          </div>

          {/* MOBILE LIST VIEW */}
          <div className="flex flex-col gap-2 sm:hidden text-left">
            {STORES.map((store) => {
              const isDone = completedStores.includes(store.name);

              return (
                <div
                  key={store.name}
                  className={`flex items-center justify-between p-2 rounded-xl border transition-all duration-300 ${
                    isDone
                      ? "bg-zinc-900 border-emerald-500/50 text-white shadow-xs"
                      : "bg-zinc-900/40 border-zinc-800 text-zinc-500"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center font-black text-[10px] shrink-0 text-white"
                      style={{ backgroundColor: store.color }}
                    >
                      {store.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-bold text-zinc-100 flex items-center gap-1.5 truncate">
                        <span>{store.name}</span>
                        {store.isFast && (
                          <span className="text-[9px] font-black text-amber-400 bg-amber-400/10 px-1 py-0.2 rounded flex items-center gap-0.5">
                            <Zap className="w-2.5 h-2.5 fill-amber-400" /> 10m
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-zinc-400 truncate">{store.perk}</div>
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center gap-1.5 pl-2">
                    {isDone ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-black text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                        <Check className="w-3 h-3 stroke-[3]" />
                        <span>Price Slashed</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-zinc-500">
                        <Loader2 className="w-3 h-3 animate-spin text-zinc-400" />
                        <span>Scanning...</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* DESKTOP 5-COLUMN GRID VIEW */}
          <div className="hidden sm:grid grid-cols-5 gap-2">
            {STORES.map((store) => {
              const isDone = completedStores.includes(store.name);

              return (
                <div
                  key={store.name}
                  className={`p-2.5 rounded-xl border text-center transition-all duration-300 ${
                    isDone
                      ? "bg-zinc-800/80 border-emerald-500/50 text-white shadow-xs"
                      : "bg-zinc-900/50 border-zinc-800 text-zinc-600"
                  }`}
                >
                  <div className="text-xs font-black truncate">{store.name}</div>
                  <div className="flex items-center justify-center mt-1.5">
                    {isDone ? (
                      <span className="w-4 h-4 rounded-full bg-emerald-500 text-zinc-950 flex items-center justify-center text-[10px] font-bold animate-in zoom-in">
                        ✓
                      </span>
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Dynamic Step Ticker */}
        <div className="flex items-center justify-center gap-2 text-xs font-bold text-emerald-400">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <motion.span
            key={activeStep}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="truncate font-mono"
          >
            {SCAN_STEPS[activeStep]}
          </motion.span>
        </div>
      </div>
    </motion.div>
  );
}
