"use client";

import { useRouter } from "next/navigation";
import { Shield, Home, CreditCard, PiggyBank, ChevronRight } from "lucide-react";

const PRODUCTS = [
  {
    icon: Home,
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    title: "Home Loans",
    match: "85% Approval Match",
    desc: "Based on your salaried profile, SBI offers the best rate at 8.40%.",
    cta: "Compare Loans",
    route: "/chat?query=home+loan+comparison",
  },
  {
    icon: Shield,
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
    title: "Health Insurance",
    match: "Coverage Gap Detected",
    desc: "Medical inflation is 14%. Upgrade to ₹10L cover for ₹12,500/yr.",
    cta: "View Plans",
    route: "/chat?query=health+insurance+plans",
  },
  {
    icon: PiggyBank,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
    title: "Sovereign Gold Bonds",
    match: "Tax-Free Returns",
    desc: "Earn 2.5% extra interest over gold price appreciation. Next tranche in April.",
    cta: "Calculate Returns",
    route: "/chat?query=sovereign+gold+bonds+calculator",
  },
  {
    icon: CreditCard,
    color: "text-purple-400",
    bg: "bg-purple-400/10",
    title: "Premium Credit Cards",
    match: "High Spending Match",
    desc: "Get 8 lounge visits and 2% unlimited cashback with ICICI Times Black.",
    cta: "Apply Now",
    route: "/chat?query=premium+credit+card+application",
  },
];

export default function MarketplacePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
            ET Marketplace
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Personalized financial products based on your persona
          </p>
        </header>

        <div className="grid md:grid-cols-2 gap-5">
          {PRODUCTS.map((product) => {
            const Icon = product.icon;
            return (
              <div
                key={product.title}
                onClick={() => router.push(product.route)}
                className="group cursor-pointer rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm p-6 hover:border-primary/30 hover:shadow-lg transition-all duration-300 flex flex-col h-full"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl ${product.bg} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className={`w-6 h-6 ${product.color}`} />
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 bg-primary/10 text-primary rounded-full">
                    {product.match}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">{product.title}</h3>
                <p className="text-sm text-muted-foreground flex-1 leading-relaxed">
                  {product.desc}
                </p>
                <div className="mt-5 flex items-center text-sm font-semibold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                  {product.cta} <ChevronRight className="w-4 h-4 ml-1" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
