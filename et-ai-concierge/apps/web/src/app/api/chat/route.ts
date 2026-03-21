import { NextRequest, NextResponse } from "next/server";
import { auth, mintBackendToken } from "@/auth";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Get auth session and mint a backend token
    const session = await auth();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (session) {
      const token = await mintBackendToken(session);
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.body) {
      return NextResponse.json(
        { error: "No response from backend" },
        { status: 502 }
      );
    }

    // Stream SSE through
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Chat proxy error:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 502 }
    );
  }
}
