"use client";

import { PriceHistoryPoint } from "@/lib/api";
import { formatINR } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { TrendingDown } from "lucide-react";

interface PriceHistoryChartProps {
  history: PriceHistoryPoint[];
  currentPrice: number;
}

export function PriceHistoryChart({ history, currentPrice }: PriceHistoryChartProps) {
  if (!history || history.length === 0) return null;

  const minPrice = Math.min(...history.map((h) => h.price));
  const maxPrice = Math.max(...history.map((h) => h.price));

  return (
    <div className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-stone-100">
        <div>
          <h3 className="font-extrabold text-stone-900 text-base sm:text-lg flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-emerald-600" />
            <span>30-Day Price Trend</span>
          </h3>
          <p className="text-xs text-stone-500">
            Track price drops and sales across Indian retailers
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 font-semibold border border-emerald-100">
            Lowest: {formatINR(minPrice)}
          </div>
          <div className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-600 font-medium">
            Highest: {formatINR(maxPrice)}
          </div>
        </div>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#78716c" }} axisLine={false} tickLine={false} />
            <YAxis
              domain={["dataMin - 20", "dataMax + 20"]}
              tick={{ fontSize: 11, fill: "#78716c" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `₹${v}`}
            />
            <Tooltip
              formatter={(value: any) => [`₹${value}`, "Best Price"]}
              labelFormatter={(label) => `Timeline: ${label}`}
              contentStyle={{
                backgroundColor: "#1c1917",
                color: "#ffffff",
                borderRadius: "12px",
                border: "none",
                fontSize: "12px",
              }}
            />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#10b981", strokeWidth: 1.5, stroke: "#ffffff" }}
              activeDot={{ r: 6, fill: "#059669" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[11px] text-stone-400 text-center">
        💡 Pro-Tip: Prices update automatically when seasonal brand sales launch on Tira or Nykaa.
      </div>
    </div>
  );
}
