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
      // Call the Next.js proxy endpoint
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

      // Convert response to blob
      const audioBlob = await response.blob();
      console.log(`[INFO] Received audio blob: ${audioBlob.size} bytes, type: ${audioBlob.type}`);

      // Create object URL and play
      const audioUrl = URL.createObjectURL(audioBlob);
      console.log(`[INFO] Created audio URL: ${audioUrl}`);
      
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        console.log("[INFO] Set audio src, attempting to play...");
        const playPromise = audioRef.current.play();
        
        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log("[OK] Audio is playing");
              setIsPlaying(true);
            })
            .catch((err) => {
              console.error("[ERROR] Playback failed:", err);
              setError(`Playback error: ${err.message}`);
            });
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      console.error("Voice briefing error:", message);
      setError(message);

      // Show error toast/notification
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
