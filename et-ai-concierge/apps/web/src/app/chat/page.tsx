"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Mic, Send, Bot, User, ShieldAlert, BadgeInfo, Sparkles, CheckCircle2, Home } from "lucide-react";
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
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [otherText, setOtherText] = useState("");

  const handleOtherSubmit = () => {
    if (otherText.trim()) {
      onSelect(otherText.trim());
      setShowOtherInput(false);
      setOtherText("");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-2 mt-3 ml-12"
    >
      <div className="flex flex-wrap gap-2">
        {options.map((option) =>
          option === "Others" ? (
            <Button
              key={option}
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => setShowOtherInput(!showOtherInput)}
              className={`rounded-full text-xs border-dashed transition-all duration-200 ${
                showOtherInput
                  ? "border-primary text-primary bg-primary/10"
                  : "border-primary/30 hover:bg-primary/10 hover:border-primary/60 hover:text-primary"
              }`}
            >
              {option} …
            </Button>
          ) : (
            <Button
              key={option}
              variant="outline"
              size="sm"
              disabled={disabled}
              onClick={() => {
                setShowOtherInput(false);
                onSelect(option);
              }}
              className="rounded-full text-xs border-primary/30 hover:bg-primary/10 hover:border-primary/60 hover:text-primary transition-all duration-200"
            >
              {option}
            </Button>
          )
        )}
      </div>
      {showOtherInput && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="flex gap-2 items-center"
        >
          <Input
            value={otherText}
            onChange={(e) => setOtherText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleOtherSubmit()}
            placeholder="Type your answer..."
            className="h-9 rounded-lg text-sm bg-secondary/30 border-border/50 flex-1"
            autoFocus
          />
          <Button
            size="sm"
            onClick={handleOtherSubmit}
            disabled={!otherText.trim()}
            className="h-9 rounded-lg px-4 text-xs"
          >
            Send
          </Button>
        </motion.div>
      )}
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

// ─── Main Chat Page ──────────────────────────────────────────────────────────
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const { data: session } = useSession();
  const [userId] = useState(() => session?.user?.id || `anon_${Math.random().toString(36).substr(2, 9)}`);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);





  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput("");
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
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          message: userMsg,
          modality: "web",
        }),
      });

      if (!response.ok) throw new Error("API Error");
      
      const data = await response.json();
      
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstMsgId
            ? { ...m, content: data.message, agentUsed: data.agent_used }
            : m
        )
      );
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

  // Determine quick replies (if any)
  const currentQuickReplies = undefined;

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
          <div className="ml-auto flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" size="icon" className="h-9 w-9">
                <Home className="w-4 h-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <BadgeInfo className="w-4 h-4" />
                Multi-Agent Active
              </span>
            </div>
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
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ node, ...props }) => (
                              <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline hover:text-blue-700 font-medium" />
                            ),
                          }}
                        >
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
                onSelect={(option) => handleChatSubmit({ preventDefault: () => {}, currentTarget: { elements: { message: { value: option } } } } as any)}
                disabled={isLoading}
              />
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
                placeholder="Ask about markets, loans, or specific stocks..."
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
