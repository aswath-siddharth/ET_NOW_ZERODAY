"use client";

import { Building2, TrendingUp, AlertTriangle, TrendingDown, ArrowUp, ArrowDown } from "lucide-react";

const METRICS = [
  { title: "NIFTY 50", value: "22,200.00", change: "+0.68%", isPositive: true },
  { title: "SENSEX", value: "73,200.00", change: "+0.66%", isPositive: true },
  { title: "MCX GOLD", value: "₹62,450", change: "-0.12%", isPositive: false },
  { title: "USD/INR", value: "82.85", change: "+0.04%", isPositive: true },
];

const SIGNALS = [
  {
    icon: TrendingUp,
    iconColor: "text-emerald-400",
    iconBg: "bg-emerald-400/10",
    title: "NIFTY 50: Golden Cross",
    desc: "50-day SMA crossed above 200-day SMA. Bullish signal.",
    label: "Confidence",
    value: "78%",
    valueColor: "text-emerald-400",
  },
  {
    icon: Building2,
    iconColor: "text-blue-400",
    iconBg: "bg-blue-400/10",
    title: "Auto Sector Rally",
    desc: "Tata Motors & M&M experiencing strong volume breakout.",
    label: "Strength",
    value: "Strong Buy",
    valueColor: "text-blue-400",
  },
];

export default function MarketsPage() {
  return (
    <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
            Market Intelligence
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Real-time data and technical signals
          </p>
        </header>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {METRICS.map((metric) => (
            <div
              key={metric.title}
              className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-5"
            >
              <div className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wider">
                {metric.title}
              </div>
              <div className="text-xl font-bold font-data text-foreground">{metric.value}</div>
              <div
                className={`text-xs mt-1.5 font-medium font-data flex items-center gap-1 ${
                  metric.isPositive ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {metric.isPositive ? (
                  <ArrowUp className="w-3 h-3" />
                ) : (
                  <ArrowDown className="w-3 h-3" />
                )}
                {metric.change}
              </div>
            </div>
          ))}
        </div>

        {/* Technical Signals */}
        <div className="rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm">
          <div className="px-6 py-4 border-b border-border/50">
            <h3 className="font-semibold text-foreground flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Technical Signals
            </h3>
          </div>
          <div className="p-4 space-y-3">
            {SIGNALS.map((signal) => {
              const Icon = signal.icon;
              return (
                <div
                  key={signal.title}
                  className="flex items-center justify-between p-4 rounded-xl bg-secondary/30 border border-border/30"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl ${signal.iconBg} flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${signal.iconColor}`} />
                    </div>
                    <div>
                      <div className="font-semibold text-foreground text-sm">{signal.title}</div>
                      <div className="text-xs text-muted-foreground">{signal.desc}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-medium text-muted-foreground">{signal.label}</div>
                    <div className={`font-bold text-sm font-data ${signal.valueColor}`}>
                      {signal.value}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
