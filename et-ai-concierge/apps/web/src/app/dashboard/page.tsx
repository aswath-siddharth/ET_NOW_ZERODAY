"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";
import { ArrowUpRight, TrendingUp, Newspaper, Shield, CreditCard, ChevronRight } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

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

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
    } else if (status === "authenticated" && (session as any)?.accessToken) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      fetch(`${backendUrl}/api/profile`, {
        headers: {
          "Authorization": `Bearer ${(session as any).accessToken}`
        }
      })
      .then(r => r.json())
      .then(d => {
        setProfile(d);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setProfile({ persona: "PERSONA_ACTIVE_TRADER" }); // Mock fallback
        setLoading(false);
      });
    }
  }, [session, status, router]);

  if (status === "loading" || loading) {
    return <div className="flex items-center justify-center min-h-screen"><div className="animate-pulse text-zinc-400">Loading Profile...</div></div>;
  }

  return (
    <div className="min-h-screen bg-background border-t border-border p-4 md:p-8 pt-24">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome back, {session?.user?.name?.split(" ")[0] || "User"}</h1>
            <p className="text-muted-foreground mt-1">
              Your persona: <span className="text-red-700 font-medium px-2 py-0.5 rounded-full bg-red-50 text-sm">{profile?.persona?.replace("PERSONA_", "").replace(/_/g, " ") || "Standard"}</span>
            </p>
          </div>
          <Link href="/onboarding">
            <Button className="rounded-xl px-6 shadow-lg bg-red-600 hover:bg-red-700 text-white">
              Financial X-Ray <ArrowUpRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
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
                    <div className="text-3xl font-bold">22,200.00</div>
                    <div className="text-sm text-emerald-600 font-medium tracking-tight">NIFTY 50 • +150.00 (+0.68%)</div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-zinc-700">73,200.00</div>
                    <div className="text-sm text-emerald-600 font-medium tracking-tight">SENSEX • +480.00 (+0.66%)</div>
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
              <CardTitle className="text-lg">Portfolio Allocation</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col items-center justify-center">
              <div className="h-[180px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={PORTFOLIO_DATA} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                      {PORTFOLIO_DATA.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#fff', borderColor: '#eee', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="w-full space-y-3 mt-4">
                {PORTFOLIO_DATA.map(item => (
                  <div key={item.name} className="flex justify-between items-center text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-zinc-600 font-medium">{item.name}</span>
                    </div>
                    <div className="font-bold">{item.value}%</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recommended Actions */}
        <div>
           <h3 className="text-xl font-semibold mb-4 text-zinc-900 mt-6">Recommended Insights</h3>
           <div className="grid md:grid-cols-3 gap-6">
             <ActionCard icon={<Shield />} title="Home Loan Deals" desc="You have a 85% approval probability for SBI Home Loan at 8.40%." onClick={() => {}} />
             <ActionCard icon={<Newspaper />} title="ET Prime Exclusives" desc="Based on your interest in Gold, read 'GIFT City Volumes Plunge 40%'." onClick={() => {}} />
             <ActionCard icon={<CreditCard />} title="NPS Tax Planning" desc="Invest ₹50,000 to maximize your 80CCD(1B) deduction." onClick={() => {}} />
           </div>
        </div>
      </div>
    </div>
  );
}

function ActionCard({ icon, title, desc, onClick }: any) {
  return (
    <div onClick={onClick} className="group cursor-pointer rounded-2xl border border-zinc-200 bg-white p-5 hover:shadow-lg transition-all flex flex-col h-full hover:border-red-200">
      <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center mb-4 text-red-600 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="font-semibold text-zinc-900">{title}</h3>
      <p className="text-sm text-zinc-500 mt-2 line-clamp-2 leading-relaxed">{desc}</p>
      <div className="mt-auto pt-4 flex items-center text-xs font-semibold text-red-600 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
        Explore <ChevronRight className="w-3 h-3 ml-1" />
      </div>
    </div>
  );
}