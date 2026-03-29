"use client";

import Link from "next/link";
import {
  ArrowRight,
  Mic,
  Sparkles,
  TrendingUp,
  Shield,
  Newspaper,
  ScanLine,
  BarChart3,
  MessageSquare,
  ChevronRight,
} from "lucide-react";
import { motion } from "framer-motion";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.1, ease: [0.22, 1, 0.36, 1] },
  }),
};

const FEATURES = [
  {
    icon: TrendingUp,
    title: "Market Intelligence",
    description: "Real-time quotes, portfolio drift analysis, and personalized morning briefings powered by live data.",
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
  },
  {
    icon: Shield,
    title: "ET Marketplace",
    description: "Zero-bias intermediation for home loans, FDs, health insurance, and credit cards with approval probability.",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    icon: Newspaper,
    title: "Editorial Insights",
    description: "Deep-dive into ET Prime exclusives, tailored entirely to your specific financial persona.",
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
  {
    icon: ScanLine,
    title: "Financial X-Ray",
    description: "AI-powered profiling that maps your persona, risk appetite, and goals through conversational analysis.",
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    icon: Mic,
    title: "Voice Assistant",
    description: "Hands-free financial navigation with natural language understanding and text-to-speech responses.",
    color: "text-rose-400",
    bg: "bg-rose-400/10",
  },
  {
    icon: BarChart3,
    title: "Portfolio Analytics",
    description: "Watchlist tracking, sector allocation analysis, and rebalancing recommendations based on your persona.",
    color: "text-amber-400",
    bg: "bg-amber-400/10",
  },
];

const STATS = [
  { value: "82+", label: "ET Resources" },
  { value: "7", label: "AI Agents" },
  { value: "5", label: "User Personas" },
  { value: "24/7", label: "Available" },
];

const STEPS = [
  {
    num: "01",
    title: "Complete Your Financial X-Ray",
    desc: "Answer a few conversational questions. Our AI maps your risk profile, goals, and financial persona.",
  },
  {
    num: "02",
    title: "Get Personalized Intelligence",
    desc: "Receive curated market insights, product recommendations, and editorial content tailored to you.",
  },
  {
    num: "03",
    title: "Navigate with Confidence",
    desc: "Ask questions, compare products, track markets, and make informed decisions — all via natural conversation.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* ─── Hero ─────────────────────────────────── */}
      <section className="relative px-6 pt-32 pb-24 md:pt-44 md:pb-32 flex flex-col items-center text-center overflow-hidden">
        {/* Accent glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] rounded-full pointer-events-none opacity-60"
          style={{ background: "radial-gradient(ellipse, rgba(212,168,83,0.08) 0%, transparent 70%)" }}
        />

        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={0}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-xs font-medium text-primary mb-8"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Powered by Multi-Agent AI</span>
        </motion.div>

        <motion.h1
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={1}
          className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter max-w-4xl leading-[1.05]"
        >
          Your Financial Life{" "}
          <br className="hidden sm:block" />
          <span className="text-gradient-gold">Navigator</span>
        </motion.h1>

        <motion.p
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={2}
          className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed"
        >
          Experience the entire Economic Times ecosystem curated for your goals,
          risk profile, and portfolio. Ask questions, compare products, and
          track markets — all through natural conversation.
        </motion.p>

        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          custom={3}
          className="mt-10 flex flex-col sm:flex-row items-center gap-4"
        >
          <Link href="/auth">
            <button className="flex items-center gap-2 bg-primary text-primary-foreground px-8 py-3.5 rounded-xl text-sm font-semibold shadow-lg hover:opacity-90 transition group"
              style={{ boxShadow: "0 8px 32px rgba(212,168,83,0.2)" }}
            >
              Get Started
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          <Link href="/chat">
            <button className="flex items-center gap-2 px-8 py-3.5 rounded-xl text-sm font-semibold border border-border hover:bg-accent transition text-foreground">
              <MessageSquare className="w-4 h-4" />
              Try the Concierge
            </button>
          </Link>
        </motion.div>
      </section>

      {/* ─── Stats ────────────────────────────────── */}
      <section className="px-6 py-12 border-t border-border/50">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              custom={i}
              className="text-center"
            >
              <div className="text-3xl md:text-4xl font-bold text-gradient-gold font-data">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ─── Features ─────────────────────────────── */}
      <section className="px-6 py-24 border-t border-border/50">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={0}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              One Concierge.{" "}
              <span className="text-gradient-gold">Seven Specialized Agents.</span>
            </h2>
            <p className="mt-4 text-muted-foreground max-w-xl mx-auto">
              Our multi-agent architecture routes every query to the right expert
              — market data, editorial, marketplace, or profiling.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  variants={fadeUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  custom={i}
                  className="group p-6 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/30 hover:shadow-lg transition-all duration-300 cursor-default"
                  style={{ transition: "border-color 0.3s, box-shadow 0.3s" }}
                >
                  <div className={`w-11 h-11 rounded-xl ${feature.bg} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                    <Icon className={`w-5 h-5 ${feature.color}`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2 text-foreground">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─────────────────────────── */}
      <section className="px-6 py-24 border-t border-border/50">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            custom={0}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              How It <span className="text-gradient-gold">Works</span>
            </h2>
          </motion.div>

          <div className="space-y-8">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.num}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                custom={i}
                className="flex gap-6 items-start group"
              >
                <div className="shrink-0 w-14 h-14 rounded-2xl border border-primary/20 bg-primary/5 flex items-center justify-center font-data text-primary text-lg font-bold group-hover:bg-primary/10 transition">
                  {step.num}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-1">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────── */}
      <section className="px-6 py-24 border-t border-border/50">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          custom={0}
          className="max-w-2xl mx-auto text-center"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">
            Start Your Financial Journey
          </h2>
          <p className="text-muted-foreground mb-8">
            Complete your Financial X-Ray and unlock personalized market intelligence,
            curated editorial insights, and smart product recommendations.
          </p>
          <Link href="/auth">
            <button
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-8 py-3.5 rounded-xl text-sm font-semibold hover:opacity-90 transition group"
              style={{ boxShadow: "0 8px 32px rgba(212,168,83,0.2)" }}
            >
              Build My Profile
              <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
        </motion.div>
      </section>

      {/* ─── Footer ───────────────────────────────── */}
      <footer className="px-6 py-8 border-t border-border/50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-primary flex items-center justify-center">
              <span className="text-[8px] font-bold text-primary-foreground">ET</span>
            </div>
            <span>ET AI Concierge &copy; {new Date().getFullYear()}</span>
          </div>
          <div className="flex gap-6">
            <Link href="#" className="hover:text-foreground transition">Terms</Link>
            <Link href="#" className="hover:text-foreground transition">Privacy</Link>
            <Link href="#" className="hover:text-foreground transition">Support</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
