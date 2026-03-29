"use client";

import { useState, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, CheckCircle2, Loader2, Sparkles } from "lucide-react";

type OnboardingStep = {
  step: number;
  question?: string;
  options?: string[];
  is_complete: boolean;
  persona?: string;
  recommended_tools?: Array<{ name: string; description: string }>;
};

export default function OnboardingPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [currentStep, setCurrentStep] = useState<OnboardingStep | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<{ q: string; a: string }[]>([]);
  const startedRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when history changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history, currentStep]);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
      return;
    }
    if (status === "authenticated" && (session as any)?.accessToken && !startedRef.current) {
      startedRef.current = true;
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      fetch(`${backendUrl}/api/onboarding/start`, {
        headers: {
          Authorization: `Bearer ${(session as any).accessToken}`,
        },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to start onboarding");
          return res.json();
        })
        .then((data) => {
          setCurrentStep(data);
          setLoading(false);

          // If already complete, redirect
          if (data.is_complete) {
            setTimeout(() => router.push("/dashboard"), 2000);
          }
        })
        .catch((err) => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [session, status, router]);

  const submitAnswer = async (currentAnswer: string) => {
    if (!currentStep || submitting || !(session as any)?.accessToken) return;
    setSubmitting(true);
    const prevQuestion = currentStep?.question || "";

    setHistory((prev) => [...prev, { q: prevQuestion, a: currentAnswer }]);
    setAnswer("");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${backendUrl}/api/onboarding/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${(session as any).accessToken}`,
        },
        body: JSON.stringify({
          user_id: session?.user?.id || "app_user",
          step: currentStep?.step,
          answer: currentAnswer,
        }),
      });
      const data = await res.json();
      setCurrentStep(data);

      if (data.is_complete) {
        setTimeout(() => {
          router.push("/dashboard");
        }, 3000);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    await submitAnswer(answer);
  };

  const handleOptionClick = async (option: string) => {
    await submitAnswer(option);
  };

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // ─── Onboarding Complete ───────────────────────
  if (currentStep?.is_complete) {
    const personaDisplay = currentStep.persona
      ?.replace("PERSONA_", "")
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());

    return (
      <div className="min-h-screen flex items-center justify-center p-6 pt-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full"
        >
          <div className="p-8 text-center rounded-2xl glass-card border border-primary/20 shadow-2xl">
            <div
              className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6"
              style={{ boxShadow: "0 0 30px rgba(212,168,83,0.15)" }}
            >
              <CheckCircle2 className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-2xl font-bold mb-2 text-foreground">Profile Complete!</h2>
            <p className="text-muted-foreground mb-6">
              We&apos;ve mapped your financial persona.
            </p>

            <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 mb-6">
              <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-medium">
                Your Persona
              </div>
              <div className="text-xl font-semibold text-primary">{personaDisplay}</div>
            </div>

            {currentStep.recommended_tools && currentStep.recommended_tools.length > 0 && (
              <div className="mb-6">
                <div className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">
                  Recommended for you
                </div>
                <div className="flex flex-wrap gap-2 justify-center">
                  {currentStep.recommended_tools.map((tool) => (
                    <span
                      key={tool.name}
                      className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20"
                    >
                      {tool.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <p className="text-sm text-muted-foreground animate-pulse">
              Redirecting to your dashboard...
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  // ─── Progress Bar ──────────────────────────────
  const totalSteps = 9;
  const currentStepNum = (currentStep?.step ?? 0) + 1;
  const progress = Math.min((currentStepNum / totalSteps) * 100, 100);

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto p-6 md:p-12 pt-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-primary" />
          Financial X-Ray
        </h1>
        <span className="text-xs text-muted-foreground font-data">
          {currentStepNum} / {totalSteps}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1 rounded-full bg-secondary mb-8 overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          style={{ boxShadow: "0 0 12px rgba(212,168,83,0.4)" }}
        />
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto mb-8 pr-2 space-y-5 scrollbar-hide">
        {history.map((item, i) => (
          <div key={i} className="space-y-3">
            {/* Assistant Question */}
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
              </div>
              <div className="rounded-2xl rounded-tl-md px-4 py-3 text-sm whitespace-pre-wrap glass-card border border-border/50 leading-relaxed text-foreground max-w-[85%]">
                {item.q}
              </div>
            </div>
            {/* User Answer */}
            <div className="flex items-start justify-end gap-3">
              <div className="rounded-2xl rounded-tr-md px-4 py-3 text-sm font-medium bg-primary text-primary-foreground max-w-[85%]">
                {item.a}
              </div>
            </div>
          </div>
        ))}

        {/* Current Question */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep?.step}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 pt-2"
          >
            <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
            </div>
            <div className="rounded-2xl rounded-tl-md px-4 py-3 text-sm font-medium leading-relaxed glass-card border border-border/50 text-foreground max-w-[85%]">
              {currentStep?.question?.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-3" : ""}>
                  {line}
                </p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        <div ref={scrollRef} />
      </div>

      {/* Input Area */}
      <div className="sticky bottom-0 bg-background/80 backdrop-blur-xl pb-6 border-t border-border/50 pt-4">
        {currentStep?.options && currentStep.options.length > 0 ? (
          <div className="flex flex-wrap gap-2 justify-center mb-4">
            {currentStep.options.map((opt, idx) => (
              <button
                key={idx}
                onClick={() => handleOptionClick(opt)}
                disabled={submitting}
                className="px-5 py-2.5 rounded-xl text-sm font-medium border border-border/50 bg-card hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all duration-200 text-foreground disabled:opacity-50 capitalize"
              >
                {opt}
              </button>
            ))}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="relative">
            <input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer..."
              className="w-full h-14 px-5 pr-14 rounded-xl bg-card border border-border/50 text-base text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition"
              disabled={submitting}
              autoFocus
            />
            <button
              type="submit"
              disabled={!answer.trim() || submitting}
              className="absolute right-2 top-2 h-10 w-10 rounded-lg bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 transition disabled:opacity-30"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>
        )}
      </div>
    </div>
  );
}