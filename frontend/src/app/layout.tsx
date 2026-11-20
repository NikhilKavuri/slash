import type { Metadata } from "next";
import { Inter, Caveat, Playfair_Display } from "next/font/google";
import "./globals.css";
import { SnackbarProvider } from "@/components/Snackbar";

// Inter: The industry standard for razor-sharp product and UI readability
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

// Caveat: Stylish, playful cursive handwriting for personal touches & callouts
const caveat = Caveat({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-cursive",
  display: "swap",
});

// Playfair Display: High-fashion, luxury editorial italic cursive
const playfair = Playfair_Display({
  subsets: ["latin"],
  style: ["normal", "italic"],
  variable: "--font-editorial",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Slash — Find the Lowest Price on Any Product",
  description:
    "Paste any product link or search term. We compare prices across Amazon, Nykaa, Tira, Blinkit & Zepto, with active checkout coupon codes to find the lowest cart price.",
  keywords: [
    "price comparison",
    "lowest price finder",
    "amazon vs flipkart",
    "nykaa coupons",
    "tira discount codes",
    "slash price",
  ],
  openGraph: {
    title: "Slash — Find the Lowest Price Across Stores",
    description: "Compare live prices, active checkout coupon codes, and verified reviews side-by-side.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${caveat.variable} ${playfair.variable}`}>
      <body className="font-sans antialiased bg-[#FAFAFA] text-zinc-900 selection:bg-zinc-200">
        <SnackbarProvider>{children}</SnackbarProvider>
      </body>
    </html>
  );
}
