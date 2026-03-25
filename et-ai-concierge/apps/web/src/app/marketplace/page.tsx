"use client";

import { useRouter } from "next/navigation";
import { Shield, Home, CreditCard, PiggyBank } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function MarketplacePage() {
  const router = useRouter();

  const handleProductAction = (action: string) => {
    // Map CTA to chat queries
    const actionRoutes: Record<string, string> = {
      "Compare Loans": "/chat?query=home+loan+comparison",
      "View Plans": "/chat?query=health+insurance+plans",
      "Calculate Returns": "/chat?query=sovereign+gold+bonds+calculator",
      "Apply Now": "/chat?query=premium+credit+card+application",
    };
    
    const route = actionRoutes[action];
    if (route) {
      router.push(route);
    }
  };

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-bold tracking-tight">ET Marketplace</h1>
          <p className="text-muted-foreground mt-1">Personalized financial products based on your persona</p>
        </header>

        <div className="grid md:grid-cols-2 gap-6">
          <ProductCard 
            icon={<Home className="w-6 h-6 text-blue-500" />}
            title="Home Loans"
            match="85% Approval Match"
            desc="Based on your salaried profile, SBI offers the best rate at 8.40%."
            cta="Compare Loans"
            onClick={() => handleProductAction("Compare Loans")}
          />
          <ProductCard 
            icon={<Shield className="w-6 h-6 text-emerald-500" />}
            title="Health Insurance"
            match="Coverage Gap Detected"
            desc="Medical inflation is 14%. Upgrade to ₹10L cover for ₹12,500/yr."
            cta="View Plans"
            onClick={() => handleProductAction("View Plans")}
          />
          <ProductCard 
            icon={<PiggyBank className="w-6 h-6 text-amber-500" />}
            title="Sovereign Gold Bonds"
            match="Tax-Free Returns"
            desc="Earn 2.5% extra interest over gold price appreciation. Next tranche in April."
            cta="Calculate Returns"
            onClick={() => handleProductAction("Calculate Returns")}
          />
          <ProductCard 
            icon={<CreditCard className="w-6 h-6 text-purple-500" />}
            title="Premium Credit Cards"
            match="High Spending Match"
            desc="Get 8 lounge visits and 2% unlimited cashback with ICICI Times Black."
            cta="Apply Now"
            onClick={() => handleProductAction("Apply Now")}
          />
        </div>
      </div>
    </div>
  );
}

function ProductCard({ icon, title, match, desc, cta, onClick }: any) {
  return (
    <Card className="flex flex-col h-full bg-card/40 hover:bg-card/80 transition-colors border-border/50">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mb-4">
            {icon}
          </div>
          <div className="text-xs font-semibold px-2 py-1 bg-primary/10 text-primary rounded-full">
            {match}
          </div>
        </div>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <p className="text-muted-foreground text-sm flex-1">{desc}</p>
        <Button 
          onClick={onClick}
          className="w-full mt-6" 
          variant="outline"
        >
          {cta}
        </Button>
      </CardContent>
    </Card>
  );
}
