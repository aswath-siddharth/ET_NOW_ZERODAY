"use client";

import { useState, useRef } from "react";
import { Volume2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface VoiceBriefingButtonProps {
  className?: string;
}

export function VoiceBriefingButton({ className }: VoiceBriefingButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleGenerateBriefing = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Call the Next.js proxy endpoint with streaming
      const response = await fetch("/api/voice-briefing", {
        method: "GET",
        headers: {
          "Accept": "audio/mpeg",
        },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(
          data.message || data.error || "Failed to generate voice briefing"
        );
      }

      if (!response.body) {
        throw new Error("No response body for audio stream");
      }

      // Stream audio chunks and play as soon as enough data arrives
      const reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let totalBytes = 0;
      let hasStartedPlayback = false;
      const PLAYBACK_THRESHOLD = 50 * 1024; // Start playback after 50KB

      console.log("[INFO] Starting audio stream...");

      // Read and buffer chunks
      const readLoop = async () => {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log(`[INFO] Stream complete: ${totalBytes} bytes received`);
            break;
          }

          chunks.push(value);
          totalBytes += value.length;
          console.log(`[INFO] Received chunk: +${value.length} bytes (total: ${totalBytes})`);

          // Start playback once we have enough buffered (50KB)
          if (!hasStartedPlayback && totalBytes >= PLAYBACK_THRESHOLD) {
            hasStartedPlayback = true;
            console.log(`[INFO] Sufficient buffer (${totalBytes}B), starting playback...`);

            // Create blob and start playback - do this ONCE only
            const audioBlob = new Blob(chunks, { type: "audio/mpeg" });
            const audioUrl = URL.createObjectURL(audioBlob);

            if (audioRef.current) {
              audioRef.current.src = audioUrl;
              audioRef.current.load(); // Force reload to enable streaming
              
              const playPromise = audioRef.current.play();

              if (playPromise !== undefined) {
                playPromise
                  .then(() => {
                    console.log("[OK] Audio playback started (streaming)");
                    setIsPlaying(true);
                  })
                  .catch((err) => {
                    console.error("[ERROR] Playback failed:", err.message);
                    setError(`Playback error: ${err.message}`);
                  });
              }
            }
          }
        }
      };

      // Run read loop without awaiting immediately (let it continue in background)
      readLoop().catch((err) => {
        console.error("[ERROR] Stream reading error:", err);
        if (!hasStartedPlayback) {
          setError("Failed to receive audio stream");
        }
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      console.error("[ERROR] Voice briefing error:", message);
      setError(message);

      if (typeof window !== "undefined" && "alert" in window) {
        alert(`Voice briefing failed: ${message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  const handleAudioError = (err: any) => {
    console.error("[ERROR] Audio playback failed:", err);
    setIsPlaying(false);
    setError("Failed to play audio - check browser console for details");
  };

  const handleAudioPlay = () => {
    console.log("[INFO] Audio playback started");
    setIsPlaying(true);
  };

  return (
    <>
      {/* Hidden audio element for playback */}
      <audio
        ref={audioRef}
        controls={false}
        autoPlay={false}
        onEnded={handleAudioEnded}
        onPlay={handleAudioPlay}
        onError={handleAudioError}
      />

      {/* Button */}
      <Button
        onClick={handleGenerateBriefing}
        disabled={isLoading || isPlaying}
        variant="default"
        size="lg"
        className={className}
        title={
          isPlaying
            ? "Playing voice briefing..."
            : "Generate personalized voice briefing"
        }
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Generating...
          </>
        ) : isPlaying ? (
          <>
            <Volume2 className="w-5 h-5 mr-2 animate-pulse" />
            Playing...
          </>
        ) : (
          <>
            <Volume2 className="w-5 h-5 mr-2" />
            Voice Briefing
          </>
        )}
      </Button>

      {/* Error message */}
      {error && (
        <p className="text-sm text-red-600 mt-2">
          Error: {error}
        </p>
      )}
    </>
  );
}
