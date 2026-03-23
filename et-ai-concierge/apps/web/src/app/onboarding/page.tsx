"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, CheckCircle2, Loader2, Sparkles, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

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

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth");
    } else if (status === "authenticated" && (session as any)?.accessToken) {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      fetch(`${backendUrl}/api/onboarding/start`, {
        headers: {
          "Authorization": `Bearer ${(session as any).accessToken}`
        }
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to start onboarding");
          return res.json();
        })
        .then((data) => {
          setCurrentStep(data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [session, status, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !currentStep || submitting || !(session as any)?.accessToken) return;
    await submitAnswer(answer);
  };

  const handleOptionClick = async (option: string) => {
    if (!currentStep || submitting || !(session as any)?.accessToken) return;
    await submitAnswer(option);
  };

  const submitAnswer = async (currentAnswer: string) => {
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
          "Authorization": `Bearer ${(session as any).accessToken}`
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
        }, 4000);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <Loader2 className="w-8 h-8 animate-spin text-red-600" />
      </div>
    );
  }

  if (currentStep?.is_complete) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 pt-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full"
        >
          <Card className="p-8 text-center border-red-100 shadow-2xl shadow-red-100/50 rounded-2xl">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Profile Complete!</h2>
            <p className="text-muted-foreground mb-6">
              We've mapped your financial persona.
            </p>

            <div className="p-4 bg-red-50 rounded-xl border border-red-100 mb-6">
              <div className="text-sm text-zinc-500 mb-1">Your Persona</div>
              <div className="text-xl font-semibold text-red-600">{currentStep.persona?.replace("PERSONA_","").replace(/_/g, " ")}</div>
            </div>

            <p className="text-sm text-zinc-400 animate-pulse">
              Redirecting to your dashboard...
            </p>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto p-6 md:p-12 pt-24">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Financial X-Ray</h1>
        <Link href="/">
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <Home className="w-4 h-4" />
          </Button>
        </Link>
      </div>
      
      <div className="flex-1 overflow-y-auto mb-8 pr-4 space-y-6 scrollbar-hide">
        {/* History */}
        {history.map((item, i) => (
          <div key={i} className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-red-600" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-sm p-4 text-sm whitespace-pre-wrap border border-zinc-200 shadow-sm leading-relaxed text-zinc-800">
                {item.q}
              </div>
            </div>
            <div className="flex items-start justify-end gap-4">
              <div className="bg-red-600 text-white rounded-2xl rounded-tr-sm p-4 text-sm font-medium">
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
            className="flex items-start gap-4 pt-4"
          >
            <div className="w-8 h-8 rounded-full bg-red-50 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4 text-red-600" />
            </div>
            <div className="bg-white rounded-2xl rounded-tl-sm p-4 text-sm font-medium leading-relaxed shadow-sm border border-zinc-200 text-zinc-800">
              {currentStep?.question?.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-4" : ""}>{line}</p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        {submitting && (
          <div className="flex justify-end pt-4">
            <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
          </div>
        )}
      </div>

      <div className="sticky bottom-0 bg-background/80 backdrop-blur-xl pb-6 border-t border-zinc-100 pt-4">
        {currentStep?.options && currentStep.options.length > 0 ? (
          <div className="flex flex-wrap gap-2 justify-center mb-4">
            {currentStep.options.map((opt, idx) => (
              <Button 
                key={idx} 
                onClick={() => handleOptionClick(opt)}
                disabled={submitting}
                className="bg-white border text-zinc-700 hover:bg-red-50 relative hover:text-red-700 border-zinc-200 capitalize font-medium px-6 py-6 rounded-xl shadow-sm hover:border-red-200 hover:shadow-md transition-all ease-in-out duration-200"
                variant="outline"
              >
                {opt}
              </Button>
            ))}
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="relative">
            <Input
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer..."
              className="pr-14 h-14 bg-white border border-zinc-300 rounded-xl text-base shadow-sm focus-visible:ring-red-600 focus-visible:ring-offset-0 transition-shadow"
              disabled={submitting}
              autoFocus
            />
            <Button
              type="submit"
              size="icon"
              disabled={!answer.trim() || submitting}
              className="absolute right-2 top-2 h-10 w-10 rounded-lg bg-red-600 hover:bg-red-700 text-white shadow-sm"
            >
              <ArrowRight className="w-5 h-5" />
            </Button>
          </form>
        )}
        <div className="mt-3 text-center text-xs font-medium text-zinc-400">
          Step {(currentStep?.step ?? 0) + 1} of 9
        </div>
      </div>
    </div>
  );
}