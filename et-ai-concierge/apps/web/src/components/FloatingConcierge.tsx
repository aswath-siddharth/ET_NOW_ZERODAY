"use client";

import { useState, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import { MessageSquare, X, Send, Sparkles, Minimize2, Maximize2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
};

export function FloatingConcierge() {
  const { data: session } = useSession();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your ET AI Concierge. I can help answer market questions, analyze your portfolio, or provide personalized insights. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen, isMinimized]);

  if (!session) return null;

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${(session as any).accessToken}`,
        },
        body: JSON.stringify({ message: userMsg }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message || data.reply || data.response || "Something went wrong.",
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I'm having trouble connecting right now. Please try again later.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ─── FAB Button ─────────────────────────────────
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center shadow-lg hover:opacity-90 transition-all duration-300 z-50 animate-pulse-glow"
      >
        <MessageSquare className="h-6 w-6" />
        <span className="sr-only">Open AI Concierge</span>
      </button>
    );
  }

  // ─── Chat Panel ─────────────────────────────────
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        className={`fixed z-50 flex flex-col shadow-2xl transition-all duration-300 rounded-2xl border border-border/50 overflow-hidden ${
          isMinimized
            ? "bottom-6 right-6 w-80 h-14"
            : "bottom-6 right-6 w-[380px] h-[600px] max-h-[85vh] max-w-[calc(100vw-3rem)]"
        }`}
        style={{ background: "var(--card)" }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3 border-b border-border/50 shrink-0 cursor-pointer bg-card"
          onClick={() => isMinimized && setIsMinimized(false)}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm text-foreground">ET AI Concierge</h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              className="h-7 w-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition"
              onClick={(e) => {
                e.stopPropagation();
                setIsMinimized(!isMinimized);
              }}
            >
              {isMinimized ? <Maximize2 className="h-3.5 w-3.5" /> : <Minimize2 className="h-3.5 w-3.5" />}
            </button>
            <button
              className="h-7 w-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent transition"
              onClick={(e) => {
                e.stopPropagation();
                setIsOpen(false);
              }}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Body */}
        {!isMinimized && (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-3" ref={scrollRef}>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex max-w-[85%] ${
                    msg.role === "user" ? "ml-auto" : "mr-auto"
                  }`}
                >
                  <div
                    className={`rounded-2xl px-3.5 py-2.5 text-sm ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-secondary text-foreground rounded-bl-md border border-border/50"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm dark:prose-invert max-w-none text-sm">
                        <ReactMarkdown
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
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex max-w-[85%] mr-auto">
                  <div className="rounded-2xl px-3.5 py-2.5 bg-secondary rounded-bl-md border border-border/50 flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" />
                  </div>
                </div>
              )}
            </div>

            {/* Footer / Input */}
            <div className="p-3 border-t border-border/50 shrink-0 bg-card">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about markets or your portfolio..."
                  className="flex-1 h-9 px-3 rounded-lg bg-secondary border border-border/50 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 transition"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="h-9 w-9 rounded-lg bg-primary text-primary-foreground flex items-center justify-center hover:opacity-90 transition disabled:opacity-30 shrink-0"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </form>
            </div>
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
