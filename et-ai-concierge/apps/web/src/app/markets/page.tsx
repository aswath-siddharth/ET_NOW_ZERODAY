"use client";

import { Building2, TrendingUp, AlertTriangle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function MarketsPage() {
  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-bold tracking-tight">Market Intelligence</h1>
          <p className="text-muted-foreground mt-1">Real-time data and technical signals</p>
        </header>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="NIFTY 50" value="22,200.00" change="+0.68%" isPositive />
          <MetricCard title="SENSEX" value="73,200.00" change="+0.66%" isPositive />
          <MetricCard title="MCX GOLD" value="₹62,450" change="-0.12%" isPositive={false} />
          <MetricCard title="USD/INR" value="82.85" change="+0.04%" isPositive />
        </div>

        <Card className="bg-gradient-to-br from-card to-card/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Technical Signals
            </CardTitle>
          </CardHeader>
          <CardContent>
             <div className="space-y-4">
               <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg border border-border/50">
                 <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded bg-emerald-500/20 text-emerald-500 flex items-center justify-center">
                     <TrendingUp className="w-5 h-5" />
                   </div>
                   <div>
                     <div className="font-semibold">NIFTY 50: Golden Cross</div>
                     <div className="text-sm text-muted-foreground">50-day SMA crossed above 200-day SMA. Bullish signal.</div>
                   </div>
                 </div>
                 <div className="text-right">
                   <div className="text-sm font-medium">Confidence</div>
                   <div className="text-emerald-500 font-bold">78%</div>
                 </div>
               </div>
               
               <div className="flex items-center justify-between p-4 bg-secondary/30 rounded-lg border border-border/50">
                 <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded bg-blue-500/20 text-blue-500 flex items-center justify-center">
                     <Building2 className="w-5 h-5" />
                   </div>
                   <div>
                     <div className="font-semibold">Auto Sector Rally</div>
                     <div className="text-sm text-muted-foreground">Tata Motors & M&M experiencing strong volume breakout.</div>
                   </div>
                 </div>
                 <div className="text-right">
                   <div className="text-sm font-medium">Strength</div>
                   <div className="text-blue-500 font-bold">Strong Buy</div>
                 </div>
               </div>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({ title, value, change, isPositive }: any) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-sm font-medium text-muted-foreground mb-2">{title}</div>
        <div className="text-2xl font-bold">{value}</div>
        <div className={`text-sm mt-1 font-medium ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
          {isPositive ? '↑' : '↓'} {change}
        </div>
      </CardContent>
    </Card>
  );
}
