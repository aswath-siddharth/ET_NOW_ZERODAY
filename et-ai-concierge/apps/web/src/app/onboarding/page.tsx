"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type OnboardingStep = {
  step: number;
  question?: string;
  is_complete: boolean;
  persona?: string;
  recommended_tools?: Array<{ name: string; description: string }>;
};

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<OnboardingStep | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState<{ q: string; a: string }[]>([]);

  useEffect(() => {
    // Start flow
    fetch("http://localhost:8000/api/onboarding/start")
      .then((res) => res.json())
      .then((data) => {
        setCurrentStep(data);
        setLoading(false);
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !currentStep || submitting) return;

    setSubmitting(true);
    const prevQuestion = currentStep.question || "";
    const currentAnswer = answer;
    
    setHistory((prev) => [...prev, { q: prevQuestion, a: currentAnswer }]);
    setAnswer("");

    try {
      const res = await fetch("http://localhost:8000/api/onboarding/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "test_user_123", // In a real app, this comes from auth
          step: currentStep.step,
          answer: currentAnswer,
        }),
      });
      const data = await res.json();
      setCurrentStep(data);
      
      // If complete, redirect after 3 seconds
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (currentStep?.is_complete) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full"
        >
          <Card className="p-8 text-center border-primary/20 shadow-2xl shadow-primary/10">
            <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Profile Complete!</h2>
            <p className="text-muted-foreground mb-6">
              We've mapped your financial persona.
            </p>
            
            <div className="p-4 bg-secondary/50 rounded-xl border border-border mb-6">
              <div className="text-sm text-muted-foreground mb-1">Your Persona</div>
              <div className="text-xl font-semibold text-primary">{currentStep.persona}</div>
            </div>

            <p className="text-sm text-muted-foreground animate-pulse">
              Redirecting to your dashboard...
            </p>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto p-6 md:p-12">
      <div className="flex-1 overflow-y-auto mb-8 pr-4 space-y-6 scrollbar-hide">
        {/* History */}
        {history.map((item, i) => (
          <div key={i} className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-secondary/50 rounded-2xl rounded-tl-sm p-4 text-sm whitespace-pre-wrap">
                {item.q}
              </div>
            </div>
            <div className="flex items-start justify-end gap-4">
              <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm p-4 text-sm">
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
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <div className="bg-secondary/50 rounded-2xl rounded-tl-sm p-4 text-sm font-medium leading-relaxed shadow-sm border border-border/50">
              {currentStep?.question?.split("\n").map((line, i) => (
                <p key={i} className={i > 0 ? "mt-4" : ""}>{line}</p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
        
        {submitting && (
          <div className="flex justify-end pt-4">
            <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>

      <div className="sticky bottom-0 bg-background/80 backdrop-blur-xl pb-6 pt-4 border-t border-border/50">
        <form onSubmit={handleSubmit} className="relative">
          <Input 
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer..."
            className="pr-14 h-14 bg-secondary/50 border-border/50 rounded-xl text-base shadow-inner focus-visible:ring-primary/50"
            disabled={submitting}
            autoFocus
          />
          <Button 
            type="submit" 
            size="icon"
            disabled={!answer.trim() || submitting}
            className="absolute right-2 top-2 h-10 w-10 rounded-lg hover:bg-primary"
          >
            <ArrowRight className="w-5 h-5" />
          </Button>
        </form>
        <div className="mt-3 text-center text-xs text-muted-foreground">
          Step {currentStep?.step} of 9
        </div>
      </div>
    </div>
  );
}
