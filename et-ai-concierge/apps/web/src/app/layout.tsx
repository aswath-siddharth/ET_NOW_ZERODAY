import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "ET AI Concierge | Your Financial Life Navigator",
  description: "Navigate wealth creation with the intelligence of The Economic Times.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased text-foreground selection:bg-primary selection:text-primary-foreground",
          fontSans.variable
        )}
      >
        <div className="relative flex min-h-screen flex-col bg-[url('/bg-grid.svg')] bg-cover">
          {children}
        </div>
      </body>
    </html>
  );
}
