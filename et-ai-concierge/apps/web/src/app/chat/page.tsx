"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Mic, Send, Bot, User, ShieldAlert, BadgeInfo, Sparkles, CheckCircle2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";

// Points to the Next.js API routes which proxy to the FastAPI backend
const BACKEND_URL = "";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentUsed?: string;
  recommendations?: any[];
  disclaimers?: string[];
  isXray?: boolean;
};

type XRayState = "idle" | "active" | "complete";

// ─── Typing Indicator ────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex gap-4">
      <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
        <Bot className="w-5 h-5" />
      </div>
      <Card className="px-5 py-4 bg-card/80 border-border/50 shadow-sm">
        <div className="flex items-center gap-1.5">
          <motion.div
            className="w-2 h-2 rounded-full bg-primary/60"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-primary/60"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-primary/60"
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
          />
        </div>
      </Card>
    </div>
  );
}

// ─── Quick Reply Chips ───────────────────────────────────────────────────────
function QuickReplyChips({
  options,
  onSelect,
  disabled,
}: {
  options: string[];
  onSelect: (option: string) => void;
  disabled: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-wrap gap-2 mt-3 ml-12"
    >
      {options.map((option) => (
        <Button
          key={option}
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={() => onSelect(option)}
          className="rounded-full text-xs border-primary/30 hover:bg-primary/10 hover:border-primary/60 hover:text-primary transition-all duration-200"
        >
          {option}
        </Button>
      ))}
    </motion.div>
  );
}

// ─── Onboarding Complete Card ────────────────────────────────────────────────
function OnboardingCompleteCard({
  persona,
  tools,
}: {
  persona: string;
  tools: string[];
}) {
  const personaDisplay = persona
    ?.replace("PERSONA_", "")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="mt-4 ml-12"
    >
      <Card className="p-5 border-primary/20 shadow-lg shadow-primary/5 bg-gradient-to-br from-card via-card to-primary/5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Financial X-Ray Complete</h3>
            <p className="text-xs text-muted-foreground">Your persona: {personaDisplay}</p>
          </div>
        </div>
        {tools.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Recommended for you
            </p>
            <div className="flex flex-wrap gap-2">
              {tools.map((tool) => (
                <span
                  key={tool}
                  className="text-xs bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>
    </motion.div>
  );
}

// ─── X-Ray Question Detection ────────────────────────────────────────────────
const XRAY_QUICK_REPLIES: Record<number, string[]> = {
  0: ["Salaried", "Self-employed", "Business owner"],
  1: ["20s", "30s", "40s", "50+"],
  2: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
  3: ["Tech", "Pharma", "Banking", "Infrastructure", "Real Estate", "FMCG"],
  4: ["Saving", "Growing wealth", "Protecting assets", "Buying something big"],
};

// ─── Main Chat Page ──────────────────────────────────────────────────────────
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [xrayState, setXrayState] = useState<XRayState>("idle");
  const [xrayStep, setXrayStep] = useState(0);
  const [sessionId, setSessionId] = useState<string>("");
  const [userId] = useState(() => `test_user_${Math.random().toString(36).substr(2, 9)}`);
  const [xrayPersona, setXrayPersona] = useState<string>("");
  const [xrayTools, setXrayTools] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  // Start X-Ray on mount
  useEffect(() => {
    startXray();
  }, []);

  const startXray = async () => {
    setIsLoading(true);
    setXrayState("active");
    try {
      const res = await fetch(`${BACKEND_URL}/api/chat/xray`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: "" }),
      });
      const data = await res.json();
      setSessionId(data.session_id || "");

      if (data.is_complete) {
        setXrayState("complete");
        setMessages([
          {
            id: "1",
            role: "assistant",
            content: data.message,
            agentUsed: "profiling_agent",
            isXray: true,
          },
        ]);
      } else {
        setMessages([
          {
            id: "1",
            role: "assistant",
            content: data.message,
            agentUsed: "profiling_agent",
            isXray: true,
          },
        ]);
        setXrayStep(0);
      }
    } catch (error) {
      console.error("Failed to start X-Ray:", error);
      // Fallback greeting
      setMessages([
        {
          id: "1",
          role: "assistant",
          content:
            "Welcome to ET! 👋 I'm your personal Financial Navigator. I'd love to understand your financial world. Let's start — are you currently **salaried**, **self-employed**, or a **business owner**?",
          isXray: true,
        },
      ]);
      setXrayStep(0);
    } finally {
      setIsLoading(false);
    }
  };

  const sendXrayAnswer = useCallback(
    async (answer: string) => {
      if (isLoading) return;

      const msgId = Date.now().toString();
      setMessages((prev) => [
        ...prev,
        { id: msgId, role: "user", content: answer },
      ]);
      setIsLoading(true);

      try {
        const res = await fetch(`${BACKEND_URL}/api/chat/xray`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            message: answer,
            session_id: sessionId,
          }),
        });
        const data = await res.json();

        const asstId = (Date.now() + 1).toString();

        // Strip the JSON block from the displayed message
        let displayContent = data.message || "";
        displayContent = displayContent
          .replace(/```json\s*\{[\s\S]*?\}\s*```/g, "")
          .replace(/\{"xray_complete"[\s\S]*?\}/g, "")
          .trim();

        setMessages((prev) => [
          ...prev,
          {
            id: asstId,
            role: "assistant",
            content: displayContent,
            agentUsed: "profiling_agent",
            isXray: true,
          },
        ]);

        if (data.is_complete) {
          setXrayState("complete");
          setXrayPersona(data.persona || "");
          setXrayTools(data.recommended_tools || []);
        } else {
          setXrayStep((prev) => prev + 1);
        }
      } catch (error) {
        console.error("X-Ray error:", error);
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: "assistant",
            content: "Sorry, I encountered an error. Please try again.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, sessionId]
  );

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput("");

    // If X-Ray is active, route to X-Ray
    if (xrayState === "active") {
      sendXrayAnswer(userMsg);
      return;
    }

    // Normal chat flow
    const msgId = Date.now().toString();
    setMessages((prev) => [
      ...prev,
      { id: msgId, role: "user", content: userMsg },
    ]);
    setIsLoading(true);

    const asstMsgId = (Date.now() + 1).toString();
    setMessages((prev) => [
      ...prev,
      { id: asstMsgId, role: "assistant", content: "" },
    ]);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          message: userMsg,
          modality: "web",
        }),
      });

      if (!response.body) throw new Error("No body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === asstMsgId
                      ? { ...m, content: m.content + data.token }
                      : m
                  )
                );
              }
              if (data.done) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === asstMsgId
                      ? { ...m, agentUsed: data.agent_used }
                      : m
                  )
                );
              }
            } catch (err) {}
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        {
          id: "err",
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentBadge = (agentId?: string) => {
    if (!agentId) return null;
    const names: Record<string, string> = {
      profiling_agent: "Financial X-Ray",
      editorial_agent: "ET Prime",
      market_intelligence_agent: "Markets",
      marketplace_agent: "Marketplace",
      behavioral_monitor: "Cross-Sell",
    };
    return names[agentId] || agentId;
  };

  // Determine quick replies for current X-Ray step
  const currentQuickReplies =
    xrayState === "active" && !isLoading ? XRAY_QUICK_REPLIES[xrayStep] : undefined;

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r border-border/40 hidden md:flex flex-col p-4 bg-card/10 backdrop-blur-md">
        <h2 className="font-bold text-lg mb-6 flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-primary text-white flex items-center justify-center text-xs">
            ET
          </span>
          Navigator
        </h2>

        <div className="space-y-2 flex-1 overflow-auto">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Status
          </div>
          {xrayState === "active" && (
            <div className="flex items-center gap-2 text-xs text-primary p-2 bg-primary/5 rounded-lg border border-primary/20">
              <Sparkles className="w-3.5 h-3.5" />
              Financial X-Ray in progress
            </div>
          )}
          {xrayState === "complete" && (
            <div className="flex items-center gap-2 text-xs text-green-500 p-2 bg-green-500/5 rounded-lg border border-green-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Profile complete
            </div>
          )}

          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-4 mb-2">
            Recent Chats
          </div>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm font-normal"
          >
            Home Loan Comparison
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm font-normal"
          >
            Gold Investment Ideas
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start text-sm font-normal"
          >
            Portfolio Rebalance
          </Button>
        </div>

        <div className="mt-auto pt-4 border-t border-border/40">
          <div className="text-xs bg-secondary p-3 rounded-lg flex items-start gap-2 text-muted-foreground">
            <ShieldAlert className="w-4 h-4 shrink-0 text-primary" />
            Advice is generated by AI. Please consult a registered advisor.
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <header className="h-14 border-b border-border/40 flex items-center px-4 backdrop-blur-md sticky top-0 bg-background/50 z-10">
          <div className="md:hidden font-bold mr-auto">ET Concierge</div>
          <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
            {xrayState === "active" && (
              <span className="flex items-center gap-1.5 text-primary font-medium">
                <Sparkles className="w-3.5 h-3.5" />
                Financial X-Ray — Q{Math.min(xrayStep + 1, 5)} of 5
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <BadgeInfo className="w-4 h-4" />
              Multi-Agent Active
            </span>
          </div>
        </header>

        {/* Messages */}
        <ScrollArea className="flex-1 py-6 px-4 md:px-8">
          <div className="max-w-3xl mx-auto space-y-6 pb-10">
            <AnimatePresence>
              {messages.map((m) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex gap-4 ${m.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      m.role === "user"
                        ? "bg-secondary"
                        : "bg-primary/20 text-primary"
                    }`}
                  >
                    {m.role === "user" ? (
                      <User className="w-5 h-5" />
                    ) : (
                      <Bot className="w-5 h-5" />
                    )}
                  </div>

                  <div
                    className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"} max-w-[85%]`}
                  >
                    <Card
                      className={`px-5 py-4 ${
                        m.role === "user"
                          ? "bg-primary text-primary-foreground border-transparent"
                          : "bg-card/80 border-border/50 shadow-sm"
                      }`}
                    >
                      {m.role === "assistant" ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {m.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="text-sm whitespace-pre-wrap">
                          {m.content}
                        </div>
                      )}
                    </Card>

                    {/* Agent Badge */}
                    {m.agentUsed && (
                      <div className="mt-1 text-[10px] uppercase tracking-wider text-muted-foreground bg-secondary px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                        {m.isXray && <Sparkles className="w-2.5 h-2.5" />}
                        {getAgentBadge(m.agentUsed)}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isLoading && <TypingIndicator />}

            {/* Quick Reply Chips */}
            {currentQuickReplies && (
              <QuickReplyChips
                options={currentQuickReplies}
                onSelect={(option) => sendXrayAnswer(option)}
                disabled={isLoading}
              />
            )}

            {/* Onboarding Complete Card */}
            {xrayState === "complete" && xrayPersona && (
              <OnboardingCompleteCard persona={xrayPersona} tools={xrayTools} />
            )}

            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 bg-background/80 backdrop-blur-xl border-t border-border/50">
          <form
            onSubmit={handleChatSubmit}
            className="max-w-3xl mx-auto relative flex gap-2"
          >
            <Button
              type="button"
              variant="outline"
              size="icon"
              className={`h-12 w-12 rounded-xl shrink-0 ${isRecording ? "text-red-500 border-red-500 animate-pulse" : ""}`}
            >
              <Mic className="w-5 h-5" />
            </Button>
            <div className="relative flex-1">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  xrayState === "active"
                    ? "Type your answer or tap a quick reply..."
                    : "Ask about markets, loans, or specific stocks..."
                }
                className="h-12 rounded-xl pr-12 bg-secondary/30 ring-offset-background border-border/50 text-base"
                disabled={isLoading}
              />
              <Button
                type="submit"
                size="icon"
                className="absolute right-1 top-1 h-10 w-10 rounded-lg hover:bg-primary shadow-sm"
                disabled={isLoading || !input.trim()}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </form>
          <div className="text-center mt-2 text-[10px] text-muted-foreground w-full">
            The ET AI Concierge can make mistakes. Please verify important
            financial information.
          </div>
        </div>
      </div>
    </div>
  );
}
