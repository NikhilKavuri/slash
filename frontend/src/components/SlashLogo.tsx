import React from "react";

export function SlashLogo({ className = "w-10 h-10" }: { className?: string }) {
  return (
    <div
      className={`relative rounded-2xl bg-zinc-950 border border-zinc-800 flex items-center justify-center shadow-md shadow-zinc-950/20 overflow-hidden shrink-0 ${className}`}
    >
      {/* Background emerald radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.2),transparent_70%)]" />

      {/* Custom Slashed Rupee (₹) Symbol */}
      <svg
        width="26"
        height="26"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="relative z-10"
      >
        {/* Rupee Top Bar (Left half of cut) */}
        <line
          x1="7"
          y1="8"
          x2="17"
          y2="8"
          stroke="#E4E4E7"
          strokeWidth="2.4"
          strokeLinecap="round"
        />

        {/* Rupee Second Bar (Left half of cut) */}
        <line
          x1="7"
          y1="13"
          x2="13"
          y2="13"
          stroke="#E4E4E7"
          strokeWidth="2.4"
          strokeLinecap="round"
        />

        {/* Rupee Loop / Curve */}
        <path
          d="M7 8V18C10.5 18 14 17 14 13C14 9 10 8 7 8Z"
          stroke="#E4E4E7"
          strokeWidth="2.4"
          strokeLinejoin="round"
        />

        {/* Rupee Diagonal Leg (Bottom Right) */}
        <path
          d="M11.5 18L19.5 26"
          stroke="#E4E4E7"
          strokeWidth="2.6"
          strokeLinecap="round"
        />

        {/* THE SHARP DYNAMIC ELECTRIC SLASH CUTTING RIGHT THROUGH THE RUPEE */}
        <line
          x1="24"
          y1="4"
          x2="6"
          y2="28"
          stroke="#10B981"
          strokeWidth="3.2"
          strokeLinecap="round"
          className="drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]"
        />

        {/* Spark cut particle */}
        <circle cx="15" cy="16" r="1.5" fill="#34D399" className="animate-ping" />
      </svg>
    </div>
  );
}
