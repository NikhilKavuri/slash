"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, Tag, X } from "lucide-react";

export type SnackbarType = "success" | "error" | "info" | "coupon";

export interface SnackbarMessage {
  id: string;
  type: SnackbarType;
  title: string;
  description?: string;
}

interface SnackbarContextType {
  showSnackbar: (title: string, description?: string, type?: SnackbarType) => void;
  showCouponToast: (code: string, store?: string) => void;
  showSuccessToast: (title: string, description?: string) => void;
  showErrorToast: (title: string, description?: string) => void;
}

const SnackbarContext = createContext<SnackbarContextType | null>(null);

export function SnackbarProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<SnackbarMessage[]>([]);

  const removeMessage = useCallback((id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const showSnackbar = useCallback(
    (title: string, description?: string, type: SnackbarType = "info") => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
      setMessages((prev) => [...prev.slice(-2), { id, title, description, type }]); // Keep max 3 toasts

      setTimeout(() => {
        removeMessage(id);
      }, 3500);
    },
    [removeMessage]
  );

  const showCouponToast = useCallback(
    (code: string, store?: string) => {
      showSnackbar(
        `Code ${code} copied!`,
        store ? `Paste at ${store} checkout for instant discount.` : "Apply at checkout to save extra.",
        "coupon"
      );
    },
    [showSnackbar]
  );

  const showSuccessToast = useCallback(
    (title: string, description?: string) => {
      showSnackbar(title, description, "success");
    },
    [showSnackbar]
  );

  const showErrorToast = useCallback(
    (title: string, description?: string) => {
      showSnackbar(title, description, "error");
    },
    [showSnackbar]
  );

  return (
    <SnackbarContext.Provider
      value={{ showSnackbar, showCouponToast, showSuccessToast, showErrorToast }}
    >
      {children}

      {/* Floating Real-Time Snackbars Container (Bottom Center on all viewports) */}
      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-2 pointer-events-none w-full max-w-sm px-4">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 20, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.92 }}
              transition={{ type: "spring", stiffness: 450, damping: 30 }}
              className="pointer-events-auto w-full p-3.5 rounded-2xl bg-zinc-950/95 backdrop-blur-md text-white border border-zinc-800 shadow-2xl flex items-center justify-between gap-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="shrink-0 flex items-center justify-center">
                  {msg.type === "coupon" && (
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                      <Tag className="w-4 h-4" />
                    </div>
                  )}
                  {msg.type === "success" && (
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                  )}
                  {msg.type === "error" && (
                    <div className="w-8 h-8 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
                      <AlertCircle className="w-4 h-4" />
                    </div>
                  )}
                  {msg.type === "info" && (
                    <div className="w-8 h-8 rounded-xl bg-zinc-800 text-zinc-300 flex items-center justify-center border border-zinc-700">
                      <Info className="w-4 h-4" />
                    </div>
                  )}
                </div>

                <div className="min-w-0">
                  <div className="text-xs font-black tracking-tight text-white flex items-center gap-1.5">
                    <span>{msg.title}</span>
                  </div>
                  {msg.description && (
                    <p className="text-[11px] text-zinc-400 leading-tight truncate mt-0.5 font-normal">
                      {msg.description}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={() => removeMessage(msg.id)}
                className="text-zinc-500 hover:text-white transition-colors shrink-0 p-1"
                aria-label="Close"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </SnackbarContext.Provider>
  );
}

export function useSnackbar() {
  const context = useContext(SnackbarContext);
  if (!context) {
    throw new Error("useSnackbar must be used within a SnackbarProvider");
  }
  return context;
}
