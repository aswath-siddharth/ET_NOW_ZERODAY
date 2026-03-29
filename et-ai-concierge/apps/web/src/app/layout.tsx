import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { FloatingConcierge } from "@/components/FloatingConcierge";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "ET AI Concierge | Your Financial Life Navigator",
  description:
    "Navigate wealth creation with the intelligence of The Economic Times. AI-powered financial concierge with personalized insights, market intelligence, and smart recommendations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased text-foreground noise-overlay">
        <Providers>
          <div className="mesh-gradient" aria-hidden="true" />
          <div className="relative flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <FloatingConcierge />
          </div>
        </Providers>
      </body>
    </html>
  );
}
