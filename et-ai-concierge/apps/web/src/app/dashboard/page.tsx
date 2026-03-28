"use client";

import { useState, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  ArrowUpRight, TrendingUp, Newspaper, Shield, CreditCard,
  ChevronRight, TrendingDown, Zap, BarChart3, Briefcase,
  Building2, Home, Calculator, MapPin, Smartphone, Loader2,
} from "lucide-react";

const NIFTY_DATA = [
  { time: "09:15", value: 22050 }, { time: "10:00", value: 22100 },
  { time: "11:00", value: 22080 }, { time: "12:00", value: 22150 },
  { time: "13:00", value: 22190 }, { time: "14:00", value: 22120 },
  { time: "15:30", value: 22200 },
];

const ICON_MAP: Record<string, React.ReactNode> = {
  Shield: <Shield className="w-5 h-5" />,
  TrendingUp: <TrendingUp className="w-5 h-5" />,
  TrendingDown: <TrendingDown className="w-5 h-5" />,
  Zap: <Zap className="w-5 h-5" />,
  BarChart3: <BarChart3 className="w-5 h-5" />,
  Newspaper: <Newspaper className="w-5 h-5" />,
  Smartphone: <Smartphone className="w-5 h-5" />,
  Briefcase: <Briefcase className="w-5 h-5" />,
  Building2: <Building2 className="w-5 h-5" />,
  Home: <Home className="w-5 h-5" />,
  Calculator: <Calculator className="w-5 h-5" />,
  MapPin: <MapPin className="w-5 h-5" />,
  CreditCard: <CreditCard className="w-5 h-5" />,
};

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [dashboardFeed, setDashboardFeed] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const handleInsightAction = (action: string) => {
    const actionRoutes: Record<string, string> = {
      "Adjust SIP": "/marketplace?filter=sip",
      "Invest Now": "/marketplace?filter=elss",
      Enroll: "/chat?query=ET+Young+Minds+Masterclass",
      Rebalance: "/chat?query=portfolio+rebalancing",
      "Consult Advisor": "/chat?query=wealth+management",
      "Compare Plans": "/chat?query=insurance+plans",
      "View Analysis": "/chat?query=stock+analysis",
      "View Charts": "/chat?query=technical+analysis",
      "Scan Strikes": "/chat?query=options+opportunities",
      "Compare Offers": "/chat?query=home+loan+comparison",
      Calculate: "/chat?query=emi+calculator",
      "View Trends": "/chat?query=property+market+trends",
      "Read Analysis": "/chat?query=corporate+governance",
      "View FD Rates": "/chat?query=fd+interest+rates",
    };
    const route = actionRoutes[action];
    if (route) router.push(route);
  };

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
    } else if (status === "authenticated" && (session as any)?.accessToken) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

      Promise.all([
        fetch(`${backendUrl}/api/profile`, {
          headers: { Authorization: `Bearer ${(session as any).accessToken}` },
        }).then((r) => r.json()),
        fetch(`${backendUrl}/api/dashboard/feed`, {
          headers: { Authorization: `Bearer ${(session as any).accessToken}` },
        }).then((r) => r.json()),
      ])
        .then(([profileData, feedData]) => {
          setProfile(profileData);
          setDashboardFeed(feedData);
          setLoading(false);
        })
        .catch((err) => {
          console.error(err);
          setProfile({ persona: "PERSONA_YOUNG_PROFESSIONAL" });
          setDashboardFeed({
            persona: "PERSONA_YOUNG_PROFESSIONAL",
            market_overview: { nifty: {}, sensex: {} },
            watchlist: [],
            news: [],
            recommended_insights: [],
            primary_tools: [],
          });
          setLoading(false);
        });
    }
  }, [session, status, router]);

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const personaName =
    (dashboardFeed?.persona || profile?.persona || "PERSONA_YOUNG_PROFESSIONAL")
      ?.replace("PERSONA_", "")
      .replace(/_/g, " ") || "Standard";
  const nifty = dashboardFeed?.market_overview?.nifty || {};
  const sensex = dashboardFeed?.market_overview?.sensex || {};
  const watchlist = dashboardFeed?.watchlist || [];
  const insights = dashboardFeed?.recommended_insights || [];
  const newsItems = dashboardFeed?.news || [];

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Welcome back, {session?.user?.name?.split(" ")[0] || "User"}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Persona:{" "}
              <span className="text-primary font-medium px-2 py-0.5 rounded-md bg-primary/10 text-xs uppercase tracking-wider">
                {personaName}
              </span>
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/onboarding">
              <button className="flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 rounded-xl text-sm font-medium hover:opacity-90 transition shadow-sm">
                Financial X-Ray <ArrowUpRight className="w-4 h-4" />
              </button>
            </Link>
          </div>
        </header>

        {/* Market Overview + Watchlist */}
        <div className="grid md:grid-cols-3 gap-5">
          {/* Market Chart */}
          <div className="md:col-span-2 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-primary" />
              Market Overview
            </h3>
            <div className="flex justify-between items-end border-b border-border/50 pb-4 mb-4">
              <div>
                <div className="text-2xl font-bold font-data text-foreground">
                  {nifty?.current_price?.toFixed(2) || "22,200.00"}
                </div>
                <div
                  className={`text-xs font-medium font-data ${
                    (nifty?.percent_change ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  NIFTY 50 &bull;{" "}
                  {(nifty?.percent_change ?? 0) >= 0 ? "+" : ""}
                  {nifty?.percent_change?.toFixed(2) || "0.00"}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold font-data text-foreground">
                  {sensex?.current_price?.toFixed(2) || "73,200.00"}
                </div>
                <div
                  className={`text-xs font-medium font-data ${
                    (sensex?.percent_change ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  SENSEX &bull;{" "}
                  {(sensex?.percent_change ?? 0) >= 0 ? "+" : ""}
                  {sensex?.percent_change?.toFixed(2) || "0.00"}%
                </div>
              </div>
            </div>
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={NIFTY_DATA}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="var(--border)"
                  />
                  <XAxis
                    dataKey="time"
                    stroke="var(--muted-foreground)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    fontFamily="JetBrains Mono"
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    stroke="var(--muted-foreground)"
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    fontFamily="JetBrains Mono"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--card)",
                      borderColor: "var(--border)",
                      borderRadius: "12px",
                      color: "var(--foreground)",
                      fontFamily: "JetBrains Mono",
                      fontSize: "12px",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Watchlist */}
          <div className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-6">
            <h3 className="text-sm font-semibold text-foreground mb-4">Watchlist</h3>
            <div className="space-y-3">
              {watchlist && watchlist.length > 0 ? (
                watchlist.map((stock: any, idx: number) => (
                  <div
                    key={idx}
                    className="flex justify-between items-center pb-3 border-b border-border/30 last:border-0 last:pb-0"
                  >
                    <div>
                      <div className="font-semibold text-sm text-foreground font-data">
                        {stock.symbol}
                      </div>
                      <div className="text-xs text-muted-foreground font-data">
                        ₹{stock.current_price?.toFixed(2) || "N/A"}
                      </div>
                    </div>
                    <div
                      className={`text-sm font-bold font-data ${
                        (stock.percent_change ?? 0) >= 0
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {(stock.percent_change ?? 0) >= 0 ? "+" : ""}
                      {stock.percent_change?.toFixed(2) || "0.00"}%
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No watchlist data available</p>
              )}
            </div>
          </div>
        </div>

        {/* Recommended Insights */}
        <div>
          <h3 className="text-lg font-semibold mb-4 text-foreground">
            Recommended for <span className="text-primary capitalize">{personaName}</span>
          </h3>
          <div className="grid md:grid-cols-3 gap-5">
            {insights && insights.length > 0 ? (
              insights.map((insight: any, idx: number) => (
                <div
                  key={idx}
                  onClick={() => handleInsightAction(insight.action)}
                  className="group cursor-pointer rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-5 hover:border-primary/30 hover:shadow-lg transition-all duration-300 flex flex-col h-full"
                >
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4 text-primary group-hover:scale-110 transition-transform duration-300">
                    {ICON_MAP[insight.icon] || <Newspaper className="w-5 h-5" />}
                  </div>
                  <h4 className="font-semibold text-foreground text-sm">{insight.title}</h4>
                  <p className="text-xs text-muted-foreground mt-2 line-clamp-2 leading-relaxed flex-1">
                    {insight.desc}
                  </p>
                  <div className="mt-4 flex items-center text-xs font-semibold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                    {insight.action} <ChevronRight className="w-3 h-3 ml-1" />
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-3 text-center py-8 text-muted-foreground text-sm">
                Loading personalized insights...
              </div>
            )}
          </div>
        </div>

        {/* Latest Market News */}
        {newsItems && newsItems.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-4 text-foreground">Latest Market News</h3>
            <div className="space-y-3">
              {newsItems.map((news: any, idx: number) => (
                <div
                  key={idx}
                  className="rounded-xl border border-border/50 bg-card/50 backdrop-blur-sm p-4 hover:border-primary/20 transition-all duration-200"
                >
                  <div className="flex items-start gap-4">
                    <Newspaper className="w-4 h-4 text-primary flex-shrink-0 mt-1" />
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-foreground text-sm line-clamp-2">
                        {news.headline}
                      </h4>
                      <a
                        href={news.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline mt-2 inline-block"
                      >
                        Read More →
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}