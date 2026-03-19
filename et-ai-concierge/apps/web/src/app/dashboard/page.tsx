"use client";

import { useState, useEffect } from "react";
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
  { name: 'Equity', value: 65, color: '#e11d48' }, // primary
  { name: 'Debt', value: 25, color: '#3b82f6' },   // blue
  { name: 'Gold', value: 10, color: '#f59e0b' },   // amber
];

export default function DashboardPage() {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/profile/test_user_123")
      .then(r => r.json())
      .then(d => setProfile(d))
      .catch(() => {
        // Mock fallback if backend offline
        setProfile({ persona: "PERSONA_ACTIVE_TRADER" });
      });
  }, []);

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
            <p className="text-muted-foreground mt-1">
              Your persona: <span className="text-primary font-medium">{profile?.persona?.replace("PERSONA_", "").replace("_", " ")}</span>
            </p>
          </div>
          <Link href="/chat">
            <Button className="rounded-full px-6 shadow-lg shadow-primary/20">
              Open My Navigator <ArrowUpRight className="ml-2 w-4 h-4" />
            </Button>
          </Link>
        </header>

        {/* Top Widgets Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Briefing Card */}
          <Card className="md:col-span-2 bg-gradient-to-br from-card to-card/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-primary" />
                Morning Briefing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-end border-b border-border/50 pb-4">
                  <div>
                    <div className="text-3xl font-bold">22,200.00</div>
                    <div className="text-sm text-emerald-500 font-medium">NIFTY 50 • +150.00 (+0.68%)</div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-muted-foreground">73,200.00</div>
                    <div className="text-sm text-emerald-500 font-medium">SENSEX • +480.00 (+0.66%)</div>
                  </div>
                </div>
                <div className="h-[200px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={NIFTY_DATA}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                      <XAxis dataKey="time" stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis domain={['auto', 'auto']} stroke="#888" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#111', borderColor: '#333', borderRadius: '8px' }} />
                      <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Portfolio Allocation */}
          <Card>
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
                    <Tooltip contentStyle={{ backgroundColor: '#111', borderColor: '#333', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="w-full space-y-2 mt-4">
                {PORTFOLIO_DATA.map(item => (
                  <div key={item.name} className="flex justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      {item.name}
                    </div>
                    <div className="font-medium">{item.value}%</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <ActionCard 
            icon={<Shield />} title="Home Loan Deals" 
            desc="You have a 85% approval probability for SBI Home Loan at 8.40%."
            onClick={() => {}}
          />
          <ActionCard 
            icon={<Newspaper />} title="ET Prime Exclusives" 
            desc="Based on your interest in Gold, read 'GIFT City Volumes Plunge 40%'."
            onClick={() => {}}
          />
          <ActionCard 
            icon={<CreditCard />} title="NPS Tax Planning" 
            desc="Invest ₹50,000 to maximize your 80CCD(1B) deduction."
            onClick={() => {}}
          />
        </div>

      </div>
    </div>
  );
}

function ActionCard({ icon, title, desc, onClick }: any) {
  return (
    <div onClick={onClick} className="group cursor-pointer rounded-2xl border border-border/50 bg-card/40 p-5 hover:bg-card hover:border-primary/40 transition-all flex flex-col h-full">
      <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center mb-4 text-primary group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{desc}</p>
      <div className="mt-auto pt-4 flex items-center text-xs font-medium text-primary mt-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
        Explore <ChevronRight className="w-3 h-3 ml-1" />
      </div>
    </div>
  );
}
