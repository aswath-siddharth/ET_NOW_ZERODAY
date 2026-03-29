"use client";

import { useState, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  Mic, Send, Bot, User, ShieldAlert, Sparkles, Home,
  Plus, MessageSquare,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion, AnimatePresence } from "framer-motion";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentUsed?: string;
  recommendations?: any[];
  disclaimers?: string[];
};

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
        <Bot className="w-4 h-4" />
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-bl-md glass-card border border-border/50">
        <div className="flex items-center gap-1.5">
          <motion.div
            className="w-1.5 h-1.5 rounded-full bg-primary/60"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className="w-1.5 h-1.5 rounded-full bg-primary/60"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
          />
          <motion.div
            className="w-1.5 h-1.5 rounded-full bg-primary/60"
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
          />
        </div>
      </div>
    </div>
  );
}

const AGENT_BADGES: Record<string, { label: string; color: string }> = {
  profiling_agent: { label: "Financial X-Ray", color: "text-primary" },
  editorial_agent: { label: "ET Prime", color: "text-purple-400" },
  market_intelligence_agent: { label: "Markets", color: "text-emerald-400" },
  marketplace_agent: { label: "Marketplace", color: "text-blue-400" },
  behavioral_monitor: { label: "Cross-Sell", color: "text-amber-400" },
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const { data: session } = useSession();
  const [userId] = useState(
    () => session?.user?.id || `anon_${Math.random().toString(36).substr(2, 9)}`
  );
  const scrollRef = useRef<HTMLDivElement>(null);

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
    setMessages((prev) => [...prev, { id: msgId, role: "user", content: userMsg }]);
    setIsLoading(true);

    const asstMsgId = (Date.now() + 1).toString();
    setMessages((prev) => [...prev, { id: asstMsgId, role: "assistant", content: "" }]);

    try {
      const response = await fetch("/api/chat", {
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
        ...prev.filter((m) => m.id !== asstMsgId),
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

  const startNewChat = () => {
    setMessages([]);
    setSessionId("");
  };

  return (
    <div className="flex h-screen pt-16 bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r border-border/40 hidden md:flex flex-col p-4 bg-card/30 backdrop-blur-sm">
        <button
          onClick={startNewChat}
          className="flex items-center gap-2 w-full px-4 py-2.5 rounded-xl border border-border/50 hover:bg-accent text-sm font-medium text-foreground transition mb-4"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>

        <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-2">
          Recent
        </div>
        <div className="space-y-1 flex-1 overflow-auto">
          {["Home Loan Comparison", "Gold Investment Ideas", "Portfolio Rebalance"].map(
            (title) => (
              <button
                key={title}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition text-left"
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{title}</span>
              </button>
            )
          )}
        </div>

        <div className="mt-auto pt-4 border-t border-border/40">
          <div className="text-xs bg-secondary/50 p-3 rounded-lg flex items-start gap-2 text-muted-foreground">
            <ShieldAlert className="w-4 h-4 shrink-0 text-primary mt-0.5" />
            <span>AI-generated advice. Please consult a registered advisor.</span>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-6 px-4 md:px-8">
          <div className="max-w-3xl mx-auto space-y-6 pb-10">
            {/* Welcome message when empty */}
            {messages.length === 0 && (
              <div className="text-center py-20">
                <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-7 h-7 text-primary" />
                </div>
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  ET AI Concierge
                </h2>
                <p className="text-sm text-muted-foreground max-w-md mx-auto mb-8">
                  Ask about markets, loans, investment strategies, or get personalized
                  financial insights based on your profile.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {[
                    "What's happening in the market today?",
                    "Compare home loan rates",
                    "Suggest tax-saving investments",
                    "Analyze my portfolio",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => {
                        setInput(suggestion);
                      }}
                      className="px-4 py-2 rounded-xl border border-border/50 text-xs text-muted-foreground hover:text-foreground hover:bg-accent hover:border-primary/20 transition"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map((m) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                  className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      m.role === "user"
                        ? "bg-primary/10 text-primary"
                        : "bg-primary/10 text-primary"
                    }`}
                  >
                    {m.role === "user" ? (
                      <User className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </div>

                  <div
                    className={`flex flex-col ${
                      m.role === "user" ? "items-end" : "items-start"
                    } max-w-[85%]`}
                  >
                    <div
                      className={`px-4 py-3 rounded-2xl ${
                        m.role === "user"
                          ? "rounded-tr-md bg-primary text-primary-foreground"
                          : "rounded-tl-md glass-card border border-border/50"
                      }`}
                    >
                      {m.role === "assistant" ? (
                        <div className="prose prose-sm dark:prose-invert max-w-none text-foreground text-sm">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({ node, ...props }) => (
                                <a
                                  {...props}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary underline hover:opacity-80 font-medium"
                                />
                              ),
                            }}
                          >
                            {m.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="text-sm whitespace-pre-wrap">{m.content}</div>
                      )}
                    </div>

                    {/* Agent Badge */}
                    {m.agentUsed && AGENT_BADGES[m.agentUsed] && (
                      <div
                        className={`mt-1.5 text-[10px] uppercase tracking-wider bg-secondary/50 px-2.5 py-0.5 rounded-md inline-flex items-center gap-1 font-medium ${
                          AGENT_BADGES[m.agentUsed].color
                        }`}
                      >
                        {AGENT_BADGES[m.agentUsed].label}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {isLoading && <TypingIndicator />}
            <div ref={scrollRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-border/50 bg-background/80 backdrop-blur-xl">
          <form
            onSubmit={handleChatSubmit}
            className="max-w-3xl mx-auto relative flex gap-2"
          >
            <button
              type="button"
              className={`h-12 w-12 rounded-xl border border-border/50 flex items-center justify-center shrink-0 text-muted-foreground hover:text-foreground hover:bg-accent transition ${
                isRecording ? "text-red-400 border-red-400/50 animate-pulse" : ""
              }`}
            >
              <Mic className="w-5 h-5" />
            </button>
            <div className="relative flex-1">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about markets, loans, or specific stocks..."
                className="w-full h-12 rounded-xl pr-12 pl-4 bg-card border border-border/50 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-1.5 top-1.5 h-9 w-9 rounded-lg bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 transition disabled:opacity-30"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
          <div className="text-center mt-2 text-[10px] text-muted-foreground">
            The ET AI Concierge can make mistakes. Please verify important financial information.
          </div>
        </div>
      </div>
    </div>
  );
}
