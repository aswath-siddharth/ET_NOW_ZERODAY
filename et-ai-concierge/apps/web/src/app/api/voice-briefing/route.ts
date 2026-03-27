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

    // Call backend voice-briefing endpoint
    const response = await fetch(`${BACKEND_URL}/api/voice-briefing`, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      console.error(`Backend returned ${response.status}`);
      
      // Return error as JSON, not audio
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

    // Get audio as buffer
    const audioBuffer = await response.arrayBuffer();
    
    // Stream back as MP3
    return new NextResponse(audioBuffer, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": audioBuffer.byteLength.toString(),
        "Cache-Control": "no-cache, no-store, must-revalidate",
      },
    });
  } catch (error) {
    console.error("Voice briefing proxy error:", error);
    return NextResponse.json(
      { error: "Failed to connect to voice briefing service" },
      { status: 502 }
    );
  }
}
