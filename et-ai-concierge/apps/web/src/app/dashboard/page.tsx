"use client";

import { useState, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";
import { ArrowUpRight, TrendingUp, Newspaper, Shield, CreditCard, ChevronRight, TrendingDown, Zap, BarChart3, Briefcase, Building2, Home, Calculator, MapPin, Smartphone, LogOut } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { VoiceBriefingButton } from "@/components/VoiceBriefingButton";

// Mock Data
const NIFTY_DATA = [
  { time: "09:15", value: 22050 }, { time: "10:00", value: 22100 },
  { time: "11:00", value: 22080 }, { time: "12:00", value: 22150 },
  { time: "13:00", value: 22190 }, { time: "14:00", value: 22120 },
  { time: "15:30", value: 22200 },
];

const PORTFOLIO_DATA = [
  { name: "Equity", value: 65, color: "#e11d48" }, // primary
  { name: "Debt", value: 25, color: "#3b82f6" },   // blue
  { name: "Gold", value: 10, color: "#f59e0b" },   // amber
];

const ICON_MAP: Record<string, React.ReactNode> = {
  "Shield": <Shield className="w-5 h-5" />,
  "TrendingUp": <TrendingUp className="w-5 h-5" />,
  "TrendingDown": <TrendingDown className="w-5 h-5" />,
  "Zap": <Zap className="w-5 h-5" />,
  "BarChart3": <BarChart3 className="w-5 h-5" />,
  "Newspaper": <Newspaper className="w-5 h-5" />,
  "Smartphone": <Smartphone className="w-5 h-5" />,
  "Briefcase": <Briefcase className="w-5 h-5" />,
  "Building2": <Building2 className="w-5 h-5" />,
  "Home": <Home className="w-5 h-5" />,
  "Calculator": <Calculator className="w-5 h-5" />,
  "MapPin": <MapPin className="w-5 h-5" />,
  "CreditCard": <CreditCard className="w-5 h-5" />,
};

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [dashboardFeed, setDashboardFeed] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const handleSignOut = async () => {
    await signOut({ redirect: false });
    router.push("/");
  };

  const handleInsightAction = (action: string) => {
    // Map action labels to routes
    const actionRoutes: Record<string, string> = {
      "Adjust SIP": "/marketplace?filter=sip",
      "Invest Now": "/marketplace?filter=elss",
      "Enroll": "/chat?query=ET+Young+Minds+Masterclass",
      "Rebalance": "/chat?query=portfolio+rebalancing",
      "Consult Advisor": "/chat?query=wealth+management",
      "Compare Plans": "/chat?query=insurance+plans",
      "View Analysis": "/chat?query=stock+analysis",
      "View Charts": "/chat?query=technical+analysis",
      "Scan Strikes": "/chat?query=options+opportunities",
      "Compare Offers": "/chat?query=home+loan+comparison",
      "Calculate": "/chat?query=emi+calculator",
      "View Trends": "/chat?query=property+market+trends",
      "Read Analysis": "/chat?query=corporate+governance",
    };
    
    const route = actionRoutes[action];
    if (route) {
      router.push(route);
    }
  };

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
    } else if (status === "authenticated" && (session as any)?.accessToken) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      
      // Fetch both profile and dashboard feed
      Promise.all([
        fetch(`${backendUrl}/api/profile`, {
          headers: {
            "Authorization": `Bearer ${(session as any).accessToken}`
          }
        }).then(r => r.json()),
        fetch(`${backendUrl}/api/dashboard/feed`, {
          headers: {
            "Authorization": `Bearer ${(session as any).accessToken}`
          }
        }).then(r => r.json())
      ])
      .then(([profileData, feedData]) => {
        setProfile(profileData);
        setDashboardFeed(feedData);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setProfile({ persona: "PERSONA_YOUNG_PROFESSIONAL" }); // Mock fallback
        setDashboardFeed({
          persona: "PERSONA_YOUNG_PROFESSIONAL",
          market_overview: { nifty: {}, sensex: {} },
          watchlist: [],
          news: [],
          recommended_insights: [],
          primary_tools: []
        });
        setLoading(false);
      });
    }
  }, [session, status, router]);

  if (status === "loading" || loading) {
    return <div className="flex items-center justify-center min-h-screen"><div className="animate-pulse text-zinc-400">Loading Dashboard...</div></div>;
  }

  const personaName = (dashboardFeed?.persona || profile?.persona || "PERSONA_YOUNG_PROFESSIONAL")
    ?.replace("PERSONA_", "")
    .replace(/_/g, " ") || "Standard";
  const nifty = dashboardFeed?.market_overview?.nifty || {};
  const sensex = dashboardFeed?.market_overview?.sensex || {};
  const watchlist = dashboardFeed?.watchlist || [];
  const insights = dashboardFeed?.recommended_insights || [];
  const newsItems = dashboardFeed?.news || [];

  return (
    <div className="min-h-screen bg-background border-t border-border p-4 md:p-8 pt-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome back, {session?.user?.name?.split(" ")[0] || "User"}</h1>
            <p className="text-muted-foreground mt-1">
              Your persona: <span className="text-red-700 font-medium px-2 py-0.5 rounded-full bg-red-50 text-sm">{personaName}</span>
            </p>
          </div>
          <div className="flex flex-col gap-3">
            <div className="flex gap-3">
              <Link href="/">
                <Button variant="outline" className="rounded-xl px-6 shadow-sm border-border/50 hover:bg-secondary">
                  <Home className="mr-2 w-4 h-4" />
                  Home
                </Button>
              </Link>
              <Link href="/onboarding">
                <Button className="rounded-xl px-6 shadow-lg bg-red-600 hover:bg-red-700 text-white">
                  Financial X-Ray <ArrowUpRight className="ml-2 w-4 h-4" />
                </Button>
              </Link>
              <Button 
                onClick={handleSignOut}
                className="rounded-xl px-6 shadow-lg bg-zinc-700 hover:bg-zinc-800 text-white"
              >
                Sign Out <LogOut className="ml-2 w-4 h-4" />
              </Button>
            </div>
            <VoiceBriefingButton className="rounded-xl px-6 shadow-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white w-full" />
          </div>
        </header>

        {/* Top Widgets Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="md:col-span-2 shadow-sm rounded-xl">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="w-5 h-5 text-red-600" />
                Market Overview
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-end border-b pb-4">
                  <div>
                    <div className="text-3xl font-bold">{nifty?.current_price?.toFixed(2) || "22,200.00"}</div>
                    <div className={`text-sm font-medium tracking-tight ${nifty?.percent_change >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      NIFTY 50 • {nifty?.percent_change >= 0 ? '+' : ''}{nifty?.percent_change?.toFixed(2) || "0.00"}%
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-zinc-700">{sensex?.current_price?.toFixed(2) || "73,200.00"}</div>
                    <div className={`text-sm font-medium tracking-tight ${sensex?.percent_change >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      SENSEX • {sensex?.percent_change >= 0 ? '+' : ''}{sensex?.percent_change?.toFixed(2) || "0.00"}%
                    </div>
                  </div>
                </div>
                <div className="h-[200px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={NIFTY_DATA}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                      <XAxis dataKey="time" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis domain={['auto', 'auto']} stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#eee', borderRadius: '8px' }} />
                      <Line type="monotone" dataKey="value" stroke="#e11d48" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm rounded-xl">
            <CardHeader>
              <CardTitle className="text-lg">Watchlist</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {watchlist && watchlist.length > 0 ? (
                watchlist.map((stock: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center border-b pb-2 last:border-0">
                    <div>
                      <div className="font-semibold text-sm text-white">{stock.symbol}</div>
                      <div className="text-xs text-zinc-500">₹{stock.current_price?.toFixed(2) || "N/A"}</div>
                    </div>
                    <div className={`text-sm font-bold ${stock.percent_change >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {stock.percent_change >= 0 ? '+' : ''}{stock.percent_change?.toFixed(2) || "0.00"}%
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-zinc-500">No watchlist data available</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recommended Actions */}
        <div>
           <h3 className="text-xl font-semibold mb-4 text-zinc-900 mt-6">Recommended Insights for {personaName}</h3>
           <div className="grid md:grid-cols-3 gap-6">
             {insights && insights.length > 0 ? (
               insights.map((insight: any, idx: number) => (
                 <ActionCard 
                   key={idx}
                   icon={ICON_MAP[insight.icon] || <Newspaper />} 
                   title={insight.title} 
                   desc={insight.desc} 
                   action={insight.action}
                   onClick={() => handleInsightAction(insight.action)} 
                 />
               ))
             ) : (
               <div className="col-span-3 text-center py-8 text-zinc-500">
                 Loading personalized insights...
               </div>
             )}
           </div>
        </div>

        {/* Latest Market News */}
        {newsItems && newsItems.length > 0 && (
          <div>
            <h3 className="text-xl font-semibold mb-4 text-white">Latest Market News</h3>
            <div className="space-y-3">
              {newsItems.map((news: any, idx: number) => (
                <Card key={idx} className="shadow-sm rounded-xl hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="pt-4">
                    <div className="flex items-start gap-4">
                      <Newspaper className="w-5 h-5 text-red-600 flex-shrink-0 mt-1" />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-white line-clamp-2">{news.headline}</h4>
                        <a href={news.url} target="_blank" rel="noopener noreferrer" className="text-xs text-red-600 hover:underline mt-2 inline-block">
                          Read More →
                        </a>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ActionCard({ icon, title, desc, action, onClick }: any) {
  return (
    <div onClick={onClick} className="group cursor-pointer rounded-2xl border border-zinc-200 bg-white p-5 hover:shadow-lg transition-all flex flex-col h-full hover:border-red-200">
      <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center mb-4 text-red-600 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="font-semibold text-zinc-900">{title}</h3>
      <p className="text-sm text-zinc-500 mt-2 line-clamp-2 leading-relaxed">{desc}</p>
      <div className="mt-auto pt-4 flex items-center text-xs font-semibold text-red-600 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
        {action} <ChevronRight className="w-3 h-3 ml-1" />
      </div>
    </div>
  );
}