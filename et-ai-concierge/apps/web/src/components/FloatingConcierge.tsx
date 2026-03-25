"use client";

import { useState, useRef, useEffect } from "react";
import { useSession } from "next-auth/react";
import { MessageSquare, X, Send, Sparkles, User, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from 'react-markdown';

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
            content: "Hi! I'm your ET AI Concierge. I can help answer market questions, analyze your portfolio, or provide personalized insights. How can I help you today?"
        }
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of chat
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
                    "Authorization": `Bearer ${(session as any).accessToken}`
                },
                body: JSON.stringify({ message: userMsg }),
            });

            if (!response.ok) {
                throw new Error("Failed to send message");
            }

            const data = await response.json();
            setMessages((prev) => [...prev, { role: "assistant", content: data.message || data.reply || data.response || "Something went wrong." }]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Sorry, I'm having trouble connecting to the servers right now. Please try again later." }
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

    if (!isOpen) {
        return (
            <Button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 z-50 p-0 bg-red-600 hover:bg-red-700 text-white"
                size="icon"
            >
                <MessageSquare className="h-6 w-6" />
                <span className="sr-only">Open AI Concierge</span>
            </Button>
        );
    }

    return (
        <Card className={`fixed z-50 flex flex-col shadow-2xl transition-all duration-300 ease-in-out border-red-100 bg-white ${
            isMinimized 
                ? "bottom-6 right-6 w-80 h-16" 
                : "bottom-6 right-6 w-[380px] h-[600px] max-h-[85vh] max-w-[calc(100vw-3rem)]"
        }`}>
            {/* Header */}
            <CardHeader className="flex flex-row items-center justify-between p-4 border-b bg-rose-50 rounded-t-xl shrink-0 cursor-pointer" onClick={() => isMinimized && setIsMinimized(false)}>
                <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-red-600" />
                    <h3 className="font-semibold text-zinc-900">ET AI Concierge</h3>
                </div>
                <div className="flex items-center gap-1">
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 hover:bg-rose-100 text-zinc-600" 
                        onClick={(e) => { e.stopPropagation(); setIsMinimized(!isMinimized); }}
                    >
                        {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
                    </Button>
                    <Button 
                        variant="ghost" 
                        size="icon" 
                        className="h-8 w-8 hover:bg-rose-100 text-zinc-600" 
                        onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
                    >
                        <X className="h-4 w-4" />
                    </Button>
                </div>
            </CardHeader>

            {/* Body */}
            {!isMinimized && (
                <>
                    <CardContent className="flex-1 p-0 overflow-hidden relative bg-white">
                        <ScrollArea className="h-full w-full p-4 [&>div>div]:flex [&>div>div]:flex-col [&>div>div]:gap-4" ref={scrollRef}>
                            {messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`flex max-w-[85%] ${
                                        msg.role === "user" ? "ml-auto" : "mr-auto"
                                    }`}
                                >
                                    <div
                                        className={`rounded-2xl px-4 py-3 ${
                                            msg.role === "user"
                                                ? "bg-red-600 text-white rounded-br-sm"
                                                : "bg-zinc-100 text-zinc-900 rounded-bl-sm border border-zinc-200"
                                        }`}
                                    >
                                        <div className="text-sm prose prose-sm max-w-none dark:prose-invert">
                                            {msg.role === "assistant" ? (
                                                <ReactMarkdown components={{
                                                    a: ({ node, ...props }) => (
                                                        <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline hover:text-blue-700 font-medium" />
                                                    ),
                                                }}>
                                                    {msg.content}
                                                </ReactMarkdown>
                                            ) : (
                                                msg.content
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex max-w-[85%] mr-auto">
                                    <div className="rounded-2xl px-4 py-3 bg-zinc-100 text-zinc-900 rounded-bl-sm border border-zinc-200 flex items-center gap-2">
                                        <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                        <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                        <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></div>
                                    </div>
                                </div>
                            )}
                        </ScrollArea>
                    </CardContent>

                    {/* Footer / Input */}
                    <CardFooter className="p-4 border-t shrink-0 bg-white rounded-b-xl">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                sendMessage();
                            }}
                            className="flex w-full items-center space-x-2"
                        >
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask about markets or your portfolio..."
                                className="flex-1 focus-visible:ring-red-600 bg-white text-zinc-900"
                                disabled={isLoading}
                            />
                            <Button 
                                type="submit" 
                                size="icon" 
                                disabled={isLoading || !input.trim()}
                                className="bg-red-600 hover:bg-red-700 text-white shrink-0"
                            >
                                <Send className="h-4 w-4" />
                                <span className="sr-only">Send</span>
                            </Button>
                        </form>
                    </CardFooter>
                </>
            )}
        </Card>
    );
}
