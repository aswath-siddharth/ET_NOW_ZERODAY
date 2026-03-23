"use client";

import Link from "next/link";
import { ArrowRight, Mic, Sparkles, TrendingUp, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-border/40 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center font-bold text-white">
            ET
          </div>
          <span className="font-semibold text-lg tracking-tight">AI Concierge</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <Link href="#features" className="hover:text-foreground transition">Features</Link>
          <Link href="#how-it-works" className="hover:text-foreground transition">How it Works</Link>
        </nav>
        <div className="flex items-center gap-4">
          <Link href="/auth">
            <Button variant="ghost" className="hidden sm:inline-flex">Sign In</Button>
          </Link>
          <Link href="/auth">
            <Button className="rounded-full shadow-lg shadow-primary/20">
              Get Started
            </Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        {/* Hero Section */}
        <section className="relative px-6 py-24 md:py-32 flex flex-col items-center text-center overflow-hidden">
          {/* Background Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-primary/20 blur-[120px] rounded-full point-events-none" />
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/80 border border-border/50 text-xs font-medium text-muted-foreground mb-8"
          >
            <Sparkles className="w-4 h-4 text-primary" />
            <span>Powered by Llama 3 & Groq</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter max-w-4xl leading-[1.1]"
          >
            Your Financial Life <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-orange-500">
              Navigator
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl"
          >
            Experience the entire Economic Times ecosystem curated specifically for your goals, risk profile, and portfolio. Ask questions, compare loans, read premium insights, and track markets — all via natural conversation.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-10 flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto"
          >
            <Link href="/auth" className="w-full sm:w-auto">
              <Button size="lg" className="w-full rounded-full h-14 px-8 text-base shadow-xl shadow-primary/25 group">
                Build My Profile
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/chat" className="w-full sm:w-auto">
              <Button variant="outline" size="lg" className="w-full rounded-full h-14 px-8 text-base bg-background/50 backdrop-blur-sm border-border">
                <Mic className="mr-2 w-4 h-4" />
                Try Voice Assistant
              </Button>
            </Link>
          </motion.div>
        </section>

        {/* Feature Grid */}
        <section id="features" className="px-6 py-24 bg-card/30 border-t border-border/50">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight">One Assistant. Five Specialized Agents.</h2>
              <p className="mt-4 text-muted-foreground">Our Multi-Agent architecture routes your queries to the right expert.</p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              <FeatureCard 
                icon={<TrendingUp className="w-6 h-6 text-emerald-500" />}
                title="Market Intelligence"
                description="Real-time quotes, mutual fund NAVs, portfolio drift analysis, and personalized morning briefings."
              />
              <FeatureCard 
                icon={<Shield className="w-6 h-6 text-blue-500" />}
                title="ET Marketplace"
                description="Zero-bias intermediation for home loans, FDs, health insurance, and credit cards with approval probability."
              />
              <FeatureCard 
                icon={<Sparkles className="w-6 h-6 text-purple-500" />}
                title="Editorial Insights"
                description="Deep-dive into ET Prime exclusives, tailored entirely to your specific financial persona."
              />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="p-6 rounded-2xl border border-border/50 bg-background/50 backdrop-blur-sm hover:border-primary/50 transition-colors group">
      <div className="w-12 h-12 rounded-xl bg-secondary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground leading-relaxed">
        {description}
      </p>
    </div>
  );
}
