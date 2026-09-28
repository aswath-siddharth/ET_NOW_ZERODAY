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

      // Stream audio chunks and play as soon as data arrives
      const reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let totalBytes = 0;
      let hasStartedPlayback = false;

      // Check for MediaSource support for progressive chunk playback
      const canUseMSE =
        typeof window !== "undefined" &&
        !!window.MediaSource &&
        MediaSource.isTypeSupported("audio/mpeg");

      let mediaSource: MediaSource | null = null;
      let sourceBuffer: SourceBuffer | null = null;

      if (canUseMSE && audioRef.current) {
        try {
          mediaSource = new MediaSource();
          const audioUrl = URL.createObjectURL(mediaSource);
          audioRef.current.src = audioUrl;

          await new Promise<void>((resolve) => {
            if (!mediaSource) return resolve();
            mediaSource.addEventListener(
              "sourceopen",
              () => {
                try {
                  if (mediaSource && mediaSource.readyState === "open") {
                    sourceBuffer = mediaSource.addSourceBuffer("audio/mpeg");
                  }
                } catch (e) {
                  console.warn("[WARN] MSE addSourceBuffer failed:", e);
                }
                resolve();
              },
              { once: true }
            );
          });
        } catch (mseErr) {
          console.warn("[WARN] MSE init failed, falling back to full stream:", mseErr);
          mediaSource = null;
          sourceBuffer = null;
        }
      }

      console.log("[INFO] Starting audio chunk stream...");

      // Read chunks progressively
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log(`[INFO] Audio stream complete: ${totalBytes} bytes received`);
          if (mediaSource && mediaSource.readyState === "open") {
            if (sourceBuffer && sourceBuffer.updating) {
              await new Promise((r) =>
                sourceBuffer!.addEventListener("updateend", r, { once: true })
              );
            }
            try {
              mediaSource.endOfStream();
            } catch (e) {
              // ignore
            }
          }
          break;
        }

        if (value && value.length > 0) {
          chunks.push(value);
          totalBytes += value.length;

          // Progressive append if MediaSource active
          if (sourceBuffer && mediaSource && mediaSource.readyState === "open") {
            try {
              if (sourceBuffer.updating) {
                await new Promise((r) =>
                  sourceBuffer!.addEventListener("updateend", r, { once: true })
                );
              }
              sourceBuffer.appendBuffer(value);

              if (!hasStartedPlayback && totalBytes >= 8192 && audioRef.current) {
                hasStartedPlayback = true;
                setIsLoading(false);
                audioRef.current.play().catch(console.error);
              }
            } catch (err) {
              console.warn("[WARN] MSE append failed, falling back to blob:", err);
              sourceBuffer = null;
              mediaSource = null;
            }
          }
        }
      }

      // Fallback: If MSE wasn't used or playback hasn't started yet, play complete blob
      if (!hasStartedPlayback && chunks.length > 0 && audioRef.current) {
        const audioBlob = new Blob(chunks, { type: "audio/mpeg" });
        const audioUrl = URL.createObjectURL(audioBlob);
        audioRef.current.src = audioUrl;
        audioRef.current.load();
        hasStartedPlayback = true;
        setIsLoading(false);
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          playPromise
            .then(() => setIsPlaying(true))
            .catch((err) => {
              console.error("[ERROR] Playback failed:", err.message);
              setError(`Playback error: ${err.message}`);
            });
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      console.error("[ERROR] Voice briefing error:", message);
      setError(message);
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
