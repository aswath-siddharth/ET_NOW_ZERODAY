import { NextRequest, NextResponse } from "next/server";
import { auth, mintBackendToken } from "@/auth";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(req: NextRequest) {
  try {
    // Get auth session and mint a backend token
    const session = await auth();
    
    if (!session) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }
    
    const headers: Record<string, string> = {
      "Accept": "audio/mpeg",
    };

    const token = await mintBackendToken(session);
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // Call backend voice-briefing endpoint with streaming
    const response = await fetch(`${BACKEND_URL}/api/voice-briefing`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      console.error(`Backend returned ${response.status}`);
      
      // Return error as JSON
      if (response.status === 503) {
        return NextResponse.json(
          { 
            error: "Service unavailable",
            message: "Voice briefing service is temporarily down. Please try again later."
          },
          { status: 503 }
        );
      }
      
      return NextResponse.json(
        { error: "Failed to generate voice briefing" },
        { status: response.status }
      );
    }

    // Forward the streaming response directly (don't buffer with arrayBuffer)
    // This allows chunks to arrive progressively at the frontend
    if (response.body) {
      return new NextResponse(response.body, {
        status: 200,
        headers: {
          "Content-Type": "audio/mpeg",
          "Cache-Control": "no-cache, no-store, must-revalidate",
          "Transfer-Encoding": "chunked", // Enable chunked transfer for streaming
        },
      });
    } else {
      return NextResponse.json(
        { error: "No response body from backend" },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error("Voice briefing proxy error:", error);
    return NextResponse.json(
      { error: "Failed to connect to voice briefing service" },
      { status: 502 }
    );
  }
}
